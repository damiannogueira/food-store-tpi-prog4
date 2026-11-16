import { useEffect, useRef } from 'react'
import { useForm } from '@tanstack/react-form'
import type { Producto, ProductoDatos } from '../types/producto'
import type { Categoria } from '@/features/categories/types/categoria'

export function ProductoModal({ producto, categorias, pendiente, error, guardar, cerrar }: { producto: Producto | null; categorias: Categoria[]; pendiente: boolean; error: string | null; guardar: (datos: ProductoDatos) => void; cerrar: () => void }) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => { ref.current?.showModal() }, [])
  const form = useForm({
    defaultValues: { nombre: producto?.nombre ?? '', descripcion: producto?.descripcion ?? '', precio_base: producto?.precio_base ?? 0, imagen_url: producto?.imagen_url ?? '', categoria_id: producto?.categoria_id ?? 0, stock: producto?.stock ?? 0, disponible: producto?.disponible ?? true },
    onSubmit: ({ value }) => { if (!pendiente) guardar({ ...value, nombre: value.nombre.trim(), descripcion: value.descripcion || null, imagen_url: value.imagen_url || null }) },
  })
  const opciones = producto && !categorias.some((c) => c.id === producto.categoria_id) ? [...categorias, producto.categoria] : categorias
  return <dialog ref={ref} aria-labelledby="producto-titulo" onCancel={(e) => { e.preventDefault(); if (!pendiente) cerrar() }} className="fixed inset-0 m-auto max-h-[90dvh] w-[calc(100%-2rem)] max-w-xl overflow-y-auto rounded-lg bg-white p-6 shadow-lg backdrop:bg-black/50 dark:bg-gray-900">
    <h2 id="producto-titulo" className="mb-4 text-2xl font-bold">{producto ? 'Editar producto' : 'Nuevo producto'}</h2>
    <form onSubmit={(e) => { e.preventDefault(); void form.handleSubmit() }} className="space-y-4"><fieldset disabled={pendiente} className="space-y-4">
      <form.Field name="nombre" validators={{ onChange: ({ value }) => value.trim() ? undefined : 'El nombre es obligatorio.' }}>{(f) => <div><label htmlFor="producto-nombre">Nombre</label><input autoFocus id="producto-nombre" required value={f.state.value} onBlur={f.handleBlur} onChange={(e) => f.handleChange(e.target.value)} className="block w-full rounded border p-2" /><p className="text-red-700">{f.state.meta.errors.join(' ')}</p></div>}</form.Field>
      <form.Field name="descripcion">{(f) => <div><label htmlFor="producto-descripcion">Descripción</label><textarea id="producto-descripcion" value={f.state.value} onChange={(e) => f.handleChange(e.target.value)} className="block w-full rounded border p-2" /></div>}</form.Field>
      <form.Field name="precio_base" validators={{ onChange: ({ value }) => Number.isFinite(value) && value >= 0 ? undefined : 'El precio debe ser mayor o igual a cero.' }}>{(f) => <div><label htmlFor="producto-precio">Precio base</label><input id="producto-precio" required type="number" min="0" step="any" value={Number.isNaN(f.state.value) ? '' : f.state.value} onChange={(e) => f.handleChange(e.target.valueAsNumber)} className="block w-full rounded border p-2" /><p className="text-red-700">{f.state.meta.errors.join(' ')}</p></div>}</form.Field>
      <form.Field name="imagen_url">{(f) => <div><label htmlFor="producto-imagen">URL de imagen (opcional)</label><input id="producto-imagen" type="url" value={f.state.value} onChange={(e) => f.handleChange(e.target.value)} className="block w-full rounded border p-2" /></div>}</form.Field>
      <form.Field name="categoria_id" validators={{ onChange: ({ value }) => value > 0 ? undefined : 'Seleccioná una categoría.' }}>{(f) => <div><label htmlFor="producto-categoria">Categoría</label><select id="producto-categoria" required value={f.state.value || ''} onChange={(e) => f.handleChange(Number(e.target.value))} className="block w-full rounded border bg-white p-2 dark:bg-gray-900"><option value="">Seleccionar categoría</option>{opciones.map((c) => <option key={c.id} value={c.id}>{c.nombre}{!c.activo ? ' (inactiva)' : ''}</option>)}</select><p className="text-red-700">{f.state.meta.errors.join(' ')}</p></div>}</form.Field>
      {!producto && <><form.Field name="stock" validators={{ onChange: ({ value }) => Number.isSafeInteger(value) && value >= 0 ? undefined : 'El stock debe ser un entero mayor o igual a cero.' }}>{(f) => <div><label htmlFor="producto-stock">Stock inicial</label><input id="producto-stock" type="number" required min="0" step="1" value={Number.isNaN(f.state.value) ? '' : f.state.value} onChange={(e) => f.handleChange(e.target.valueAsNumber)} className="block w-full rounded border p-2" /><p className="text-red-700">{f.state.meta.errors.join(' ')}</p></div>}</form.Field>
      <form.Field name="disponible">{(f) => <label className="flex gap-2"><input type="checkbox" checked={f.state.value} onChange={(e) => f.handleChange(e.target.checked)} />Disponible</label>}</form.Field></>}
    </fieldset>{error && <p role="alert" className="text-red-700 dark:text-red-300">{error}</p>}
    <div className="flex justify-end gap-3"><button type="button" disabled={pendiente} onClick={cerrar} className="rounded border p-2">Cancelar</button><button type="submit" disabled={pendiente} className="rounded bg-blue-700 p-2 text-white">{pendiente ? 'Guardando...' : 'Guardar'}</button></div></form>
  </dialog>
}
