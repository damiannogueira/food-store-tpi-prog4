from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

from app.core.deps import require_role
from app.modules.categorias.schemas import (
    CategoriaCreate,
    CategoriaRead,
    CategoriaUpdate,
)
from app.modules.categorias.service import (
    CategoriaInvalida,
    CategoriaNoEncontrada,
    CategoriaService,
    NombreDuplicado,
)
from app.modules.categorias.unit_of_work import CategoriaUnitOfWork

router = APIRouter(prefix="/categorias", tags=["Categoria"])


def get_categoria_service() -> CategoriaService:
    return CategoriaService(CategoriaUnitOfWork())


ServiceDep = Annotated[CategoriaService, Depends(get_categoria_service)]
Errores = (CategoriaNoEncontrada, NombreDuplicado, CategoriaInvalida)


def _http(error: Exception) -> HTTPException:
    codigo = (
        404
        if isinstance(error, CategoriaNoEncontrada)
        else 409
        if isinstance(error, NombreDuplicado)
        else 400
    )
    return HTTPException(codigo, str(error))


@router.get("", response_model=list[CategoriaRead])
def listar(service: ServiceDep):
    return service.listar()


@router.get("/{id}", response_model=CategoriaRead)
def obtener(id: int, service: ServiceDep):
    try:
        return service.obtener(id)
    except Errores as error:
        raise _http(error) from error


@router.post(
    "",
    response_model=CategoriaRead,
    status_code=201,
    dependencies=[Depends(require_role(["admin"]))],
)
def crear(datos: CategoriaCreate, service: ServiceDep):
    try:
        return service.crear(datos)
    except Errores as error:
        raise _http(error) from error


@router.put(
    "/{id}",
    response_model=CategoriaRead,
    dependencies=[Depends(require_role(["admin"]))],
)
def actualizar(id: int, datos: CategoriaUpdate, service: ServiceDep):
    try:
        return service.actualizar(id, datos)
    except Errores as error:
        raise _http(error) from error


@router.delete(
    "/{id}", status_code=204, dependencies=[Depends(require_role(["admin"]))]
)
def eliminar(id: int, service: ServiceDep):
    try:
        service.eliminar(id)
    except Errores as error:
        raise _http(error) from error
    return Response(status_code=204)
