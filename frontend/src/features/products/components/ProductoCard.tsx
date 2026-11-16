import type { Producto } from '../types/producto'
import { useCartStore } from '@/store/cartStore'
import { useNotificationStore } from '@/store/notificationStore'
import { moneda } from '@/shared/format'

export function ProductoCard({ producto }: { producto: Producto }) {
  const agregar = useCartStore((state) => state.agregar)
  const seVende = producto.disponible && producto.stock > 0
  function agregarProducto() {
    agregar({ producto_id: producto.id, nombre: producto.nombre, precio_unitario: producto.precio_base })
    useNotificationStore.getState().showNotification(`${producto.nombre} agregado al carrito.`)
  }
  return <article className="flex flex-col rounded-lg border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-900">
    {producto.imagen_url && <img src={producto.imagen_url} alt={producto.nombre} loading="lazy" className="mb-4 h-40 w-full rounded object-cover" />}
    <p className="text-sm text-blue-700 dark:text-blue-300">{producto.categoria.nombre}</p>
    <h2 className="mt-1 text-xl font-semibold">{producto.nombre}</h2>
    {producto.descripcion && <p className="mt-2 text-gray-600 dark:text-gray-300">{producto.descripcion}</p>}
    <p className="mt-4 text-lg font-bold">{moneda(producto.precio_base)}</p>
    <p className="mb-4 text-sm">{seVende ? `Stock: ${producto.stock}` : 'No disponible'}</p>
    <button type="button" aria-label={`Agregar al carrito: ${producto.nombre}`} disabled={!seVende} onClick={agregarProducto} className="mt-auto rounded bg-blue-700 px-4 py-2 text-white disabled:opacity-40">Agregar al carrito</button>
  </article>
}
