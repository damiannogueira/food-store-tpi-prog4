import type { ColumnDef } from '@tanstack/react-table'
import { useAdminUsers } from '../hooks/useAdminUsers'
import type { UsuarioAuth } from '../types/auth.types'
import { useAuthStore } from '@/store/authStore'
import { TablaAdmin } from '@/shared/components/TablaAdmin'
import { EstadoError } from '@/shared/components/EstadosLista'
import { mensajeError } from '@/shared/api/request'

export function AdminUsersPage() {
  const { query, cambio } = useAdminUsers()
  const actual = useAuthStore((state) => state.usuario?.id)
  const columnas: ColumnDef<UsuarioAuth>[] = [
    { accessorKey: 'username', header: 'Username' }, { accessorKey: 'full_name', header: 'Nombre completo' }, { accessorKey: 'email', header: 'Email' }, { accessorKey: 'role', header: 'Rol' },
    { accessorKey: 'disabled', header: 'Estado', cell: ({ row }) => row.original.disabled ? 'Desactivado' : 'Activo' },
    { id: 'acciones', header: 'Acciones', cell: ({ row }) => row.original.id === actual ? <span>Sesión actual</span> : <button type="button" disabled={cambio.isPending} onClick={() => cambio.mutate({ id: row.original.id, disabled: !row.original.disabled })} className="text-blue-700 underline disabled:opacity-40 dark:text-blue-300">{row.original.disabled ? 'Activar' : 'Desactivar'}</button> },
  ]
  return <main className="mx-auto max-w-6xl p-6"><h1 className="mb-6 text-3xl font-bold">Administrar usuarios</h1>
    {query.isPending && <p role="status">Cargando usuarios...</p>}
    {query.isError && <EstadoError error={query.error} reintentar={() => { void query.refetch() }} />}
    {cambio.isError && <p role="alert" className="text-red-700 dark:text-red-300">{mensajeError(cambio.error)}</p>}
    {query.isSuccess && <TablaAdmin datos={query.data} columnas={columnas} titulo="Usuarios" />}
  </main>
}
