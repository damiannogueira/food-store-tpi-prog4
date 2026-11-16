import { useState } from 'react'
import { useCategories } from '@/features/categories'
import { useProducts } from '../hooks/useProducts'
import { ProductoCard } from '../components/ProductoCard'
import { EstadoError, EstadoVacio, Paginacion, Skeleton } from '@/shared/components/EstadosLista'

const limite = 6

export function CatalogoPage() {
  const [busqueda, setBusqueda] = useState('')
  const [filtros, setFiltros] = useState({ search: '', categoria_id: undefined as number | undefined, pagina: 0 })
  const productos = useProducts({ skip: filtros.pagina * limite, limit: limite, search: filtros.search, categoria_id: filtros.categoria_id })
  const { query: categorias } = useCategories()

  return <main className="mx-auto max-w-6xl px-6 py-8">
    <h1 className="text-3xl font-bold">Catálogo</h1>
    <p className="mt-2 text-gray-600 dark:text-gray-300">Elegí tus comidas y agregalas al carrito.</p>
    <div className="my-6 flex flex-wrap items-end gap-4">
      <form className="flex flex-wrap items-end gap-2" onSubmit={(event) => { event.preventDefault(); setFiltros({ ...filtros, search: busqueda, pagina: 0 }) }}>
        <div><label htmlFor="busqueda" className="mb-1 block font-medium">Buscar por nombre</label>
          <input id="busqueda" type="search" value={busqueda} onChange={(event) => setBusqueda(event.target.value)} className="rounded border border-gray-300 px-3 py-2 dark:border-gray-600" />
        </div>
        <button type="submit" className="rounded bg-blue-700 px-4 py-2 text-white">Buscar</button>
      </form>
      <div><label htmlFor="categoria" className="mb-1 block font-medium">Categoría</label>
        <select id="categoria" value={filtros.categoria_id ?? ''} onChange={(event) => setFiltros({ ...filtros, categoria_id: event.target.value ? Number(event.target.value) : undefined, pagina: 0 })} className="rounded border border-gray-300 bg-white px-3 py-2 dark:border-gray-600 dark:bg-gray-900">
          <option value="">Todas las categorías</option>
          {categorias.data?.map((categoria) => <option key={categoria.id} value={categoria.id}>{categoria.nombre}</option>)}
        </select>
      </div>
    </div>
    {categorias.isError && <EstadoError error={categorias.error} reintentar={() => { void categorias.refetch() }} />}
    {productos.isPending && <Skeleton />}
    {productos.isError && <EstadoError error={productos.error} reintentar={() => { void productos.refetch() }} />}
    {productos.isSuccess && <>
      <p className="mb-4 text-sm">{productos.data.total} {productos.data.total === 1 ? 'producto' : 'productos'}</p>
      {productos.data.items.length === 0
        ? <EstadoVacio mensaje="No hay productos que coincidan con la búsqueda." />
        : <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">{productos.data.items.map((producto) => <ProductoCard key={producto.id} producto={producto} />)}</div>}
      <Paginacion pagina={filtros.pagina} total={productos.data.total} limite={limite} cambiar={(pagina) => setFiltros({ ...filtros, pagina })} />
    </>}
  </main>
}
