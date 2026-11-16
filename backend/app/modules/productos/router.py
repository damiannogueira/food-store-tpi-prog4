from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from app.core.deps import require_role
from app.modules.productos.schemas import (
    ProductoCreate,
    ProductoRead,
    ProductosPaginados,
    ProductoStockUpdate,
    ProductoUpdate,
)
from app.modules.productos.service import (
    CategoriaNoEncontrada,
    ProductoInvalido,
    ProductoNoEncontrado,
    ProductoService,
)
from app.modules.productos.unit_of_work import ProductoUnitOfWork

router = APIRouter(prefix="/productos", tags=["Producto"])


def get_producto_service() -> ProductoService:
    return ProductoService(ProductoUnitOfWork())


ServiceDep = Annotated[ProductoService, Depends(get_producto_service)]
Errores = (ProductoNoEncontrado, ProductoInvalido, CategoriaNoEncontrada)


def _http(error: Exception) -> HTTPException:
    codigo = (
        404 if isinstance(error, (ProductoNoEncontrado, CategoriaNoEncontrada)) else 400
    )
    return HTTPException(codigo, str(error))


@router.get("", response_model=ProductosPaginados)
def listar(
    service: ServiceDep,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    categoria_id: int | None = None,
    disponible: bool | None = None,
):
    return service.listar(skip, limit, search, categoria_id, disponible)


@router.get("/{id}", response_model=ProductoRead)
def obtener(id: int, service: ServiceDep):
    try:
        return service.obtener(id)
    except Errores as error:
        raise _http(error) from error


@router.post(
    "",
    response_model=ProductoRead,
    status_code=201,
    dependencies=[Depends(require_role(["admin"]))],
)
def crear(datos: ProductoCreate, service: ServiceDep):
    try:
        return service.crear(datos)
    except Errores as error:
        raise _http(error) from error


@router.put(
    "/{id}",
    response_model=ProductoRead,
    dependencies=[Depends(require_role(["admin"]))],
)
def actualizar(id: int, datos: ProductoUpdate, service: ServiceDep):
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


@router.patch(
    "/{id}/stock",
    response_model=ProductoRead,
    dependencies=[Depends(require_role(["admin"]))],
)
def actualizar_stock(id: int, datos: ProductoStockUpdate, service: ServiceDep):
    try:
        return service.actualizar(id, datos)
    except Errores as error:
        raise _http(error) from error
