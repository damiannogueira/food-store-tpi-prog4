import { useState } from 'react'
import type { ColumnDef } from '@tanstack/react-table'
import { useAdminProducts } from '../hooks/useAdminProducts'
import { useCategories } from '@/features/categories/hooks/useCategories'
import type { Producto } from '../types/producto'
import { ProductoModal } from '../components/ProductoModal'
import { StockModal } from '../components/StockModal'
import { TablaAdmin } from '@/shared/components/TablaAdmin'
import { ConfirmDeleteModal } from '@/shared/components/ConfirmDeleteModal'
import { EstadoError } from '@/shared/components/EstadosLista'
import { moneda } from '@/shared/format'
import { mensajeError } from '@/shared/api/request'

export function AdminProductosPage() {
  const productos = useAdminProducts()
  const { query: categorias } = useCategories()
  const [formulario, setFormulario] = useState<{ producto: Producto | null } | null>(null)
  const [stock, setStock] = useState<Producto | null>(null)
  const [baja, setBaja] = useState<Producto | null>(null)
  const columnas: ColumnDef<Producto>[] = [
    { accessorKey: 'nombre', header: 'Nombre' }, { id: 'categoria', header: 'Categoría', cell: ({ row }) => row.original.categoria.nombre },
    { accessorKey: 'precio_base', header: 'Precio', cell: ({ row }) => moneda(row.original.precio_base) }, { accessorKey: 'stock', header: 'Stock' },
    { accessorKey: 'disponible', header: 'Disponible', cell: ({ row }) => row.original.disponible ? 'Sí' : 'No' },
    { id: 'acciones', header: 'Acciones', cell: ({ row }) => <div className="flex flex-wrap gap-3"><button type="button" className="text-blue-700 underline dark:text-blue-300" onClick={() => { productos.guardar.reset(); setFormulario({ producto: row.original }) }}>Editar</button><button type="button" className="underline" onClick={() => { productos.stock.reset(); setStock(row.original) }}>Stock y disponibilidad</button><button type="button" className="text-red-700 underline dark:text-red-300" onClick={() => { productos.eliminar.reset(); setBaja(row.original) }}>Dar de baja</button></div> },
  ]
  return <main className="mx-auto max-w-6xl p-6"><div className="mb-6 flex flex-wrap justify-between gap-4"><h1 className="text-3xl font-bold">Administrar productos</h1><button type="button" disabled={!categorias.isSuccess} onClick={() => { productos.guardar.reset(); setFormulario({ producto: null }) }} className="rounded bg-blue-700 px-4 py-2 text-white disabled:opacity-40">Nuevo producto</button></div>
    {productos.query.isPending && <p role="status">Cargando productos...</p>}
    {productos.query.isError && <EstadoError error={productos.query.error} reintentar={() => { void productos.query.refetch() }} />}
    {categorias.isError && <EstadoError error={categorias.error} reintentar={() => { void categorias.refetch() }} />}
    {productos.query.isSuccess && <TablaAdmin datos={productos.query.data} columnas={columnas} titulo="Productos" />}
    {formulario && <ProductoModal producto={formulario.producto} categorias={categorias.data ?? []} pendiente={productos.guardar.isPending} error={productos.guardar.isError ? mensajeError(productos.guardar.error) : null} guardar={(datos) => {
      const id = formulario.producto?.id
      productos.guardar.mutate({ id, datos, categoriaActual: formulario.producto?.categoria_id }, { onSuccess: () => setFormulario(null) })
    }} cerrar={() => setFormulario(null)} />}
    {stock && <StockModal producto={stock} pendiente={productos.stock.isPending} error={productos.stock.isError ? mensajeError(productos.stock.error) : null} guardar={(cantidad, disponible) => productos.stock.mutate({ id: stock.id, stock: cantidad, disponible }, { onSuccess: () => setStock(null) })} cerrar={() => setStock(null)} />}
    {baja && <ConfirmDeleteModal elemento={{ nombre: baja.nombre, entidad: 'producto' }} pendiente={productos.eliminar.isPending} error={productos.eliminar.isError ? mensajeError(productos.eliminar.error) : null} onConfirmar={() => productos.eliminar.mutate(baja.id, { onSuccess: () => setBaja(null) })} onCancelar={() => setBaja(null)} />}
  </main>
}
