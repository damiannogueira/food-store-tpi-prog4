import { mensajeError } from '@/shared/api/request'

export function EstadoVacio({ mensaje }: { mensaje: string }) {
  return <p role="status" className="rounded-lg border border-gray-200 p-6 dark:border-gray-700">{mensaje}</p>
}

export function EstadoError({ error, reintentar }: { error: unknown; reintentar: () => void }) {
  return <div role="alert" className="rounded-lg border border-red-300 p-4 text-red-700 dark:text-red-300">
    <p>{mensajeError(error)}</p>
    <button type="button" className="mt-2 underline" onClick={reintentar}>Reintentar</button>
  </div>
}

export function Skeleton() {
  return <div role="status" aria-label="Cargando productos" className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
    {Array.from({ length: 6 }, (_, i) => <div key={i} aria-hidden="true" className="h-60 animate-pulse rounded-lg bg-gray-100 dark:bg-gray-800" />)}
    <span className="sr-only">Cargando productos...</span>
  </div>
}

export function Paginacion({ pagina, total, limite, cambiar }: { pagina: number; total: number; limite: number; cambiar: (pagina: number) => void }) {
  const paginas = Math.max(1, Math.ceil(total / limite))
  return <nav aria-label="Paginación" className="mt-6 flex items-center justify-center gap-4">
    <button type="button" disabled={pagina === 0} onClick={() => cambiar(pagina - 1)} className="rounded border px-3 py-2 disabled:opacity-40">Anterior</button>
    <span>Página {pagina + 1} de {paginas}</span>
    <button type="button" disabled={pagina + 1 >= paginas} onClick={() => cambiar(pagina + 1)} className="rounded border px-3 py-2 disabled:opacity-40">Siguiente</button>
  </nav>
}
