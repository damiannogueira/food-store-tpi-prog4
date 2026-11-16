from collections.abc import Callable
from types import TracebackType
from typing import Self

from sqlmodel import Session

from app.core.database import session_factory


class UnitOfWork:
    def __init__(self, factory: Callable[[], Session] = session_factory):
        self.session_factory = factory
        self.session: Session

    def __enter__(self) -> Self:
        self.session = self.session_factory()
        try:
            self._crear_repositorios()
        except Exception:
            self.session.close()
            raise
        return self

    def _crear_repositorios(self) -> None:
        pass

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            # Confirmo los cambios solo si la operación terminó sin errores.
            if exc_type is None:
                self.session.commit()
            else:
                self.session.rollback()
        except Exception:
            self.session.rollback()
            raise
        finally:
            self.session.close()
