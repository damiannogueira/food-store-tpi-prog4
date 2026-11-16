# ruff: noqa: E402

import ast
import importlib
import os
import pkgutil
import unittest
from pathlib import Path
from unittest.mock import Mock

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "clave-temporal-para-verificar-la-base-del-tpi"

import app
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.core.unit_of_work import UnitOfWork
from app.main import app as api
from app.modules.categorias.models import Categoria
from app.modules.categorias.schemas import CategoriaCreate, CategoriaUpdate
from app.modules.pedidos.models import DetallePedido, Pedido
from app.modules.pedidos.schemas import PedidoCreate, PedidoRead
from app.modules.pedidos.unit_of_work import PedidoUnitOfWork
from app.modules.productos.models import Producto
from app.modules.productos.schemas import ProductoCreate, ProductoRead, ProductoUpdate
from app.modules.productos.unit_of_work import ProductoUnitOfWork
from app.modules.usuarios.models import Usuario
from app.modules.usuarios.schemas import UserPublic
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import event, inspect
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import Engine
from sqlalchemy.orm import configure_mappers
from sqlalchemy.schema import CreateTable
from sqlmodel import SQLModel


def impedir_conexion(*args, **kwargs):
    raise AssertionError("Esta verificación no debe abrir conexiones")


class BaseTpiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Bloqueo conexiones solo durante estas verificaciones sin base.
        event.listen(Engine, "do_connect", impedir_conexion)

    @classmethod
    def tearDownClass(cls):
        event.remove(Engine, "do_connect", impedir_conexion)

    def test_importaciones_y_sintaxis(self):
        for archivo in Path("app").rglob("*.py"):
            ast.parse(archivo.read_text(encoding="utf-8"))
        for modulo in pkgutil.walk_packages(app.__path__, "app."):
            importlib.import_module(modulo.name)

    def test_tablas_y_campos_exactos(self):
        esperados = {
            "usuario": (
                "id username full_name email hashed_password role disabled created_at"
            ),
            "categoria": "id nombre descripcion activo",
            "producto": (
                "id categoria_id nombre descripcion precio_base imagen_url "
                "stock disponible activo"
            ),
            "pedido": (
                "id usuario_id estado forma_pago direccion_entrega notas "
                "total created_at updated_at"
            ),
            "detallepedido": (
                "id pedido_id producto_id cantidad nombre_producto "
                "precio_unitario subtotal"
            ),
        }
        self.assertEqual(set(SQLModel.metadata.tables), set(esperados))
        for nombre, campos in esperados.items():
            tabla = SQLModel.metadata.tables[nombre]
            self.assertEqual(set(tabla.columns.keys()), set(campos.split()))
            self.assertEqual([c.name for c in tabla.primary_key], ["id"])
            self.assertIs(tabla.c.id.type.python_type, int)
            self.assertTrue(
                str(CreateTable(tabla).compile(dialect=postgresql.dialect()))
            )

    def test_tipos_claves_y_restricciones(self):
        for modelo, campo in (
            (Producto, "precio_base"),
            (Pedido, "total"),
            (DetallePedido, "precio_unitario"),
            (DetallePedido, "subtotal"),
        ):
            self.assertIs(modelo.__table__.c[campo].type.python_type, float)
        for modelo, campo, destino in (
            (Producto, "categoria_id", "categoria.id"),
            (Pedido, "usuario_id", "usuario.id"),
            (DetallePedido, "pedido_id", "pedido.id"),
            (DetallePedido, "producto_id", "producto.id"),
        ):
            columna = modelo.__table__.c[campo]
            self.assertFalse(columna.nullable)
            self.assertEqual(
                {fk.target_fullname for fk in columna.foreign_keys}, {destino}
            )
        for modelo, campo in (
            (Usuario, "username"),
            (Usuario, "email"),
            (Categoria, "nombre"),
        ):
            self.assertTrue(modelo.__table__.c[campo].unique)
        for tabla in SQLModel.metadata.tables.values():
            for columna in tabla.columns:
                if columna.name not in {"descripcion", "imagen_url", "notas"}:
                    self.assertFalse(columna.nullable)

    def test_relaciones_bidireccionales(self):
        configure_mappers()
        for origen, atributo, destino, inversa, coleccion in (
            (Categoria, "productos", Producto, "categoria", True),
            (Producto, "categoria", Categoria, "productos", False),
            (Usuario, "pedidos", Pedido, "usuario", True),
            (Pedido, "usuario", Usuario, "pedidos", False),
            (Pedido, "items", DetallePedido, "pedido", True),
            (DetallePedido, "pedido", Pedido, "items", False),
            (Producto, "detalles", DetallePedido, "producto", True),
            (DetallePedido, "producto", Producto, "detalles", False),
        ):
            relacion = inspect(origen).relationships[atributo]
            self.assertIs(relacion.mapper.class_, destino)
            self.assertEqual(relacion.back_populates, inversa)
            self.assertEqual(relacion.uselist, coleccion)

    def test_defaults_y_schemas_de_lectura(self):
        usuario = Usuario(
            id=1,
            username="cliente",
            full_name="Cliente",
            email="cliente@example.com",
            hashed_password="no-exponer",
        )
        categoria = Categoria(id=1, nombre="Comidas")
        producto = Producto(
            id=1, categoria=categoria, categoria_id=1, nombre="Pizza", precio_base=10
        )
        pedido = Pedido(
            id=1,
            usuario=usuario,
            usuario_id=1,
            forma_pago="EFECTIVO",
            direccion_entrega="Calle 123",
            total=20,
        )
        detalle = DetallePedido(
            id=1,
            pedido=pedido,
            producto=producto,
            pedido_id=1,
            producto_id=1,
            cantidad=2,
            nombre_producto="Pizza",
            precio_unitario=10,
            subtotal=20,
        )
        self.assertEqual(usuario.role, "user")
        self.assertFalse(usuario.disabled)
        self.assertTrue(categoria.activo)
        self.assertEqual(producto.stock, 0)
        self.assertTrue(producto.activo and producto.disponible)
        self.assertEqual(pedido.estado, "PENDIENTE")
        self.assertEqual(ProductoRead.model_validate(producto).categoria.id, 1)
        self.assertEqual(PedidoRead.model_validate(pedido).items[0].subtotal, 20)
        self.assertIs(pedido.items[0], detalle)
        self.assertNotIn(
            "hashed_password", UserPublic.model_validate(usuario).model_dump()
        )

    def test_validaciones_de_schemas(self):
        for modelo, datos in (
            (CategoriaCreate, {"nombre": "x"}),
            (CategoriaUpdate, {"nombre": None}),
            (ProductoCreate, {"nombre": "Pizza", "precio_base": -1, "categoria_id": 1}),
            (
                ProductoCreate,
                {"nombre": "Pizza", "precio_base": 1, "categoria_id": 1, "stock": -1},
            ),
            (ProductoUpdate, {"stock": None}),
            (
                PedidoCreate,
                {
                    "items": [],
                    "forma_pago": "EFECTIVO",
                    "direccion_entrega": "Calle 123",
                },
            ),
            (
                PedidoCreate,
                {
                    "items": [{"producto_id": 1, "cantidad": 0}],
                    "forma_pago": "EFECTIVO",
                    "direccion_entrega": "Calle 123",
                },
            ),
            (
                PedidoCreate,
                {
                    "items": [{"producto_id": 1, "cantidad": 1}],
                    "forma_pago": "TARJETA",
                    "direccion_entrega": "Calle 123",
                },
            ),
            (
                PedidoCreate,
                {
                    "items": [{"producto_id": 1, "cantidad": 1}],
                    "forma_pago": "EFECTIVO",
                    "direccion_entrega": "1234",
                },
            ),
        ):
            with self.subTest(modelo=modelo.__name__, datos=datos):
                with self.assertRaises(ValidationError):
                    modelo.model_validate(datos)
        self.assertEqual(
            ProductoUpdate(nombre="Nueva").model_dump(exclude_unset=True),
            {"nombre": "Nueva"},
        )

    def test_uow_confirma_y_cierra(self):
        sesion = Mock()
        factory = Mock(return_value=sesion)
        uow = UnitOfWork(factory)
        factory.assert_not_called()
        with uow as actual:
            self.assertIs(actual, uow)
        factory.assert_called_once_with()
        self.assertEqual([c[0] for c in sesion.method_calls], ["commit", "close"])

    def test_uow_revierte_y_cierra_ante_error(self):
        sesion = Mock()
        with self.assertRaises(ValueError):
            with UnitOfWork(lambda: sesion):
                raise ValueError("Falla de validación")
        self.assertEqual([c[0] for c in sesion.method_calls], ["rollback", "close"])

    def test_uow_revierte_si_falla_commit(self):
        sesion = Mock()
        sesion.commit.side_effect = RuntimeError("Falla de commit")
        with self.assertRaises(RuntimeError):
            with UnitOfWork(lambda: sesion):
                pass
        self.assertEqual(
            [c[0] for c in sesion.method_calls], ["commit", "rollback", "close"]
        )

    def test_uow_cierra_si_falla_repositorio(self):
        sesion = Mock()
        uow = UnitOfWork(lambda: sesion)
        uow._crear_repositorios = Mock(side_effect=RuntimeError("Falla de repositorio"))
        with self.assertRaises(RuntimeError):
            with uow:
                pass
        sesion.close.assert_called_once_with()

    def test_repositorios_comparten_sesion(self):
        for clase, repositorios in (
            (ProductoUnitOfWork, ["productos", "categorias"]),
            (PedidoUnitOfWork, ["pedidos", "productos"]),
        ):
            sesion = Mock()
            with clase(lambda: sesion) as uow:
                for nombre in repositorios:
                    self.assertIs(getattr(uow, nombre).session, sesion)

    def test_seguridad_reutilizada_sin_base(self):
        hashed = hash_password("Clave1234!")
        self.assertTrue(verify_password("Clave1234!", hashed))
        self.assertFalse(verify_password("incorrecta", hashed))
        self.assertEqual(
            decode_access_token(create_access_token({"sub": "cliente"}))["sub"],
            "cliente",
        )
        self.assertIsNone(decode_access_token("token-invalido"))

    def test_openapi_y_rutas_sin_conexion(self):
        with TestClient(api) as client:
            self.assertEqual(client.get("/docs").status_code, 200)
            respuesta = client.get("/openapi.json")
            self.assertEqual(respuesta.status_code, 200)
            paths = respuesta.json()["paths"]
            self.assertTrue(all(p.startswith("/api/v1/") for p in paths))
            self.assertNotIn("delete", paths["/api/v1/pedidos/{id}"])
            self.assertNotIn("put", paths["/api/v1/pedidos/{id}"])
            self.assertEqual(client.get("/api/v1/auth/me").status_code, 401)
            self.assertEqual(client.post("/api/v1/auth/logout").status_code, 200)


if __name__ == "__main__":
    unittest.main()
