# ruff: noqa: E402

import os
import unittest

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "clave-temporal-para-verificar-la-base-del-tpi"

from app.core.security import verify_password
from app.db.seed import cargar_seed
from app.modules.categorias.models import Categoria
from app.modules.productos.models import Producto
from app.modules.usuarios.models import Usuario
from sqlmodel import Session, create_engine, func, select


class SeedTest(unittest.TestCase):
    def test_instalacion_nueva_y_repeticion_sin_sobrescribir(self):
        engine = create_engine("sqlite://")
        self.addCleanup(engine.dispose)
        self.assertEqual(
            cargar_seed(engine), {"usuarios": 1, "categorias": 3, "productos": 8}
        )
        with Session(engine) as session:
            admin = session.exec(select(Usuario)).one()
            self.assertEqual(admin.role, "admin")
            self.assertFalse(admin.disabled)
            self.assertTrue(verify_password("Admin1234!", admin.hashed_password))
            hashed = admin.hashed_password
            producto = session.exec(select(Producto).order_by(Producto.id)).first()
            self.assertGreater(producto.stock, 0)
            producto.stock = 1
            producto.activo = False
            session.commit()
        self.assertEqual(
            cargar_seed(engine), {"usuarios": 0, "categorias": 0, "productos": 0}
        )
        with Session(engine) as session:
            for modelo, cantidad in ((Usuario, 1), (Categoria, 3), (Producto, 8)):
                self.assertEqual(
                    session.exec(select(func.count()).select_from(modelo)).one(),
                    cantidad,
                )
            producto = session.exec(select(Producto).order_by(Producto.id)).first()
            self.assertEqual(producto.stock, 1)
            self.assertFalse(producto.activo)
            self.assertEqual(
                session.exec(select(Usuario)).one().hashed_password, hashed
            )


if __name__ == "__main__":
    unittest.main()
