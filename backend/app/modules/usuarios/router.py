from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import require_role
from app.modules.usuarios.schemas import UserPublic
from app.modules.usuarios.service import UsuarioService
from app.modules.usuarios.unit_of_work import UsuarioUnitOfWork

router = APIRouter(prefix="/admin/usuarios", tags=["Usuarios"])


def get_usuario_service() -> UsuarioService:
    return UsuarioService(UsuarioUnitOfWork())


ServiceDep = Annotated[UsuarioService, Depends(get_usuario_service)]
AdminDep = Annotated[UserPublic, Depends(require_role(["admin"]))]


@router.get("", response_model=list[UserPublic])
def listar_usuarios(service: ServiceDep, admin: AdminDep):
    return service.listar()


def _cambiar_estado(
    id: int, disabled: bool, service: UsuarioService, admin: UserPublic
):
    usuario = service.cambiar_estado(id, disabled, admin.id)
    if usuario is None:
        raise HTTPException(404, "Usuario no encontrado")
    return usuario


@router.post("/{id}/activar", response_model=UserPublic)
def activar_usuario(id: int, service: ServiceDep, admin: AdminDep):
    return _cambiar_estado(id, False, service, admin)


@router.post("/{id}/desactivar", response_model=UserPublic)
def desactivar_usuario(id: int, service: ServiceDep, admin: AdminDep):
    return _cambiar_estado(id, True, service, admin)
