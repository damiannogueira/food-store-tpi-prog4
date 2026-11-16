import type { EstadoPedido } from '../types/pedido'

const clases: Record<EstadoPedido, string> = {
  PENDIENTE: 'bg-yellow-100 text-yellow-900',
  EN_PREPARACION: 'bg-blue-100 text-blue-900',
  ENTREGADO: 'bg-green-100 text-green-900',
  CANCELADO: 'bg-red-100 text-red-900',
}

export function BadgeEstado({ estado }: { estado: EstadoPedido }) {
  return <span className={`rounded-full px-3 py-1 text-sm font-medium ${clases[estado]}`}>{estado.replaceAll('_', ' ')}</span>
}
