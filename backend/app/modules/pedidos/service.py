from datetime import timedelta

from app.modules.pedidos.models import DetallePedido, Pedido, ahora_utc
from app.modules.pedidos.schemas import (
    PedidoCreate,
    PedidoRead,
    PedidosPaginados,
    ResumenPedidos,
)
from app.modules.pedidos.unit_of_work import PedidoUnitOfWork
from app.modules.usuarios.schemas import UserPublic


class PedidoNoEncontrado(Exception):
    pass


class PedidoAjeno(Exception):
    pass


class ProductoNoEncontrado(Exception):
    pass


class ProductoNoDisponible(Exception):
    pass


class StockInsuficiente(Exception):
    pass


class ProductoRepetido(Exception):
    pass


class PedidoInvalido(Exception):
    pass


class TransicionInvalida(Exception):
    pass


class PedidoService:
    TRANSICIONES = {
        "PENDIENTE": {"EN_PREPARACION", "CANCELADO"},
        "EN_PREPARACION": {"ENTREGADO", "CANCELADO"},
        "ENTREGADO": set(),
        "CANCELADO": set(),
    }

    def __init__(self, uow: PedidoUnitOfWork):
        self.uow = uow

    def crear(self, datos: PedidoCreate, usuario: UserPublic) -> PedidoRead:
        with self.uow as uow:
            if not datos.items:
                raise PedidoInvalido("El pedido debe contener al menos un ítem")
            ids = [item.producto_id for item in datos.items]
            if len(ids) != len(set(ids)):
                raise ProductoRepetido("Un producto no puede repetirse en el pedido")
            pedido = Pedido(
                usuario_id=usuario.id,
                estado="PENDIENTE",
                forma_pago=datos.forma_pago,
                direccion_entrega=datos.direccion_entrega,
                notas=datos.notas,
                total=0.0,
                items=[],
            )
            uow.pedidos.add(pedido)
            # Bloqueo los productos en el mismo orden para evitar interbloqueos.
            for item in sorted(datos.items, key=lambda item: item.producto_id):
                producto = uow.productos.get_by_id_for_update(item.producto_id)
                if producto is None or not producto.activo:
                    raise ProductoNoEncontrado("Producto no encontrado")
                if not producto.disponible:
                    raise ProductoNoDisponible("El producto no está disponible")
                if item.cantidad < 1:
                    raise PedidoInvalido("La cantidad debe ser mayor o igual a uno")
                if producto.stock < item.cantidad:
                    raise StockInsuficiente("Stock insuficiente")
                producto.stock -= item.cantidad
                subtotal = producto.precio_base * item.cantidad
                pedido.items.append(
                    DetallePedido(
                        pedido_id=pedido.id,
                        producto_id=producto.id,
                        cantidad=item.cantidad,
                        nombre_producto=producto.nombre,
                        precio_unitario=producto.precio_base,
                        subtotal=subtotal,
                    )
                )
                pedido.total += subtotal
                uow.pedidos.add(pedido)
            return PedidoRead.model_validate(pedido)

    def cambiar_estado(self, id: int, estado: str) -> PedidoRead:
        with self.uow as uow:
            pedido = uow.pedidos.get_by_id_for_update(id)
            if pedido is None:
                raise PedidoNoEncontrado("Pedido no encontrado")
            self._aplicar_transicion(pedido, estado, uow)
            return PedidoRead.model_validate(pedido)

    def cancelar(self, id: int, usuario: UserPublic) -> PedidoRead:
        with self.uow as uow:
            pedido = uow.pedidos.get_by_id_for_update(id)
            if pedido is None:
                raise PedidoNoEncontrado("Pedido no encontrado")
            if pedido.usuario_id != usuario.id:
                raise PedidoAjeno("El pedido pertenece a otro usuario")
            if pedido.estado != "PENDIENTE":
                raise TransicionInvalida("Solo puedo cancelar pedidos pendientes")
            self._aplicar_transicion(pedido, "CANCELADO", uow)
            return PedidoRead.model_validate(pedido)

    def _aplicar_transicion(
        self,
        pedido: Pedido,
        destino: str,
        uow: PedidoUnitOfWork,
    ) -> None:
        if destino not in self.TRANSICIONES.get(pedido.estado, set()):
            raise TransicionInvalida("Transición de estado inválida")
        if destino == "CANCELADO":
            for item in sorted(pedido.items, key=lambda item: item.producto_id):
                producto = uow.productos.get_by_id_for_update(item.producto_id)
                if producto is None:
                    raise ProductoNoEncontrado("Producto no encontrado")
                # Restituyo también el stock de productos dados de baja.
                producto.stock += item.cantidad
                uow.productos.add(producto)
        pedido.estado = destino
        pedido.updated_at = ahora_utc()
        uow.pedidos.add(pedido)

    def resumen(self) -> ResumenPedidos:
        with self.uow as uow:
            # Uso el día UTC, igual que las fechas que genero para los pedidos.
            desde = ahora_utc().replace(hour=0, minute=0, second=0, microsecond=0)
            hasta = desde + timedelta(days=1)
            return ResumenPedidos(
                pendientes=uow.pedidos.count_by_estado("PENDIENTE"),
                en_preparacion=uow.pedidos.count_by_estado("EN_PREPARACION"),
                entregados=uow.pedidos.count_by_estado("ENTREGADO"),
                cancelados=uow.pedidos.count_by_estado("CANCELADO"),
                pedidos_hoy=uow.pedidos.count_created_between(desde, hasta),
                ingresos_entregados=uow.pedidos.sum_total_by_estado("ENTREGADO"),
            )

    def listar(
        self,
        usuario: UserPublic,
        skip: int,
        limit: int,
        estado: str | None,
    ) -> PedidosPaginados:
        with self.uow as uow:
            usuario_id = None if usuario.role == "admin" else usuario.id
            total, items = uow.pedidos.list_by_usuario(usuario_id, skip, limit, estado)
            return PedidosPaginados(
                total=total,
                items=[PedidoRead.model_validate(p) for p in items],
            )

    def obtener(self, id: int, usuario: UserPublic) -> PedidoRead:
        with self.uow as uow:
            pedido = uow.pedidos.get_by_id(id)
            if pedido is None:
                raise PedidoNoEncontrado("Pedido no encontrado")
            if usuario.role != "admin" and pedido.usuario_id != usuario.id:
                raise PedidoAjeno("El pedido pertenece a otro usuario")
            return PedidoRead.model_validate(pedido)
