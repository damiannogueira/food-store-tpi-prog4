import { useState } from 'react'
import type { ColumnDef } from '@tanstack/react-table'
import { useAdminPedidos, useCambiarEstado } from '../hooks/useAdminPedidos'
import { useAdminUsers } from '@/features/auth/hooks/useAdminUsers'
import type { EstadoPedido, Pedido } from '../types/pedido'
import { BadgeEstado } from '../components/BadgeEstado'
import { DetallePedido } from '../components/DetallePedido'
import { TablaAdmin } from '@/shared/components/TablaAdmin'
import { ConfirmarAccion } from '@/shared/components/ConfirmarAccion'
import { EstadoError } from '@/shared/components/EstadosLista'
import { mensajeError } from '@/shared/api/request'
import { moneda } from '@/shared/format'

const transiciones: Record<EstadoPedido, EstadoPedido[]> = { PENDIENTE: ['EN_PREPARACION', 'CANCELADO'], EN_PREPARACION: ['ENTREGADO', 'CANCELADO'], ENTREGADO: [], CANCELADO: [] }
const etiquetas: Record<EstadoPedido, string> = { PENDIENTE: 'Pendiente', EN_PREPARACION: 'En preparación', ENTREGADO: 'Entregado', CANCELADO: 'Cancelado' }
export function AdminPedidosPage() {
  const [estado, setEstado] = useState<EstadoPedido | undefined>()
  const [detalle, setDetalle] = useState<number | null>(null)
  const [cancelacion, setCancelacion] = useState<number | null>(null)
  const query = useAdminPedidos(estado)
  const { query: usuarios } = useAdminUsers()
  const cambio = useCambiarEstado()
  const nombres = new Map(usuarios.data?.map((usuario) => [usuario.id, usuario]))
  const columnas: ColumnDef<Pedido>[] = [
    { accessorKey: 'id', header: 'Pedido', cell: ({ row }) => '#' + row.original.id },
    { accessorKey: 'usuario_id', header: 'Usuario', cell: ({ row }) => { const usuario = nombres.get(row.original.usuario_id); return usuario ? <span>{usuario.username}<br />{usuario.full_name}<br />{usuario.email}</span> : 'Usuario #' + row.original.usuario_id } },
    { accessorKey: 'created_at', header: 'Fecha', cell: ({ row }) => new Date(row.original.created_at).toLocaleString('es-AR') },
    { accessorKey: 'estado', header: 'Estado', cell: ({ row }) => <BadgeEstado estado={row.original.estado} /> },
    { accessorKey: 'total', header: 'Total', cell: ({ row }) => moneda(row.original.total) },
    { id: 'acciones', header: 'Acciones', cell: ({ row }) => <div className="flex flex-wrap gap-3"><button type="button" className="underline" onClick={() => setDetalle(detalle === row.original.id ? null : row.original.id)}>Ver detalle #{row.original.id}</button>
      {transiciones[row.original.estado].map((siguiente) => <button type="button" disabled={cambio.isPending} key={siguiente} className="text-blue-700 underline disabled:opacity-40 dark:text-blue-300" onClick={() => { cambio.reset(); if (siguiente === 'CANCELADO') setCancelacion(row.original.id); else cambio.mutate({ id: row.original.id, estado: siguiente }) }}>{siguiente === 'CANCELADO' ? 'Cancelar' : siguiente === 'EN_PREPARACION' ? 'Preparar' : 'Entregar'} #{row.original.id}</button>)}
    </div> },
  ]
  return <main className="mx-auto max-w-6xl p-6"><h1 className="mb-6 text-3xl font-bold">Administrar pedidos</h1>
    <label htmlFor="filtro-estado" className="mr-3">Estado</label><select id="filtro-estado" value={estado ?? ''} onChange={(event) => { setEstado(event.target.value ? event.target.value as EstadoPedido : undefined); setDetalle(null) }} className="mb-6 rounded border bg-white p-2 dark:bg-gray-900"><option value="">Todos</option>{Object.entries(etiquetas).map(([clave, nombre]) => <option key={clave} value={clave}>{nombre}</option>)}</select>
    {query.isPending && <p role="status">Cargando pedidos...</p>}
    {query.isError && <EstadoError error={query.error} reintentar={() => { void query.refetch() }} />}
    {usuarios.isError && <EstadoError error={usuarios.error} reintentar={() => { void usuarios.refetch() }} />}
    {cambio.isError && !cancelacion && <p role="alert" className="text-red-700 dark:text-red-300">{mensajeError(cambio.error)}</p>}
    {query.isSuccess && <TablaAdmin datos={query.data} columnas={columnas} titulo="Pedidos" />}
    {detalle !== null && <section aria-label={'Detalle del pedido #' + detalle} className="mt-6 rounded border p-4"><h2 className="text-xl font-bold">Pedido #{detalle}</h2><DetallePedido id={detalle} /><button type="button" className="mt-3 underline" onClick={() => setDetalle(null)}>Cerrar detalle</button></section>}
    {cancelacion !== null && <ConfirmarAccion titulo="Cancelar pedido" mensaje={'¿Querés cancelar el pedido #' + cancelacion + '? Se restituirá el stock.'} pendiente={cambio.isPending} error={cambio.isError ? mensajeError(cambio.error) : null} confirmar={() => cambio.mutate({ id: cancelacion, estado: 'CANCELADO' }, { onSuccess: () => setCancelacion(null) })} cerrar={() => setCancelacion(null)} />}
  </main>
}
