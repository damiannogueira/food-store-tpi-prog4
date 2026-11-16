import json

from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from app.core.database import create_all_tables, engine
from app.core.security import hash_password
from app.core.unit_of_work import UnitOfWork
from app.modules.categorias.models import Categoria
from app.modules.productos.models import Producto
from app.modules.usuarios.models import Usuario

CATEGORIAS = ("Pizzas", "Empanadas", "Bebidas")
PRODUCTOS = (
    ("Pizza muzzarella", "Pizzas", 8500.0, 20),
    ("Pizza napolitana", "Pizzas", 9500.0, 15),
    ("Pizza fugazzeta", "Pizzas", 10000.0, 12),
    ("Empanada de carne", "Empanadas", 1500.0, 60),
    ("Empanada de pollo", "Empanadas", 1500.0, 50),
    ("Empanada de jamón y queso", "Empanadas", 1600.0, 50),
    ("Agua mineral", "Bebidas", 1800.0, 40),
    ("Gaseosa", "Bebidas", 2500.0, 30),
)


def cargar_seed(db_engine: Engine = engine) -> dict[str, int]:
    with db_engine.begin() as connection:
        create_all_tables(connection)
    creados = {"usuarios": 0, "categorias": 0, "productos": 0}
    with UnitOfWork(lambda: Session(db_engine, expire_on_commit=False)) as uow:
        session = uow.session
        admin = session.exec(select(Usuario).where(Usuario.username == "admin")).first()
        if admin is None:
            session.add(
                Usuario(
                    username="admin",
                    full_name="Administrador",
                    email="admin@foodstore.example",
                    role="admin",
                    hashed_password=hash_password("Admin1234!"),
                )
            )
            creados["usuarios"] += 1
        elif admin.role != "admin" or admin.disabled:
            raise ValueError("El usuario admin existente no es un administrador activo")
        categorias = {}
        for nombre in CATEGORIAS:
            categoria = session.exec(
                select(Categoria).where(Categoria.nombre == nombre)
            ).first()
            if categoria is None:
                categoria = Categoria(nombre=nombre)
                session.add(categoria)
                session.flush()
                creados["categorias"] += 1
            categorias[nombre] = categoria
        for nombre, categoria_nombre, precio, stock in PRODUCTOS:
            categoria = categorias[categoria_nombre]
            existente = session.exec(
                select(Producto).where(
                    Producto.nombre == nombre,
                    Producto.categoria_id == categoria.id,
                )
            ).first()
            if existente is None:
                session.add(
                    Producto(
                        nombre=nombre,
                        categoria_id=categoria.id,
                        precio_base=precio,
                        stock=stock,
                    )
                )
                creados["productos"] += 1
        # Conservo contraseñas, bajas y stock de los registros que ya existen.
    return creados


if __name__ == "__main__":
    print(json.dumps(cargar_seed(), ensure_ascii=False))
