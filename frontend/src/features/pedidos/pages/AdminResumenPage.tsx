import { useResumenPedidos } from '../hooks/useAdminPedidos'
import { EstadoError } from '@/shared/components/EstadosLista'
import { moneda } from '@/shared/format'

export function AdminResumenPage() {
  const query = useResumenPedidos()
  return <main className="mx-auto max-w-6xl p-6"><h1 className="mb-6 text-3xl font-bold">Resumen de pedidos</h1>
    {query.isPending && <p role="status">Cargando resumen...</p>}
    {query.isError && <EstadoError error={query.error} reintentar={() => { void query.refetch() }} />}
    {query.isSuccess && <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{[
      ['Pendientes', query.data.pendientes], ['En preparación', query.data.en_preparacion], ['Entregados', query.data.entregados], ['Cancelados', query.data.cancelados], ['Pedidos hoy', query.data.pedidos_hoy], ['Ingresos entregados', moneda(query.data.ingresos_entregados)],
    ].map(([nombre, valor]) => <article key={nombre} className="rounded-lg border border-gray-200 p-5 dark:border-gray-700"><h2 className="text-lg font-semibold">{nombre}</h2><p className="mt-2 text-2xl font-bold">{valor}</p></article>)}</div>}
  </main>
}
