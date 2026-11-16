from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.core.deps import get_current_active_user
from app.modules.auth.schemas import UserCreate, UserPublic
from app.modules.auth.service import AuthService
from app.modules.usuarios.exceptions import (
    CredencialesInvalidas,
    CuentaDesactivada,
    UsuarioDuplicado,
)
from app.modules.usuarios.unit_of_work import UsuarioUnitOfWork

router = APIRouter(prefix="/auth", tags=["Autenticación"])


def get_auth_service() -> AuthService:
    return AuthService(UsuarioUnitOfWork())


ServiceDep = Annotated[AuthService, Depends(get_auth_service)]


@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
)
def registrar(datos: UserCreate, service: ServiceDep):
    try:
        return service.registrar(datos)
    except UsuarioDuplicado as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.post("/token")
def login(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: ServiceDep,
):
    try:
        token = service.autenticar(
            form_data.username,
            form_data.password,
        )
    except CredencialesInvalidas as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    except CuentaDesactivada as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    # Utilizo una cookie HttpOnly para que JavaScript no pueda leer el JWT.
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    return {"message": "Login exitoso"}


@router.post("/logout")
def logout(response: Response):
    # Elimino la cookie para cerrar la sesión en el navegador.
    response.delete_cookie(
        key="access_token",
        path="/",
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
    )

    return {"mensaje": "Sesión cerrada correctamente"}


@router.get("/me", response_model=UserPublic)
def obtener_usuario_actual(
    usuario: Annotated[UserPublic, Depends(get_current_active_user)],
):
    return usuario
