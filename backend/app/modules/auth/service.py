from sqlalchemy.exc import IntegrityError

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.modules.usuarios.exceptions import (
    CredencialesInvalidas,
    CuentaDesactivada,
    UsuarioDuplicado,
)
from app.modules.usuarios.models import Usuario
from app.modules.usuarios.schemas import UserCreate, UserPublic
from app.modules.usuarios.unit_of_work import UsuarioUnitOfWork


class AuthService:
    def __init__(self, uow: UsuarioUnitOfWork):
        self.uow = uow

    def registrar(self, datos: UserCreate) -> UserPublic:
        try:
            with self.uow as uow:
                if uow.usuarios.get_by_username(datos.username):
                    raise UsuarioDuplicado("El nombre de usuario ya está registrado")

                if uow.usuarios.get_by_email(str(datos.email)):
                    raise UsuarioDuplicado("El correo electrónico ya está registrado")

                # Asigno siempre el rol user en el registro público.
                usuario = Usuario(
                    username=datos.username,
                    full_name=datos.full_name,
                    email=str(datos.email),
                    hashed_password=hash_password(datos.password),
                    role="user",
                    disabled=False,
                )

                uow.usuarios.add(usuario)
                return UserPublic.model_validate(usuario)

        except IntegrityError as error:
            if getattr(error.orig, "pgcode", None) == "23505":
                raise UsuarioDuplicado(
                    "El nombre de usuario o el correo electrónico ya está registrado"
                ) from error
            raise

    def autenticar(self, username: str, password: str) -> str:
        with self.uow as uow:
            usuario = uow.usuarios.get_by_username(username)

            if len(password.encode("utf-8")) > 72:
                raise CredencialesInvalidas("Credenciales incorrectas")

            if usuario is None or not verify_password(
                password, usuario.hashed_password
            ):
                raise CredencialesInvalidas("Credenciales incorrectas")

            if usuario.disabled:
                raise CuentaDesactivada("Cuenta de usuario desactivada")

            return create_access_token({"sub": usuario.username, "role": usuario.role})
