from sqlalchemy.exc import IntegrityError

from app.modules.categorias.models import Categoria
from app.modules.categorias.schemas import (
    CategoriaCreate,
    CategoriaRead,
    CategoriaUpdate,
)
from app.modules.categorias.unit_of_work import CategoriaUnitOfWork


class CategoriaNoEncontrada(Exception):
    pass


class NombreDuplicado(Exception):
    pass


class CategoriaInvalida(Exception):
    pass


def validar_nombre(nombre: str) -> None:
    if not 2 <= len(nombre) <= 100:
        raise CategoriaInvalida("El nombre debe tener entre 2 y 100 caracteres")


class CategoriaService:
    def __init__(self, uow: CategoriaUnitOfWork):
        self.uow = uow

    def listar(self) -> list[CategoriaRead]:
        with self.uow as uow:
            return [
                CategoriaRead.model_validate(c) for c in uow.categorias.list_activas()
            ]

    def obtener(self, id: int) -> CategoriaRead:
        with self.uow as uow:
            categoria = uow.categorias.get_by_id(id)
            if categoria is None or not categoria.activo:
                raise CategoriaNoEncontrada("Categoría no encontrada")
            return CategoriaRead.model_validate(categoria)

    def crear(self, datos: CategoriaCreate) -> CategoriaRead:
        validar_nombre(datos.nombre)
        try:
            with self.uow as uow:
                if uow.categorias.get_by_nombre(datos.nombre):
                    raise NombreDuplicado("El nombre de la categoría ya existe")
                categoria = uow.categorias.add(Categoria.model_validate(datos))
                return CategoriaRead.model_validate(categoria)
        except IntegrityError as error:
            if getattr(error.orig, "pgcode", None) == "23505":
                raise NombreDuplicado("El nombre de la categoría ya existe") from error
            raise

    def actualizar(self, id: int, datos: CategoriaUpdate) -> CategoriaRead:
        cambios = datos.model_dump(exclude_unset=True)
        if datos.nombre is not None:
            validar_nombre(datos.nombre)
        try:
            with self.uow as uow:
                categoria = uow.categorias.get_by_id(id)
                if categoria is None or not categoria.activo:
                    raise CategoriaNoEncontrada("Categoría no encontrada")
                if datos.nombre is not None:
                    existente = uow.categorias.get_by_nombre(datos.nombre)
                    if existente is not None and existente.id != id:
                        raise NombreDuplicado("El nombre de la categoría ya existe")
                categoria.sqlmodel_update(cambios)
                uow.categorias.add(categoria)
                return CategoriaRead.model_validate(categoria)
        except IntegrityError as error:
            if getattr(error.orig, "pgcode", None) == "23505":
                raise NombreDuplicado("El nombre de la categoría ya existe") from error
            raise

    def eliminar(self, id: int) -> None:
        with self.uow as uow:
            categoria = uow.categorias.get_by_id(id)
            if categoria is None or not categoria.activo:
                raise CategoriaNoEncontrada("Categoría no encontrada")
            categoria.activo = False
            uow.categorias.add(categoria)
