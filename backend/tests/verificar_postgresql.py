# ruff: noqa: E402

import os
import secrets
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from sqlalchemy.engine import make_url

url = os.environ.get("TPI_TEST_DATABASE_URL", "")
if not url or not (make_url(url).database or "").startswith("foodstore_tpi_test_"):
    raise RuntimeError("Uso únicamente una base foodstore_tpi_test_* explícita")
os.environ["DATABASE_URL"] = url

from app.core.database import engine
from app.core.security import verify_password
from app.db.seed import cargar_seed
from app.main import app
from app.modules.categorias.models import Categoria
from app.modules.pedidos.models import DetallePedido, Pedido, ahora_utc
from app.modules.pedidos.schemas import PedidoCreate
from app.modules.pedidos.service import (
    PedidoService,
    StockInsuficiente,
    TransicionInvalida,
)
from app.modules.pedidos.unit_of_work import PedidoUnitOfWork
from app.modules.productos.models import Producto
from app.modules.usuarios.models import Usuario
from app.modules.usuarios.schemas import UserPublic
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text
from sqlmodel import Session, create_engine, func, select


class PostgreSQLTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cargar_seed()
        cls.concurrent_engine = create_engine(
            url,
            hide_parameters=True,
            connect_args={"options": "-c lock_timeout=8000 -c statement_timeout=12000"},
        )

    @classmethod
    def tearDownClass(cls):
        cls.concurrent_engine.dispose()
        engine.dispose()

    def setUp(self):
        self.tag = secrets.token_hex(6)
        self.admin = TestClient(app)
        self.client = TestClient(app)
        self.other = TestClient(app)
        for client in (self.admin, self.client, self.other):
            self.addCleanup(client.close)
        self.check(
            self.admin.post(
                "/api/v1/auth/token",
                data={
                    "username": "admin",
                    "password": "Admin1234!",
                },
            ),
            200,
        )
        for client, nombre in ((self.client, "cliente"), (self.other, "otro")):
            username = nombre + self.tag
            registrado = self.check(
                client.post(
                    "/api/v1/auth/register",
                    json={
                        "username": username,
                        "full_name": nombre,
                        "email": username + "@example.com",
                        "password": "Prueba1234!",
                    },
                ),
                201,
            )
            self.check(
                client.post(
                    "/api/v1/auth/token",
                    data={
                        "username": username,
                        "password": "Prueba1234!",
                    },
                ),
                200,
            )
            if client is self.client:
                self.user = UserPublic.model_validate(registrado)
        self.category = self.check(
            self.admin.post(
                "/api/v1/categorias",
                json={
                    "nombre": "Categoria " + self.tag,
                },
            ),
            201,
        )["id"]
        self.products = []
        for n in (1, 2):
            producto = self.check(
                self.admin.post(
                    "/api/v1/productos",
                    json={
                        "nombre": f"Producto {n} {self.tag}",
                        "categoria_id": self.category,
                        "precio_base": 10.5 * n,
                        "stock": 3,
                    },
                ),
                201,
            )
            self.products.append(producto["id"])

    def check(self, respuesta, codigo):
        self.assertEqual(respuesta.status_code, codigo, respuesta.text)
        return respuesta.json() if respuesta.content else None

    def datos(self, items=None):
        return {
            "items": items
            if items is not None
            else [
                {"producto_id": self.products[0], "cantidad": 1},
                {"producto_id": self.products[1], "cantidad": 2},
            ],
            "forma_pago": "EFECTIVO",
            "direccion_entrega": "Calle 123",
        }

    def stock(self, id):
        with Session(engine) as session:
            return session.get(Producto, id).stock

    def compra(self, items=None):
        return self.check(
            self.client.post("/api/v1/pedidos", json=self.datos(items)), 201
        )

    def test_auth_usuarios_y_codigos(self):
        with TestClient(app) as publico:
            self.check(publico.get("/api/v1/auth/me"), 401)
            self.check(
                publico.post(
                    "/api/v1/auth/token",
                    data={
                        "username": "admin",
                        "password": "incorrecta",
                    },
                ),
                401,
            )
            login = publico.post(
                "/api/v1/auth/token",
                data={
                    "username": "admin",
                    "password": "Admin1234!",
                },
            )
            self.assertEqual(self.check(login, 200), {"message": "Login exitoso"})
            self.assertIn("HttpOnly", login.headers["set-cookie"])
            self.assertIn("SameSite=lax", login.headers["set-cookie"])
            admin = self.check(publico.get("/api/v1/auth/me"), 200)
            self.assertNotIn("hashed_password", admin)
            self.check(
                publico.post(f"/api/v1/admin/usuarios/{admin['id']}/desactivar"), 400
            )
            self.check(publico.post("/api/v1/auth/logout"), 200)
            self.check(publico.get("/api/v1/auth/me"), 401)
        self.check(self.client.get("/api/v1/admin/usuarios"), 403)
        self.check(self.admin.post("/api/v1/admin/usuarios/2147483647/activar"), 404)
        for _ in range(2):
            self.check(
                self.admin.post(f"/api/v1/admin/usuarios/{self.user.id}/desactivar"),
                200,
            )
        self.check(self.client.get("/api/v1/auth/me"), 400)
        self.check(
            self.client.post(
                "/api/v1/auth/token",
                data={
                    "username": self.user.username,
                    "password": "Prueba1234!",
                },
            ),
            400,
        )
        for _ in range(2):
            self.check(
                self.admin.post(f"/api/v1/admin/usuarios/{self.user.id}/activar"), 200
            )
        self.check(self.client.get("/api/v1/auth/me"), 200)
        self.check(
            self.client.post(
                "/api/v1/auth/register",
                json={
                    "username": self.user.username,
                    "full_name": "duplicado",
                    "email": self.user.email,
                    "password": "Prueba1234!",
                },
            ),
            409,
        )

    def test_catalogo_completo(self):
        id = self.products[0]
        with TestClient(app) as publico:
            self.check(publico.get("/api/v1/categorias"), 200)
            self.check(publico.get(f"/api/v1/categorias/{self.category}"), 200)
            self.check(
                publico.post("/api/v1/categorias", json={"nombre": "Sin sesion"}), 401
            )
            self.check(publico.get(f"/api/v1/productos/{id}"), 200)
            listado = self.check(
                publico.get(
                    "/api/v1/productos",
                    params={
                        "categoria_id": self.category,
                        "search": "PRODUCTO",
                        "skip": 1,
                        "limit": 1,
                    },
                ),
                200,
            )
            self.assertEqual(listado["total"], 2)
            self.assertEqual(len(listado["items"]), 1)
            self.check(publico.get("/api/v1/productos?limit=101"), 422)
        self.check(
            self.client.post(
                "/api/v1/productos",
                json={
                    "nombre": "Sin rol",
                    "categoria_id": self.category,
                    "precio_base": 1,
                },
            ),
            403,
        )
        self.check(
            self.admin.post(
                "/api/v1/categorias",
                json={
                    "nombre": "Categoria " + self.tag,
                },
            ),
            409,
        )
        self.check(
            self.admin.post(
                "/api/v1/productos",
                json={
                    "nombre": "Invalido",
                    "categoria_id": 2147483647,
                    "precio_base": 1,
                },
            ),
            404,
        )
        self.check(
            self.admin.post(
                "/api/v1/productos",
                json={
                    "nombre": "Invalido",
                    "categoria_id": self.category,
                    "precio_base": -1,
                },
            ),
            422,
        )
        cambio = self.check(
            self.admin.put(f"/api/v1/productos/{id}", json={"nombre": "Editado"}), 200
        )
        self.assertEqual(cambio["precio_base"], 10.5)
        self.check(
            self.admin.patch(
                f"/api/v1/productos/{id}/stock",
                json={
                    "stock": 7,
                    "disponible": False,
                },
            ),
            200,
        )
        filtrado = self.check(
            self.admin.get(
                "/api/v1/productos",
                params={
                    "categoria_id": self.category,
                    "disponible": False,
                },
            ),
            200,
        )
        self.assertEqual([p["id"] for p in filtrado["items"]], [id])
        self.check(
            self.admin.put(
                f"/api/v1/categorias/{self.category}", json={"descripcion": "Editada"}
            ),
            200,
        )
        self.check(self.admin.delete(f"/api/v1/categorias/{self.category}"), 204)
        self.check(self.admin.get(f"/api/v1/productos/{id}"), 200)
        self.check(self.admin.get(f"/api/v1/categorias/{self.category}"), 404)
        self.check(
            self.admin.put(
                f"/api/v1/categorias/{self.category}", json={"descripcion": "Otra"}
            ),
            404,
        )
        self.check(self.admin.delete(f"/api/v1/categorias/{self.category}"), 404)
        self.check(
            self.admin.post(
                "/api/v1/categorias", json={"nombre": "Categoria " + self.tag}
            ),
            409,
        )
        self.check(self.admin.delete(f"/api/v1/productos/{id}"), 204)
        for metodo, suffix, datos in (
            ("get", "", None),
            ("put", "", {"nombre": "Otra"}),
            ("patch", "/stock", {"stock": 2}),
            ("delete", "", None),
        ):
            self.check(
                self.admin.request(
                    metodo, f"/api/v1/productos/{id}{suffix}", json=datos
                ),
                404,
            )
        with Session(engine) as session:
            self.assertFalse(session.get(Producto, id).activo)
            self.assertFalse(session.get(Categoria, self.category).activo)

    def test_compra_rollback_cancelacion_y_copias(self):
        pedido = self.compra()
        id = pedido["id"]
        self.assertEqual(pedido["total"], 52.5)
        self.assertEqual([self.stock(p) for p in self.products], [2, 1])
        self.check(
            self.admin.put(
                f"/api/v1/productos/{self.products[0]}",
                json={"nombre": "Cambio", "precio_base": 999},
            ),
            200,
        )
        actual = self.check(self.client.get(f"/api/v1/pedidos/{id}"), 200)
        self.assertEqual(actual["items"], pedido["items"])
        self.assertEqual(actual["total"], pedido["total"])
        for endpoint in (f"/api/v1/pedidos/{id}", f"/api/v1/pedidos/{id}/cancelar"):
            self.check(
                self.other.request(
                    "get" if endpoint.endswith(str(id)) else "patch", endpoint
                ),
                403,
            )
        self.check(self.admin.patch(f"/api/v1/pedidos/{id}/cancelar"), 403)
        antes = self.check(self.client.get("/api/v1/pedidos"), 200)["total"]
        self.assertEqual(antes, 1)
        self.assertEqual(self.check(self.other.get("/api/v1/pedidos"), 200)["total"], 0)
        self.check(
            self.client.post(
                "/api/v1/pedidos",
                json=self.datos(
                    [
                        {"producto_id": self.products[0], "cantidad": 1},
                        {"producto_id": self.products[1], "cantidad": 99},
                    ]
                ),
            ),
            400,
        )
        self.assertEqual(
            self.check(self.client.get("/api/v1/pedidos"), 200)["total"], antes
        )
        self.assertEqual([self.stock(p) for p in self.products], [2, 1])
        cancelado = self.check(self.client.patch(f"/api/v1/pedidos/{id}/cancelar"), 200)
        self.assertEqual(cancelado["estado"], "CANCELADO")
        self.assertEqual(cancelado["items"], pedido["items"])
        self.assertEqual(cancelado["total"], pedido["total"])
        self.check(self.client.patch(f"/api/v1/pedidos/{id}/cancelar"), 400)
        self.assertEqual([self.stock(p) for p in self.products], [3, 3])
        for metodo in ("put", "delete", "patch"):
            self.check(
                self.admin.request(metodo, f"/api/v1/pedidos/{id}", json={"total": 1}),
                405,
            )

    def test_transiciones_cancelacion_dueno_admin_y_resumen(self):
        pedido = self.compra()
        id = pedido["id"]
        ruta = f"/api/v1/pedidos/{id}/estado"
        self.check(self.client.patch(ruta, json={"estado": "EN_PREPARACION"}), 403)
        self.check(self.admin.patch(ruta, json={"estado": "ENTREGADO"}), 400)
        self.check(self.admin.patch(ruta, json={"estado": "EN_PREPARACION"}), 200)
        self.check(self.client.patch(f"/api/v1/pedidos/{id}/cancelar"), 400)
        self.check(self.admin.patch(f"/api/v1/pedidos/{id}/cancelar"), 403)
        final = self.check(self.admin.patch(ruta, json={"estado": "ENTREGADO"}), 200)
        self.assertEqual(final["items"], pedido["items"])
        self.check(self.admin.patch(ruta, json={"estado": "CANCELADO"}), 400)
        propio = self.check(
            self.admin.post(
                "/api/v1/pedidos",
                json=self.datos(
                    [
                        {"producto_id": self.products[0], "cantidad": 1},
                    ]
                ),
            ),
            201,
        )
        self.check(self.admin.patch(f"/api/v1/pedidos/{propio['id']}/cancelar"), 200)
        propio = self.check(
            self.admin.post(
                "/api/v1/pedidos",
                json=self.datos(
                    [
                        {"producto_id": self.products[0], "cantidad": 1},
                    ]
                ),
            ),
            201,
        )
        self.check(
            self.admin.patch(
                f"/api/v1/pedidos/{propio['id']}/estado",
                json={"estado": "EN_PREPARACION"},
            ),
            200,
        )
        self.check(self.admin.patch(f"/api/v1/pedidos/{propio['id']}/cancelar"), 400)
        self.check(
            self.admin.patch(
                f"/api/v1/pedidos/{propio['id']}/estado", json={"estado": "CANCELADO"}
            ),
            200,
        )
        self.check(self.client.get("/api/v1/pedidos/resumen"), 403)
        resumen = self.check(self.admin.get("/api/v1/pedidos/resumen"), 200)
        with Session(engine) as session:
            for campo, estado in (
                ("pendientes", "PENDIENTE"),
                ("en_preparacion", "EN_PREPARACION"),
                ("entregados", "ENTREGADO"),
                ("cancelados", "CANCELADO"),
            ):
                self.assertEqual(
                    resumen[campo],
                    session.exec(
                        select(func.count())
                        .select_from(Pedido)
                        .where(Pedido.estado == estado)
                    ).one(),
                )
            ingresos = session.exec(
                select(func.coalesce(func.sum(Pedido.total), 0)).where(
                    Pedido.estado == "ENTREGADO"
                )
            ).one()
            self.assertAlmostEqual(resumen["ingresos_entregados"], ingresos)
            desde = ahora_utc().replace(hour=0, minute=0, second=0, microsecond=0)
            hoy = session.exec(
                select(func.count())
                .select_from(Pedido)
                .where(
                    Pedido.created_at >= desde,
                )
            ).one()
            self.assertEqual(resumen["pedidos_hoy"], hoy)

    def test_seed_idempotente_y_esquema_real(self):
        with Session(engine) as session:
            antes = [
                session.exec(select(func.count()).select_from(m)).one()
                for m in (Usuario, Categoria, Producto)
            ]
            admin = session.exec(
                select(Usuario).where(Usuario.username == "admin")
            ).one()
            hashed = admin.hashed_password
            self.assertTrue(verify_password("Admin1234!", hashed))
        self.assertEqual(
            cargar_seed(), {"usuarios": 0, "categorias": 0, "productos": 0}
        )
        with Session(engine) as session:
            self.assertEqual(
                antes,
                [
                    session.exec(select(func.count()).select_from(m)).one()
                    for m in (Usuario, Categoria, Producto)
                ],
            )
            self.assertEqual(
                session.exec(select(Usuario).where(Usuario.username == "admin"))
                .one()
                .hashed_password,
                hashed,
            )
        inspector = inspect(engine)
        self.assertEqual(
            set(inspector.get_table_names()),
            {"usuario", "categoria", "producto", "pedido", "detallepedido"},
        )
        for model in (Usuario, Categoria, Producto, Pedido, DetallePedido):
            tabla = model.__tablename__
            self.assertEqual(
                {c["name"] for c in inspector.get_columns(tabla)},
                set(model.__table__.columns.keys()),
            )
            self.assertEqual(
                inspector.get_pk_constraint(tabla)["constrained_columns"], ["id"]
            )
            for c in inspector.get_columns(tabla):
                self.assertEqual(c["nullable"], model.__table__.c[c["name"]].nullable)
                if c["name"] == "id":
                    self.assertIn("nextval", c["default"])
            self.assertEqual(
                len(inspector.get_foreign_keys(tabla)),
                len(model.__table__.foreign_keys),
            )
            reales = {
                (
                    tuple(fk["constrained_columns"]),
                    fk["referred_table"],
                    tuple(fk["referred_columns"]),
                )
                for fk in inspector.get_foreign_keys(tabla)
            }
            esperadas = {
                ((fk.parent.name,), fk.column.table.name, (fk.column.name,))
                for fk in model.__table__.foreign_keys
            }
            self.assertEqual(reales, esperadas)
        for tabla, campos in (
            ("usuario", {"username", "email"}),
            ("categoria", {"nombre"}),
        ):
            self.assertEqual(
                {c["column_names"][0] for c in inspector.get_unique_constraints(tabla)},
                campos,
            )

    def race(self, acciones, tabla, id):
        ready = Barrier(3)
        pids = []

        def factory():
            session = Session(self.concurrent_engine, expire_on_commit=False)
            pids.append(session.exec(select(func.pg_backend_pid())).one())
            ready.wait(timeout=10)
            return session

        def ejecutar(accion):
            service = PedidoService(PedidoUnitOfWork(factory))
            try:
                return accion(service)
            except (StockInsuficiente, TransicionInvalida) as error:
                return error

        with self.concurrent_engine.connect() as guard:
            transaction = guard.begin()
            guard.execute(
                text(f"SELECT id FROM {tabla} WHERE id=:id FOR UPDATE"), {"id": id}
            )
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(ejecutar, accion) for accion in acciones]
                try:
                    ready.wait(timeout=10)
                    self.assertEqual(len(set(pids)), 2)
                    limite = time.monotonic() + 6
                    esperando = 0
                    while time.monotonic() < limite:
                        with self.concurrent_engine.connect() as observador:
                            esperando = observador.execute(
                                text(
                                    "SELECT count(*) FROM pg_stat_activity "
                                    "WHERE pid=ANY(:pids) AND wait_event_type='Lock'"
                                ),
                                {"pids": pids},
                            ).scalar_one()
                        if esperando == 2:
                            break
                        time.sleep(0.03)
                    self.assertEqual(
                        esperando, 2, "Ambas conexiones deben esperar un bloqueo real"
                    )
                finally:
                    # Libero únicamente el bloqueo de lectura de la prueba.
                    transaction.rollback()
                return [future.result(timeout=15) for future in futures]

    def test_defaults_orm_persistidos(self):
        with Session(engine) as session:
            admin = session.exec(
                select(Usuario).where(Usuario.username == "admin")
            ).one()
            usuario = Usuario(
                username="defaults" + self.tag,
                full_name="Defaults",
                email="defaults" + self.tag + "@example.com",
                hashed_password=admin.hashed_password,
            )
            categoria = Categoria(nombre="Defaults " + self.tag)
            session.add_all([usuario, categoria])
            session.flush()
            producto = Producto(
                categoria_id=categoria.id, nombre="Defaults", precio_base=0
            )
            pedido = Pedido(
                usuario_id=usuario.id,
                forma_pago="EFECTIVO",
                direccion_entrega="Calle 123",
                total=0,
            )
            session.add_all([producto, pedido])
            session.flush()
            for objeto in (usuario, categoria, producto, pedido):
                session.refresh(objeto)
            self.assertEqual(usuario.role, "user")
            self.assertFalse(usuario.disabled)
            self.assertTrue(categoria.activo)
            self.assertEqual(producto.stock, 0)
            self.assertTrue(producto.disponible and producto.activo)
            self.assertEqual(pedido.estado, "PENDIENTE")
            self.assertIsNotNone(usuario.created_at)
            self.assertIsNotNone(pedido.created_at)
            self.assertIsNotNone(pedido.updated_at)

    def test_concurrencia_dos_compras_stock_insuficiente(self):
        id = self.products[0]
        datos = PedidoCreate.model_validate(
            self.datos([{"producto_id": id, "cantidad": 2}])
        )
        resultados = self.race(
            [lambda s: s.crear(datos, self.user)] * 2, "producto", id
        )
        self.assertEqual(sum(isinstance(r, StockInsuficiente) for r in resultados), 1)
        self.assertEqual(self.stock(id), 1)
        with Session(engine) as session:
            self.assertEqual(
                session.exec(
                    select(func.count())
                    .select_from(Pedido)
                    .where(Pedido.usuario_id == self.user.id)
                ).one(),
                1,
            )

    def test_concurrencia_dos_cancelaciones(self):
        pedido = self.compra()
        resultados = self.race(
            [
                lambda s: s.cancelar(pedido["id"], self.user),
                lambda s: s.cambiar_estado(pedido["id"], "CANCELADO"),
            ],
            "pedido",
            pedido["id"],
        )
        self.assertEqual(sum(isinstance(r, TransicionInvalida) for r in resultados), 1)
        self.assertEqual([self.stock(p) for p in self.products], [3, 3])
        self.assertEqual(
            self.check(self.client.get(f"/api/v1/pedidos/{pedido['id']}"), 200)[
                "estado"
            ],
            "CANCELADO",
        )

    def test_concurrencia_cancelar_y_avanzar(self):
        pedido = self.compra()
        resultados = self.race(
            [
                lambda s: s.cancelar(pedido["id"], self.user),
                lambda s: s.cambiar_estado(pedido["id"], "EN_PREPARACION"),
            ],
            "pedido",
            pedido["id"],
        )
        self.assertEqual(sum(isinstance(r, TransicionInvalida) for r in resultados), 1)
        final = self.check(self.client.get(f"/api/v1/pedidos/{pedido['id']}"), 200)
        self.assertIn(final["estado"], {"CANCELADO", "EN_PREPARACION"})
        self.assertEqual(
            [self.stock(p) for p in self.products],
            [3, 3] if final["estado"] == "CANCELADO" else [2, 1],
        )
        self.assertEqual(final["items"], pedido["items"])
        self.assertEqual(final["total"], pedido["total"])

    def test_concurrencia_carritos_orden_inverso(self):
        items = [{"producto_id": id, "cantidad": 1} for id in self.products]
        a = PedidoCreate.model_validate(self.datos(items))
        b = PedidoCreate.model_validate(self.datos(list(reversed(items))))
        resultados = self.race(
            [lambda s: s.crear(a, self.user), lambda s: s.crear(b, self.user)],
            "producto",
            self.products[0],
        )
        self.assertTrue(
            all(
                isinstance(r, object) and not isinstance(r, Exception)
                for r in resultados
            )
        )
        self.assertEqual([self.stock(p) for p in self.products], [1, 1])
        self.assertEqual(len({r.id for r in resultados}), 2)


if __name__ == "__main__":
    unittest.main()
