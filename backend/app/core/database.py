from sqlalchemy.engine import Connection
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, echo=False, hide_parameters=True)


def register_models() -> None:
    from app.modules.categorias import models as categorias
    from app.modules.pedidos import models as pedidos
    from app.modules.productos import models as productos
    from app.modules.usuarios import models as usuarios

    # Registro solo las cinco tablas del UML.
    _ = categorias, pedidos, productos, usuarios


def create_all_tables(connection: Connection | None = None) -> None:
    register_models()
    SQLModel.metadata.create_all(connection if connection is not None else engine)


def session_factory() -> Session:
    return Session(engine, expire_on_commit=False)
