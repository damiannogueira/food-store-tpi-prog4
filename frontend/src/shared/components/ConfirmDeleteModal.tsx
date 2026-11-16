import { useEffect, useRef } from 'react'

interface ConfirmDeleteModalProps {
  categoria?: { nombre: string }
  elemento?: { nombre: string; entidad: 'producto' }
  pendiente: boolean
  error: string | null
  onConfirmar: () => void
  onCancelar: () => void
}

export function ConfirmDeleteModal({ categoria, elemento, pendiente, error, onConfirmar, onCancelar }: ConfirmDeleteModalProps) {
  const entidad = elemento?.entidad ?? 'categoría'
  const nombre = elemento?.nombre ?? categoria?.nombre
  const articulo = entidad === 'categoría' ? 'la' : 'el'
  const dialogRef = useRef<HTMLDialogElement>(null)
  useEffect(() => { dialogRef.current?.showModal() }, [])
  return (
    <dialog ref={dialogRef} aria-labelledby="delete-title" onCancel={(event) => { event.preventDefault(); if (!pendiente) onCancelar() }} className="fixed inset-0 m-auto w-[calc(100%-2rem)] max-w-md rounded-lg bg-white p-6 shadow-lg backdrop:bg-black/50 dark:bg-gray-900">
      <h2 id="delete-title" className="text-2xl font-bold text-blue-900 dark:text-blue-200">Eliminar {entidad}</h2>
      <p className="mt-4 break-words">¿Querés eliminar {articulo} {entidad} <strong>{nombre}</strong>?</p>
      {error && <p role="alert" className="mt-4 text-red-700 dark:text-red-300">{error}</p>}
      <div className="mt-6 flex justify-end gap-3">
        <button autoFocus type="button" disabled={pendiente} onClick={onCancelar} className="rounded-md bg-gray-200 px-4 py-2 disabled:opacity-50 dark:bg-gray-700">Cancelar</button>
        <button type="button" disabled={pendiente} onClick={onConfirmar} className="rounded-md bg-red-700 px-4 py-2 text-white disabled:opacity-50">{pendiente ? 'Eliminando...' : 'Eliminar'}</button>
      </div>
    </dialog>
  )
}
