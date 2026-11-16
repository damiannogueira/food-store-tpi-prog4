# ruff: noqa: E402

import os
import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "clave-temporal-para-verificar-la-base-del-tpi"

from app.core.deps import get_usuario_uow
from app.core.security import create_access_token, hash_password
from app.main import app
from app.modules.auth.router import get_auth_service
from app.modules.auth.service import AuthService
from app.modules.categorias.models import Categoria
from app.modules.pedidos.models import DetallePedido, Pedido
from app.modules.pedidos.repository import PedidoRepository
from app.modules.pedidos.router import get_pedido_service, router
from app.modules.pedidos.schemas import PedidoCreate
from app.modules.pedidos.service import (
    PedidoAjeno,
    PedidoNoEncontrado,
    PedidoService,
    ProductoNoDisponible,
    ProductoNoEncontrado,
    ProductoRepetido,
    StockInsuficiente,
    TransicionInvalida,
)
from app.modules.pedidos.unit_of_work import PedidoUnitOfWork
from app.modules.productos.models import Producto
from app.modules.productos.repository import ProductoRepository
from app.modules.usuarios.models import Usuario
from app.modules.usuarios.schemas import UserPublic
from app.modules.usuarios.unit_of_work import UsuarioUnitOfWork
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.dialects import postgresql
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, func, select


class PedidosTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.password_hash = hash_password("Clave1234!")

    def setUp(self):
        # Creo una base nueva en memoria para cada prueba.
        self.engine = create_engine(
            "sqlite://",
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )

        @event.listens_for(self.engine, "connect")
        def activar_claves_foraneas(connection, _record):
            connection.execute("PRAGMA foreign_keys=ON")

        SQLModel.metadata.create_all(self.engine)
        self.addCleanup(self.engine.dispose)
        self.factory = lambda: Session(self.engine, expire_on_commit=False)
        self.service = PedidoService(PedidoUnitOfWork(self.factory))
        with self.factory() as session:
            usuarios = [
                Usuario(
                    id=id,
                    username=nombre,
                    full_name=nombre,
                    email=f"{nombre}@example.com",
                    hashed_password=self.password_hash,
                    role=rol,
                    disabled=disabled,
                )
                for id, nombre, rol, disabled in (
                    (1, "cliente", "user", False),
                    (2, "otro", "user", False),
                    (3, "admin", "admin", False),
                    (4, "inactivo", "user", True),
                )
            ]
            session.add_all(usuarios)
            session.add(Categoria(id=1, nombre="Comidas"))
            session.flush()
            session.add_all(
                [
                    Producto(
                        id=1, categoria_id=1, nombre="Pizza", precio_base=10.5, stock=10
                    ),
                    Producto(
                        id=2,
                        categoria_id=1,
                        nombre="Empanadas",
                        precio_base=20.25,
                        stock=8,
                    ),
                    Producto(
                        id=3, categoria_id=1, nombre="Agua", precio_base=0, stock=5
                    ),
                ]
            )
            session.commit()
            self.cliente, self.otro, self.admin, self.inactivo = [
                UserPublic.model_validate(u) for u in usuarios
            ]
        app.dependency_overrides[get_pedido_service] = lambda: self.service
        app.dependency_overrides[get_usuario_uow] = lambda: UsuarioUnitOfWork(
            self.factory
        )
        app.dependency_overrides[get_auth_service] = lambda: AuthService(
            UsuarioUnitOfWork(self.factory)
        )
        self.addCleanup(app.dependency_overrides.clear)
        self.http = TestClient(app)
        self.addCleanup(self.http.close)

    def datos(self, items=None):
        return PedidoCreate(
            items=items
            if items is not None
            else [
                {"producto_id": 1, "cantidad": 2},
                {"producto_id": 2, "cantidad": 3},
            ],
            forma_pago="EFECTIVO",
            direccion_entrega="Calle 123",
            notas="Sin timbre",
        )

    def autenticar(self, usuario=None):
        self.http.cookies.clear()
        if usuario is not None:
            self.http.cookies.set(
                "access_token",
                create_access_token({"sub": usuario.username}),
            )

    def stocks(self):
        with self.factory() as session:
            return {p.id: p.stock for p in session.exec(select(Producto)).all()}

    def comprobar_sin_pedido(self):
        self.assertEqual(self.stocks(), {1: 10, 2: 8, 3: 5})
        with self.factory() as session:
            for model in (Pedido, DetallePedido):
                self.assertEqual(
                    session.exec(select(func.count()).select_from(model)).one(), 0
                )

    def test_creacion_varios_productos_stock_y_total_persistidos(self):
        pedido = self.service.crear(self.datos(), self.cliente)
        self.assertEqual(pedido.estado, "PENDIENTE")
        self.assertEqual(pedido.usuario_id, self.cliente.id)
        self.assertEqual(self.stocks(), {1: 8, 2: 5, 3: 5})
        self.assertEqual([d.subtotal for d in pedido.items], [21, 60.75])
        self.assertAlmostEqual(pedido.total, 81.75)
        with self.factory() as session:
            guardado = session.get(Pedido, pedido.id)
            self.assertEqual(guardado.total, pedido.total)
            self.assertEqual(len(guardado.items), 2)

    def test_compra_precio_cero_y_stock_exacto(self):
        pedido = self.service.crear(
            self.datos([{"producto_id": 3, "cantidad": 5}]), self.admin
        )
        self.assertEqual(pedido.usuario_id, self.admin.id)
        self.assertEqual(pedido.total, 0)
        self.assertEqual(self.stocks()[3], 0)

    def test_stock_insuficiente_revierte_linea_y_descuento_previos(self):
        datos = self.datos(
            [
                {"producto_id": 1, "cantidad": 2},
                {"producto_id": 2, "cantidad": 9},
            ]
        )
        with self.assertRaises(StockInsuficiente):
            self.service.crear(datos, self.cliente)
        self.comprobar_sin_pedido()

    def test_productos_repetidos(self):
        datos = self.datos(
            [
                {"producto_id": 1, "cantidad": 1},
                {"producto_id": 1, "cantidad": 2},
            ]
        )
        with self.assertRaises(ProductoRepetido):
            self.service.crear(datos, self.cliente)
        self.comprobar_sin_pedido()

    def test_producto_inexistente_revierte_todo(self):
        datos = self.datos(
            [
                {"producto_id": 1, "cantidad": 2},
                {"producto_id": 999, "cantidad": 1},
            ]
        )
        with self.assertRaises(ProductoNoEncontrado):
            self.service.crear(datos, self.cliente)
        self.comprobar_sin_pedido()

    def test_producto_inactivo_y_no_disponible_revierten_todo(self):
        for campo, error in (
            ("activo", ProductoNoEncontrado),
            ("disponible", ProductoNoDisponible),
        ):
            with self.subTest(campo=campo):
                with self.factory() as session:
                    producto = session.get(Producto, 2)
                    producto.activo = campo != "activo"
                    producto.disponible = campo != "disponible"
                    session.commit()
                with self.assertRaises(error):
                    self.service.crear(self.datos(), self.cliente)
                self.comprobar_sin_pedido()

    def test_categoria_inactiva_no_impide_comprar_producto_activo(self):
        with self.factory() as session:
            session.get(Categoria, 1).activo = False
            session.commit()
        pedido = self.service.crear(self.datos(), self.cliente)
        self.assertEqual(pedido.estado, "PENDIENTE")

    def test_copias_nombre_precio_y_total_no_cambian(self):
        pedido = self.service.crear(self.datos(), self.cliente)
        with self.factory() as session:
            producto = session.get(Producto, 1)
            producto.nombre = "Otro nombre"
            producto.precio_base = 999
            session.commit()
        lectura = self.service.obtener(pedido.id, self.cliente)
        self.assertEqual(lectura.items[0].nombre_producto, "Pizza")
        self.assertEqual(lectura.items[0].precio_unitario, 10.5)
        self.assertEqual(lectura.items, pedido.items)
        self.assertEqual(lectura.total, pedido.total)

    def test_todas_las_transiciones_validas(self):
        for inicial, destino in (
            ("PENDIENTE", "EN_PREPARACION"),
            ("PENDIENTE", "CANCELADO"),
            ("EN_PREPARACION", "ENTREGADO"),
            ("EN_PREPARACION", "CANCELADO"),
        ):
            with self.subTest(inicial=inicial, destino=destino):
                pedido = self.service.crear(
                    self.datos([{"producto_id": 1, "cantidad": 1}]), self.cliente
                )
                if inicial == "EN_PREPARACION":
                    self.service.cambiar_estado(pedido.id, inicial)
                anterior = self.service.obtener(pedido.id, self.cliente)
                final = self.service.cambiar_estado(pedido.id, destino)
                self.assertEqual(final.estado, destino)
                self.assertEqual(final.items, anterior.items)
                self.assertEqual(final.total, anterior.total)
                self.assertGreaterEqual(final.updated_at, anterior.updated_at)

    def test_todas_las_transiciones_invalidas(self):
        mapa = PedidoService.TRANSICIONES
        for inicial in mapa:
            for destino in mapa:
                if destino in mapa[inicial]:
                    continue
                with self.subTest(inicial=inicial, destino=destino):
                    pedido = self.service.crear(
                        self.datos([{"producto_id": 3, "cantidad": 1}]), self.cliente
                    )
                    with self.factory() as session:
                        session.get(Pedido, pedido.id).estado = inicial
                        session.commit()
                    stock_previo = self.stocks()
                    with self.assertRaises(TransicionInvalida):
                        self.service.cambiar_estado(pedido.id, destino)
                    self.assertEqual(self.stocks(), stock_previo)
                    self.assertEqual(
                        self.service.obtener(pedido.id, self.cliente).estado, inicial
                    )
                    with self.factory() as session:
                        session.get(Producto, 3).stock = 5
                        session.commit()

    def test_cancelacion_restituye_sin_modificar_lineas_ni_total(self):
        pedido = self.service.crear(self.datos(), self.cliente)
        cancelado = self.service.cancelar(pedido.id, self.cliente)
        self.assertEqual(cancelado.estado, "CANCELADO")
        self.assertEqual(self.stocks(), {1: 10, 2: 8, 3: 5})
        self.assertEqual(cancelado.items, pedido.items)
        self.assertEqual(cancelado.total, pedido.total)

    def test_no_se_restituye_stock_dos_veces_por_ninguna_ruta(self):
        pedido = self.service.crear(self.datos(), self.cliente)
        self.service.cancelar(pedido.id, self.cliente)
        for operacion in (
            lambda: self.service.cancelar(pedido.id, self.cliente),
            lambda: self.service.cambiar_estado(pedido.id, "CANCELADO"),
        ):
            with self.assertRaises(TransicionInvalida):
                operacion()
            self.assertEqual(self.stocks(), {1: 10, 2: 8, 3: 5})

    def test_admin_cancela_ajeno_solo_por_estado(self):
        pedido = self.service.crear(self.datos(), self.cliente)
        self.service.cambiar_estado(pedido.id, "EN_PREPARACION")
        with self.assertRaises(TransicionInvalida):
            self.service.cancelar(pedido.id, self.cliente)
        self.assertEqual(self.stocks()[1], 8)
        with self.assertRaises(PedidoAjeno):
            self.service.cancelar(pedido.id, self.admin)
        self.assertEqual(
            self.service.cambiar_estado(pedido.id, "CANCELADO").estado, "CANCELADO"
        )
        self.assertEqual(self.stocks()[1], 10)

    def test_admin_dueno_cancela_solo_su_pedido_pendiente(self):
        pedido = self.service.crear(self.datos(), self.admin)
        self.assertEqual(
            self.service.cancelar(pedido.id, self.admin).estado, "CANCELADO"
        )
        otro = self.service.crear(self.datos(), self.admin)
        self.service.cambiar_estado(otro.id, "EN_PREPARACION")
        with self.assertRaises(TransicionInvalida):
            self.service.cancelar(otro.id, self.admin)

    def test_cancelacion_restituye_producto_inactivo(self):
        pedido = self.service.crear(self.datos(), self.cliente)
        with self.factory() as session:
            session.get(Producto, 1).activo = False
            session.commit()
        self.service.cancelar(pedido.id, self.cliente)
        self.assertEqual(self.stocks()[1], 10)

    def test_pedido_entregado_no_se_puede_cancelar(self):
        pedido = self.service.crear(self.datos(), self.cliente)
        self.service.cambiar_estado(pedido.id, "EN_PREPARACION")
        self.service.cambiar_estado(pedido.id, "ENTREGADO")
        with self.assertRaises(TransicionInvalida):
            self.service.cancelar(pedido.id, self.cliente)
        with self.assertRaises(PedidoAjeno):
            self.service.cancelar(pedido.id, self.admin)
        with self.assertRaises(TransicionInvalida):
            self.service.cambiar_estado(pedido.id, "CANCELADO")
        self.assertEqual(self.stocks(), {1: 8, 2: 5, 3: 5})

    def test_forma_pago_y_limites_de_direccion_validos(self):
        self.autenticar(self.cliente)
        for pago, direccion in (("EFECTIVO", "12345"), ("TRANSFERENCIA", "x" * 200)):
            datos = self.datos([{"producto_id": 3, "cantidad": 1}]).model_dump()
            datos.update(forma_pago=pago, direccion_entrega=direccion)
            respuesta = self.http.post("/api/v1/pedidos", json=datos)
            self.assertEqual(respuesta.status_code, 201)
            self.assertEqual(respuesta.json()["forma_pago"], pago)
            self.assertEqual(respuesta.json()["direccion_entrega"], direccion)

    def test_cancelacion_fallida_revierte_restitucion_parcial(self):
        pedido = self.service.crear(self.datos(), self.cliente)
        original = ProductoRepository.get_by_id_for_update

        def obtener(repository, id):
            return None if id == 2 else original(repository, id)

        with patch.object(ProductoRepository, "get_by_id_for_update", obtener):
            with self.assertRaises(ProductoNoEncontrado):
                self.service.cancelar(pedido.id, self.cliente)
        self.assertEqual(self.stocks(), {1: 8, 2: 5, 3: 5})
        self.assertEqual(
            self.service.obtener(pedido.id, self.cliente).estado, "PENDIENTE"
        )

    def test_permisos_dueno_admin_y_listados(self):
        pedido = self.service.crear(self.datos(), self.cliente)
        self.service.crear(self.datos([{"producto_id": 3, "cantidad": 1}]), self.otro)
        for operacion in (self.service.obtener, self.service.cancelar):
            with self.assertRaises(PedidoAjeno):
                operacion(pedido.id, self.otro)
            with self.assertRaises(PedidoNoEncontrado):
                operacion(999, self.cliente)
        self.assertEqual(self.service.obtener(pedido.id, self.admin).id, pedido.id)
        self.assertEqual(self.service.listar(self.cliente, 0, 20, None).total, 1)
        self.assertEqual(self.service.listar(self.admin, 0, 20, None).total, 2)
        self.service.cambiar_estado(pedido.id, "EN_PREPARACION")
        filtrado = self.service.listar(self.admin, 0, 1, "PENDIENTE")
        self.assertEqual(filtrado.total, 1)
        self.assertEqual(len(filtrado.items), 1)

    def test_resumen_vacio(self):
        self.assertEqual(
            self.service.resumen().model_dump(),
            {
                "pendientes": 0,
                "en_preparacion": 0,
                "entregados": 0,
                "cancelados": 0,
                "pedidos_hoy": 0,
                "ingresos_entregados": 0,
            },
        )

    def test_resumen_cuenta_estados_dia_y_solo_ingresos_entregados(self):
        ahora = datetime(2026, 11, 15, 12, tzinfo=UTC)
        inicio = ahora.replace(hour=0)
        with self.factory() as session:
            for estado, total, fecha in (
                ("PENDIENTE", 100, inicio),
                ("EN_PREPARACION", 200, inicio + timedelta(hours=2)),
                ("ENTREGADO", 30, inicio + timedelta(hours=23, minutes=59)),
                ("CANCELADO", 400, inicio + timedelta(days=1)),
                ("ENTREGADO", 20, inicio - timedelta(microseconds=1)),
            ):
                session.add(
                    Pedido(
                        usuario_id=1,
                        estado=estado,
                        forma_pago="EFECTIVO",
                        direccion_entrega="Calle 123",
                        total=total,
                        created_at=fecha,
                    )
                )
            session.commit()
        with patch("app.modules.pedidos.service.ahora_utc", return_value=ahora):
            self.assertEqual(
                self.service.resumen().model_dump(),
                {
                    "pendientes": 1,
                    "en_preparacion": 1,
                    "entregados": 2,
                    "cancelados": 1,
                    "pedidos_hoy": 3,
                    "ingresos_entregados": 50,
                },
            )

    def test_post_http_y_cookie_real(self):
        login = self.http.post(
            "/api/v1/auth/token", data={"username": "cliente", "password": "Clave1234!"}
        )
        self.assertEqual(login.status_code, 200)
        self.assertIn("HttpOnly", login.headers["set-cookie"])
        respuesta = self.http.post("/api/v1/pedidos", json=self.datos().model_dump())
        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.json()["usuario_id"], 1)
        self.assertEqual(self.stocks()[1], 8)

    def test_http_sin_sesion_y_cuenta_desactivada(self):
        for metodo, path, datos in (
            ("post", "/api/v1/pedidos", self.datos().model_dump()),
            ("get", "/api/v1/pedidos", None),
            ("get", "/api/v1/pedidos/resumen", None),
            ("get", "/api/v1/pedidos/1", None),
            ("patch", "/api/v1/pedidos/1/estado", {"estado": "ENTREGADO"}),
            ("patch", "/api/v1/pedidos/1/cancelar", None),
        ):
            with self.subTest(path=path):
                self.autenticar()
                self.assertEqual(
                    self.http.request(metodo, path, json=datos).status_code, 401
                )
                self.autenticar(self.inactivo)
                respuesta = self.http.request(metodo, path, json=datos)
                self.assertEqual(respuesta.status_code, 400)
                self.assertEqual(
                    respuesta.json()["detail"], "Cuenta de usuario desactivada"
                )

    def test_http_validaciones_422(self):
        self.autenticar(self.cliente)
        validos = self.datos().model_dump()
        for campo, valores in (
            (
                "items",
                [
                    [],
                    [{"producto_id": 1, "cantidad": 0}],
                    [{"producto_id": 1, "cantidad": 1.5}],
                    [{"producto_id": 1, "cantidad": True}],
                    [{"producto_id": 1, "cantidad": "1"}],
                ],
            ),
            ("forma_pago", ["TARJETA", "efectivo", None]),
            ("direccion_entrega", ["1234", "x" * 201, None]),
            ("usuario_id", [2]),
            ("total", [1]),
        ):
            for valor in valores:
                with self.subTest(campo=campo, valor=valor):
                    respuesta = self.http.post(
                        "/api/v1/pedidos", json={**validos, campo: valor}
                    )
                    self.assertEqual(respuesta.status_code, 422)
        self.comprobar_sin_pedido()

    def test_http_errores_negocio_400_y_404(self):
        self.autenticar(self.cliente)
        for items, codigo in (
            ([{"producto_id": 1, "cantidad": 11}], 400),
            ([{"producto_id": 1, "cantidad": 1}] * 2, 400),
            ([{"producto_id": 999, "cantidad": 1}], 404),
        ):
            respuesta = self.http.post(
                "/api/v1/pedidos", json=self.datos(items).model_dump()
            )
            self.assertEqual(respuesta.status_code, codigo)
            self.comprobar_sin_pedido()
        for campo, codigo in (("activo", 404), ("disponible", 400)):
            with self.factory() as session:
                producto = session.get(Producto, 1)
                producto.activo = campo != "activo"
                producto.disponible = campo != "disponible"
                session.commit()
            respuesta = self.http.post(
                "/api/v1/pedidos", json=self.datos().model_dump()
            )
            self.assertEqual(respuesta.status_code, codigo)
            self.comprobar_sin_pedido()

    def test_http_permisos_estados_cancelacion_y_resumen(self):
        pedido = self.service.crear(self.datos(), self.cliente)
        self.autenticar(self.otro)
        self.assertEqual(self.http.get(f"/api/v1/pedidos/{pedido.id}").status_code, 403)
        self.assertEqual(
            self.http.patch(f"/api/v1/pedidos/{pedido.id}/cancelar").status_code, 403
        )
        self.assertEqual(self.http.get("/api/v1/pedidos/resumen").status_code, 403)
        self.assertEqual(
            self.http.patch(
                f"/api/v1/pedidos/{pedido.id}/estado", json={"estado": "EN_PREPARACION"}
            ).status_code,
            403,
        )
        self.autenticar(self.admin)
        self.assertEqual(self.http.get("/api/v1/pedidos/resumen").status_code, 200)
        self.assertEqual(
            self.http.patch(
                "/api/v1/pedidos/999/estado", json={"estado": "EN_PREPARACION"}
            ).status_code,
            404,
        )
        self.assertEqual(
            self.http.patch(
                f"/api/v1/pedidos/{pedido.id}/estado", json={"estado": "OTRO"}
            ).status_code,
            422,
        )
        self.assertEqual(
            self.http.patch(
                f"/api/v1/pedidos/{pedido.id}/estado", json={"estado": "ENTREGADO"}
            ).status_code,
            400,
        )
        self.assertEqual(
            self.http.patch(
                f"/api/v1/pedidos/{pedido.id}/estado", json={"estado": "EN_PREPARACION"}
            ).status_code,
            200,
        )
        self.autenticar(self.cliente)
        self.assertEqual(
            self.http.patch(f"/api/v1/pedidos/{pedido.id}/cancelar").status_code, 400
        )
        self.autenticar(self.admin)
        self.assertEqual(
            self.http.patch(f"/api/v1/pedidos/{pedido.id}/cancelar").status_code, 403
        )
        self.assertEqual(
            self.http.patch(
                f"/api/v1/pedidos/{pedido.id}/estado", json={"estado": "CANCELADO"}
            ).status_code,
            200,
        )
        self.assertEqual(self.http.get("/api/v1/pedidos/999").status_code, 404)
        self.assertEqual(
            self.http.patch("/api/v1/pedidos/999/cancelar").status_code, 404
        )

    def test_no_existen_endpoints_de_edicion_o_borrado(self):
        pedido = self.service.crear(self.datos(), self.cliente)
        self.autenticar(self.admin)
        for metodo in ("put", "delete", "patch"):
            self.assertEqual(
                self.http.request(
                    metodo, f"/api/v1/pedidos/{pedido.id}", json={"total": 1}
                ).status_code,
                405,
            )
        for path in (f"/api/v1/pedidos/{pedido.id}/items", "/api/v1/detalles"):
            self.assertEqual(
                self.http.post(path, json={"cantidad": 999}).status_code, 404
            )
        self.assertEqual(
            self.http.patch(
                f"/api/v1/pedidos/{pedido.id}/estado",
                json={"estado": "EN_PREPARACION", "total": 1},
            ).status_code,
            422,
        )
        self.assertEqual(
            self.service.obtener(pedido.id, self.admin).total, pedido.total
        )

    def test_resumen_se_declara_antes_del_detalle(self):
        paths = [r.path for r in router.routes]
        self.assertLess(paths.index("/pedidos/resumen"), paths.index("/pedidos/{id}"))

    def test_consultas_de_bloqueo_compilan_for_update_postgresql(self):
        for repo in (ProductoRepository, PedidoRepository):
            session = Mock()
            repo(session).get_by_id_for_update(1)
            consulta = session.exec.call_args.args[0]
            sql = str(consulta.compile(dialect=postgresql.dialect()))
            self.assertIn("FOR UPDATE", sql)
            self.assertTrue(consulta.get_execution_options()["populate_existing"])

    def test_bloqueos_en_orden_ascendente(self):
        original = ProductoRepository.get_by_id_for_update
        orden = []

        def obtener(repo, id):
            orden.append(id)
            return original(repo, id)

        with patch.object(ProductoRepository, "get_by_id_for_update", obtener):
            pedido = self.service.crear(
                self.datos(
                    [
                        {"producto_id": 2, "cantidad": 1},
                        {"producto_id": 1, "cantidad": 1},
                    ]
                ),
                self.cliente,
            )
            self.assertEqual(orden, [1, 2])
            orden.clear()
            self.service.cancelar(pedido.id, self.cliente)
            self.assertEqual(orden, [1, 2])


if __name__ == "__main__":
    unittest.main()
