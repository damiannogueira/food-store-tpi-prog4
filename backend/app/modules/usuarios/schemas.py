from datetime import datetime

from pydantic import ConfigDict, EmailStr, Field, field_validator
from sqlmodel import SQLModel


class UserCreate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=50)
    full_name: str = Field(min_length=1, max_length=160)
    email: EmailStr = Field(max_length=254)
    password: str = Field(min_length=8, max_length=72)

    @field_validator("username", "full_name", mode="before")
    @classmethod
    def limpiar_textos(cls, valor: object) -> object:
        return valor.strip() if isinstance(valor, str) else valor

    @field_validator("password")
    @classmethod
    def validar_longitud_password(cls, password: str) -> str:
        # Verifico también los bytes porque bcrypt admite hasta 72.
        if len(password.encode("utf-8")) > 72:
            raise ValueError("La contraseña no puede superar los 72 bytes")
        return password


class UserPublic(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    email: str
    role: str
    disabled: bool

    created_at: datetime
