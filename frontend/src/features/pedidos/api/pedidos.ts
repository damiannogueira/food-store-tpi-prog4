import { api } from '@/shared/api/request'
import type { Pedido, PedidoCreate, PedidosPaginados, EstadoPedido, ResumenPedidos } from '../types/pedido'

export const crearPedido = (datos: PedidoCreate): Promise<Pedido> => api('/pedidos', { method: 'POST', body: datos })
export const getPedidos = (skip: number, limit: number, estado?: EstadoPedido): Promise<PedidosPaginados> => api('/pedidos', { params: { skip, limit, estado } })
export const getPedido = (id: number): Promise<Pedido> => api(`/pedidos/${id}`)
export const cancelarPedido = (id: number): Promise<Pedido> => api(`/pedidos/${id}/cancelar`, { method: 'PATCH' })

export const cambiarEstado = (id: number, estado: EstadoPedido): Promise<Pedido> => api(`/pedidos/${id}/estado`, { method: 'PATCH', body: { estado } })
export const getResumen = (): Promise<ResumenPedidos> => api('/pedidos/resumen')
