from sqlmodel import Session, col, func, select

from app.core.base_repository import BaseRepository
from app.modules.productos.models import Producto


class ProductoRepository(BaseRepository[Producto]):
    def __init__(self, session: Session):
        super().__init__(session, Producto)

    def get_by_id_for_update(self, producto_id: int) -> Producto | None:
        consulta = (
            select(Producto)
            .where(Producto.id == producto_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        return self.session.exec(consulta).first()

    def search(
        self,
        skip: int,
        limit: int,
        search: str | None = None,
        categoria_id: int | None = None,
        disponible: bool | None = None,
    ) -> tuple[int, list[Producto]]:
        consulta = select(Producto).where(Producto.activo)
        if search:
            consulta = consulta.where(col(Producto.nombre).ilike(f"%{search}%"))
        if categoria_id is not None:
            consulta = consulta.where(Producto.categoria_id == categoria_id)
        if disponible is not None:
            consulta = consulta.where(Producto.disponible == disponible)
        total = self.session.exec(
            select(func.count()).select_from(consulta.subquery())
        ).one()
        items = self.session.exec(
            consulta.order_by(col(Producto.id)).offset(skip).limit(limit)
        ).all()
        return total, list(items)

    def refresh_categoria(self, producto: Producto) -> None:
        # Vuelvo a cargar la relación si cambié la categoría.
        self.session.expire(producto, ["categoria"])
