from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.deps import get_current_active_user, require_role
from app.modules.pedidos.schemas import (
    CambioEstado,
    EstadoPedido,
    PedidoCreate,
    PedidoRead,
    PedidosPaginados,
    ResumenPedidos,
)
from app.modules.pedidos.service import (
    PedidoAjeno,
    PedidoInvalido,
    PedidoNoEncontrado,
    PedidoService,
    ProductoNoDisponible,
    ProductoNoEncontrado,
    ProductoRepetido,
    StockInsuficiente,
    TransicionInvalida,
)
from app.modules.pedidos.unit_of_work import PedidoUnitOfWork
from app.modules.usuarios.schemas import UserPublic

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


def get_pedido_service() -> PedidoService:
    return PedidoService(PedidoUnitOfWork())


ServiceDep = Annotated[PedidoService, Depends(get_pedido_service)]
UsuarioDep = Annotated[UserPublic, Depends(get_current_active_user)]
Errores = (
    PedidoAjeno,
    PedidoInvalido,
    PedidoNoEncontrado,
    ProductoNoDisponible,
    ProductoNoEncontrado,
    ProductoRepetido,
    StockInsuficiente,
    TransicionInvalida,
)


def _http(error: Exception) -> HTTPException:
    if isinstance(error, (PedidoNoEncontrado, ProductoNoEncontrado)):
        codigo = 404
    elif isinstance(error, PedidoAjeno):
        codigo = 403
    else:
        codigo = 400
    return HTTPException(codigo, str(error))


@router.post("", response_model=PedidoRead, status_code=201)
def crear(datos: PedidoCreate, service: ServiceDep, usuario: UsuarioDep):
    try:
        return service.crear(datos, usuario)
    except Errores as error:
        raise _http(error) from error


@router.get(
    "/resumen",
    response_model=ResumenPedidos,
    dependencies=[Depends(require_role(["admin"]))],
)
def resumen(service: ServiceDep):
    return service.resumen()


@router.get("", response_model=PedidosPaginados)
def listar(
    service: ServiceDep,
    usuario: UsuarioDep,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    estado: EstadoPedido | None = None,
):
    return service.listar(usuario, skip, limit, estado)


@router.get("/{id}", response_model=PedidoRead)
def obtener(id: int, service: ServiceDep, usuario: UsuarioDep):
    try:
        return service.obtener(id, usuario)
    except Errores as error:
        raise _http(error) from error


@router.patch(
    "/{id}/estado",
    response_model=PedidoRead,
    dependencies=[Depends(require_role(["admin"]))],
)
def cambiar_estado(id: int, datos: CambioEstado, service: ServiceDep):
    try:
        return service.cambiar_estado(id, datos.estado)
    except Errores as error:
        raise _http(error) from error


@router.patch("/{id}/cancelar", response_model=PedidoRead)
def cancelar(id: int, service: ServiceDep, usuario: UsuarioDep):
    try:
        return service.cancelar(id, usuario)
    except Errores as error:
        raise _http(error) from error
