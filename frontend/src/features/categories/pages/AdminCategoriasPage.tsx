import { useState } from 'react'
import type { ColumnDef } from '@tanstack/react-table'
import { useCategories } from '../hooks/useCategories'
import { CategoriaModal } from '../components/CategoriaModal'
import type { Categoria } from '../types/categoria'
import { TablaAdmin } from '@/shared/components/TablaAdmin'
import { ConfirmDeleteModal } from '@/shared/components/ConfirmDeleteModal'
import { EstadoError } from '@/shared/components/EstadosLista'
import { mensajeError } from '@/shared/api/request'

export function AdminCategoriasPage() {
  const [formulario, setFormulario] = useState<{ categoria: Categoria | null } | null>(null)
  const [baja, setBaja] = useState<Categoria | null>(null)
  const { query, guardar, eliminar } = useCategories({ onGuardado: () => setFormulario(null), onEliminado: () => setBaja(null) })
  const columnas: ColumnDef<Categoria>[] = [
    { accessorKey: 'nombre', header: 'Nombre' }, { accessorKey: 'descripcion', header: 'Descripción', cell: ({ row }) => row.original.descripcion || '—' },
    { id: 'acciones', header: 'Acciones', cell: ({ row }) => <div className="flex gap-3"><button type="button" className="text-blue-700 underline dark:text-blue-300" onClick={() => { guardar.reset(); setFormulario({ categoria: row.original }) }}>Editar</button><button type="button" className="text-red-700 underline dark:text-red-300" onClick={() => { eliminar.reset(); setBaja(row.original) }}>Dar de baja</button></div> },
  ]
  return <main className="mx-auto max-w-6xl p-6"><div className="mb-6 flex flex-wrap justify-between gap-4"><h1 className="text-3xl font-bold">Administrar categorías</h1><button type="button" onClick={() => { guardar.reset(); setFormulario({ categoria: null }) }} className="rounded bg-blue-700 px-4 py-2 text-white">Nueva categoría</button></div>
    {query.isPending && <p role="status">Cargando categorías...</p>}
    {query.isError && <EstadoError error={query.error} reintentar={() => { void query.refetch() }} />}
    {query.isSuccess && <TablaAdmin datos={query.data} columnas={columnas} titulo="Categorías" />}
    {formulario && <CategoriaModal categoria={formulario.categoria} pendiente={guardar.isPending} error={guardar.isError ? mensajeError(guardar.error) : null} onGuardar={(datos) => guardar.mutate({ categoria: formulario.categoria, datos })} onCancelar={() => setFormulario(null)} />}
    {baja && <ConfirmDeleteModal categoria={baja} pendiente={eliminar.isPending} error={eliminar.isError ? mensajeError(eliminar.error) : null} onConfirmar={() => eliminar.mutate(baja.id)} onCancelar={() => setBaja(null)} />}
  </main>
}
