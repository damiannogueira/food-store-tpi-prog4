import { useDetallePedido } from '../hooks/usePedidos'
import { EstadoError } from '@/shared/components/EstadosLista'
import { moneda } from '@/shared/format'

export function DetallePedido({ id }: { id: number }) {
  const pedido = useDetallePedido(id)
  if (pedido.isPending) return <p role="status">Cargando detalle...</p>
  if (pedido.isError) return <EstadoError error={pedido.error} reintentar={() => { void pedido.refetch() }} />
  return <div className="mt-4 border-t border-gray-200 pt-4 dark:border-gray-700">
    <p>Dirección: {pedido.data.direccion_entrega}</p>
    <p>Forma de pago: {pedido.data.forma_pago}</p>
    {pedido.data.notas && <p>Notas: {pedido.data.notas}</p>}
    <ul className="my-3 space-y-2">{pedido.data.items.map((item) => <li key={item.producto_id}>
      {item.nombre_producto} — {item.cantidad} × {moneda(item.precio_unitario)} = {moneda(item.subtotal)}
    </li>)}</ul>
    <p className="font-bold">Total: {moneda(pedido.data.total)}</p>
  </div>
}
