import { useEffect, useRef } from 'react'

export function ConfirmarAccion({ titulo, mensaje, pendiente, error, confirmar, cerrar }: { titulo: string; mensaje: string; pendiente: boolean; error: string | null; confirmar: () => void; cerrar: () => void }) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => { ref.current?.showModal() }, [])
  return <dialog ref={ref} aria-labelledby="confirmar-titulo" onCancel={(event) => { event.preventDefault(); if (!pendiente) cerrar() }} className="fixed inset-0 m-auto w-[calc(100%-2rem)] max-w-md rounded-lg bg-white p-6 shadow-lg backdrop:bg-black/50 dark:bg-gray-900">
    <h2 id="confirmar-titulo" className="text-xl font-bold">{titulo}</h2><p className="my-4">{mensaje}</p>
    {error && <p role="alert" className="text-red-700 dark:text-red-300">{error}</p>}
    <div className="mt-4 flex justify-end gap-3"><button autoFocus type="button" disabled={pendiente} onClick={cerrar} className="rounded border px-3 py-2">Volver</button><button type="button" disabled={pendiente} onClick={confirmar} className="rounded bg-red-700 px-3 py-2 text-white disabled:opacity-40">{pendiente ? 'Procesando...' : 'Confirmar'}</button></div>
  </dialog>
}
