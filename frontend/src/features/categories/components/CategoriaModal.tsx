import { useForm } from '@tanstack/react-form'
import { useEffect, useRef } from 'react'
import type { Categoria, CategoriaDatos } from '@/features/categories/types/categoria'

interface CategoriaModalProps {
  categoria: Categoria | null
  pendiente: boolean
  error: string | null
  onGuardar: (datos: CategoriaDatos) => void
  onCancelar: () => void
}

export function CategoriaModal({ categoria, pendiente, error, onGuardar, onCancelar }: CategoriaModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  useEffect(() => { dialogRef.current?.showModal() }, [])
  const form = useForm({
    defaultValues: { nombre: categoria?.nombre ?? '', descripcion: categoria?.descripcion ?? '' },
    onSubmit: ({ value }) => {
      if (!pendiente) onGuardar({ nombre: value.nombre.trim(), descripcion: value.descripcion })
    },
  })

  return (
    <dialog ref={dialogRef} aria-labelledby="category-title" onCancel={(event) => { event.preventDefault(); if (!pendiente) onCancelar() }} className="fixed inset-0 m-auto max-h-[90dvh] w-[calc(100%-2rem)] max-w-md overflow-y-auto rounded-lg bg-white p-6 shadow-lg backdrop:bg-black/50 dark:bg-gray-900">
      <h2 id="category-title" className="text-2xl font-bold text-blue-900 dark:text-blue-200">{categoria ? 'Editar categoría' : 'Nueva categoría'}</h2>
      <form className="mt-6 space-y-4" onSubmit={(event) => { event.preventDefault(); void form.handleSubmit() }}>
        <fieldset disabled={pendiente} className="space-y-4 disabled:opacity-60">
          <form.Field name="nombre" validators={{ onChange: ({ value }) => value.trim().length >= 2 && value.trim().length <= 100 ? undefined : 'El nombre debe tener entre 2 y 100 caracteres.' }}>
            {(field) => (
              <div>
                <label htmlFor="nombre" className="mb-1 block font-medium">Nombre</label>
                <input autoFocus id="nombre" required minLength={2} maxLength={100} value={field.state.value} onBlur={field.handleBlur} onChange={(event) => field.handleChange(event.target.value)} aria-invalid={field.state.meta.errors.length > 0} aria-describedby="nombre-error" className="w-full rounded-md border border-gray-300 px-3 py-2 dark:border-gray-600" />
                <p id="nombre-error" className="mt-1 text-sm text-red-700 dark:text-red-300">{field.state.meta.errors.join(' ')}</p>
              </div>
            )}
          </form.Field>
          <form.Field name="descripcion">
            {(field) => (
              <div>
                <label htmlFor="descripcion" className="mb-1 block font-medium">Descripción (opcional)</label>
                <textarea id="descripcion" rows={4} value={field.state.value} onBlur={field.handleBlur} onChange={(event) => field.handleChange(event.target.value)} className="w-full rounded-md border border-gray-300 px-3 py-2 dark:border-gray-600" />
              </div>
            )}
          </form.Field>
        </fieldset>
        {error && <p role="alert" className="text-red-700 dark:text-red-300">{error}</p>}
        <div className="flex justify-end gap-3">
          <button type="button" disabled={pendiente} onClick={onCancelar} className="rounded-md bg-gray-200 px-4 py-2 disabled:opacity-50 dark:bg-gray-700">Cancelar</button>
          <button type="submit" disabled={pendiente} className="rounded-md bg-blue-700 px-4 py-2 text-white disabled:opacity-50">{pendiente ? 'Guardando...' : 'Guardar'}</button>
        </div>
      </form>
    </dialog>
  )
}
