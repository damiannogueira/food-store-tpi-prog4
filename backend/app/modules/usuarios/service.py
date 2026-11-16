from fastapi import HTTPException

from app.modules.usuarios.schemas import UserPublic
from app.modules.usuarios.unit_of_work import UsuarioUnitOfWork


class UsuarioService:
    def __init__(self, uow: UsuarioUnitOfWork):
        self.uow = uow

    def listar(self) -> list[UserPublic]:
        with self.uow as uow:
            return [
                UserPublic.model_validate(usuario) for usuario in uow.usuarios.get_all()
            ]

    def cambiar_estado(
        self, usuario_id: int, disabled: bool, actor_id: int
    ) -> UserPublic | None:
        if disabled and usuario_id == actor_id:
            raise HTTPException(400, "No puedo desactivar mi propia cuenta")
        with self.uow as uow:
            usuario = uow.usuarios.get_by_id(usuario_id)
            if usuario is None:
                return None
            usuario.disabled = disabled
            uow.usuarios.add(usuario)
            return UserPublic.model_validate(usuario)
