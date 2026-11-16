import { useRef, useEffect } from 'react'
import { useForm } from '@tanstack/react-form'
import type { Producto } from '../types/producto'
export function StockModal({ producto, pendiente, error, guardar, cerrar }: { producto: Producto; pendiente: boolean; error: string | null; guardar: (stock: number, disponible: boolean) => void; cerrar: () => void }) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => { ref.current?.showModal() }, [])
  const form = useForm({ defaultValues: { stock: producto.stock, disponible: producto.disponible }, onSubmit: ({ value }) => { if (!pendiente) guardar(value.stock, value.disponible) } })
  return <dialog ref={ref} aria-labelledby="stock-titulo" onCancel={(e) => { e.preventDefault(); if (!pendiente) cerrar() }} className="fixed inset-0 m-auto w-[calc(100%-2rem)] max-w-md rounded-lg bg-white p-6 shadow-lg backdrop:bg-black/50 dark:bg-gray-900"><h2 id="stock-titulo" className="text-xl font-bold">Stock y disponibilidad</h2><p>{producto.nombre}</p><form className="mt-4 space-y-4" onSubmit={(e) => { e.preventDefault(); void form.handleSubmit() }}><fieldset disabled={pendiente} className="space-y-4">
    <form.Field name="stock" validators={{ onChange: ({ value }) => Number.isSafeInteger(value) && value >= 0 ? undefined : 'Ingresá un entero mayor o igual a cero.' }}>{(f) => <div><label htmlFor="stock-valor">Stock</label><input id="stock-valor" required type="number" min="0" step="1" value={Number.isNaN(f.state.value) ? '' : f.state.value} onChange={(e) => f.handleChange(e.target.valueAsNumber)} className="block w-full rounded border p-2" /><p className="text-red-700">{f.state.meta.errors.join(' ')}</p></div>}</form.Field>
    <form.Field name="disponible">{(f) => <label className="flex gap-2"><input type="checkbox" checked={f.state.value} onChange={(e) => f.handleChange(e.target.checked)} />Disponible</label>}</form.Field></fieldset>
    {error && <p role="alert" className="text-red-700 dark:text-red-300">{error}</p>}<div className="flex justify-end gap-3"><button type="button" disabled={pendiente} onClick={cerrar} className="rounded border p-2">Cancelar</button><button type="submit" disabled={pendiente} className="rounded bg-blue-700 p-2 text-white">Guardar</button></div>
  </form></dialog>
}
