import { useState } from 'react'
import { useCancelarPedido, usePedidos } from '../hooks/usePedidos'
import { BadgeEstado } from '../components/BadgeEstado'
import { DetallePedido } from '../components/DetallePedido'
import { EstadoError, EstadoVacio, Paginacion } from '@/shared/components/EstadosLista'
import { mensajeError } from '@/shared/api/request'
import { moneda } from '@/shared/format'

const limite = 10

export function MisPedidosPage() {
  const [pagina, setPagina] = useState(0)
  const [abierto, setAbierto] = useState<number | null>(null)
  const pedidos = usePedidos(pagina, limite)
  const cancelar = useCancelarPedido()

  return <main className="mx-auto max-w-4xl px-6 py-8">
    <h1 className="mb-6 text-3xl font-bold">Mis pedidos</h1>
    {pedidos.isPending && <p role="status">Cargando pedidos...</p>}
    {pedidos.isError && <EstadoError error={pedidos.error} reintentar={() => { void pedidos.refetch() }} />}
    {cancelar.isError && <p role="alert" className="mb-4 text-red-700 dark:text-red-300">{mensajeError(cancelar.error)}</p>}
    {pedidos.isSuccess && <>
      {pedidos.data.items.length === 0 && <EstadoVacio mensaje="Todavía no hay pedidos para mostrar." />}
      <div className="space-y-4">{pedidos.data.items.map((pedido) => <article key={pedido.id} className="rounded-lg border border-gray-200 p-5 dark:border-gray-700">
        <div className="flex flex-wrap items-center justify-between gap-3"><h2 className="text-xl font-semibold">Pedido #{pedido.id}</h2><BadgeEstado estado={pedido.estado} /></div>
        <p className="mt-3">{new Date(pedido.created_at).toLocaleString('es-AR')}</p>
        <p className="my-3 font-semibold">Total: {moneda(pedido.total)}</p>
        <div className="flex flex-wrap gap-4">
          <button type="button" aria-expanded={abierto === pedido.id} aria-controls={`detalle-${pedido.id}`} className="text-blue-700 underline dark:text-blue-300" onClick={() => setAbierto(abierto === pedido.id ? null : pedido.id)}>{abierto === pedido.id ? 'Ocultar detalle' : 'Ver detalle'}</button>
          {pedido.estado === 'PENDIENTE' && <button type="button" disabled={cancelar.isPending} className="text-red-700 underline disabled:opacity-40 dark:text-red-300" onClick={() => cancelar.mutate(pedido.id)}>Cancelar pedido #{pedido.id}</button>}
        </div>
        {abierto === pedido.id && <div id={`detalle-${pedido.id}`}><DetallePedido id={pedido.id} /></div>}
      </article>)}</div>
      <Paginacion pagina={pagina} total={pedidos.data.total} limite={limite} cambiar={setPagina} />
    </>}
  </main>
}
