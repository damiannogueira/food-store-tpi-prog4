from datetime import datetime

from sqlmodel import Session, col, func, select

from app.core.base_repository import BaseRepository
from app.modules.pedidos.models import Pedido


class PedidoRepository(BaseRepository[Pedido]):
    def __init__(self, session: Session):
        super().__init__(session, Pedido)

    def get_by_id_for_update(self, pedido_id: int) -> Pedido | None:
        consulta = (
            select(Pedido)
            .where(Pedido.id == pedido_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        return self.session.exec(consulta).first()

    def list_by_usuario(
        self,
        usuario_id: int | None,
        skip: int,
        limit: int,
        estado: str | None = None,
    ) -> tuple[int, list[Pedido]]:
        consulta = select(Pedido)
        if usuario_id is not None:
            consulta = consulta.where(Pedido.usuario_id == usuario_id)
        if estado is not None:
            consulta = consulta.where(Pedido.estado == estado)
        total = self.session.exec(
            select(func.count()).select_from(consulta.subquery())
        ).one()
        items = self.session.exec(
            consulta.order_by(col(Pedido.id).desc()).offset(skip).limit(limit)
        ).all()
        return total, list(items)

    def count_by_estado(self, estado: str) -> int:
        return self.session.exec(
            select(func.count()).select_from(Pedido).where(Pedido.estado == estado)
        ).one()

    def count_created_between(self, desde: datetime, hasta: datetime) -> int:
        consulta = (
            select(func.count())
            .select_from(Pedido)
            .where(
                Pedido.created_at >= desde,
                Pedido.created_at < hasta,
            )
        )
        return self.session.exec(consulta).one()

    def sum_total_by_estado(self, estado: str) -> float:
        consulta = select(func.coalesce(func.sum(Pedido.total), 0.0)).where(
            Pedido.estado == estado,
        )
        return float(self.session.exec(consulta).one())
