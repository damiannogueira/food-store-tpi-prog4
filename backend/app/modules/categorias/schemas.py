from pydantic import ConfigDict, field_validator
from sqlmodel import Field, SQLModel


class CategoriaCreate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(min_length=2, max_length=100)
    descripcion: str | None = None


class CategoriaUpdate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = Field(default=None, min_length=2, max_length=100)
    descripcion: str | None = None

    @field_validator("nombre")
    @classmethod
    def nombre_no_nulo(cls, valor: str | None) -> str:
        if valor is None:
            raise ValueError("El nombre no puede ser nulo")
        return valor


class CategoriaRead(SQLModel):
    id: int
    nombre: str
    descripcion: str | None
    activo: bool
