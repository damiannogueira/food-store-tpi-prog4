import { Link } from 'react-router-dom'
import { useCartStore } from '@/store/cartStore'
import { EstadoVacio } from '@/shared/components/EstadosLista'
import { moneda } from '@/shared/format'

export function CarritoPage() {
  const { items, quitar, cambiarCantidad, vaciar, total } = useCartStore()
  return <main className="mx-auto max-w-4xl px-6 py-8">
    <h1 className="mb-6 text-3xl font-bold">Carrito</h1>
    {items.length === 0 ? <><EstadoVacio mensaje="Tu carrito está vacío." /><Link to="/" className="mt-4 inline-block text-blue-700 underline dark:text-blue-300">Ver catálogo</Link></> : <>
      <ul className="space-y-4">{items.map((item) => <li key={item.producto_id} className="flex flex-wrap items-center justify-between gap-4 rounded-lg border border-gray-200 p-4 dark:border-gray-700">
        <div><h2 className="font-semibold">{item.nombre}</h2><p>{moneda(item.precio_unitario)} por unidad</p></div>
        <label className="flex items-center gap-2">Cantidad de {item.nombre}
          <input aria-label={`Cantidad de ${item.nombre}`} type="number" min="1" step="1" required value={item.cantidad} onChange={(event) => cambiarCantidad(item.producto_id, event.target.valueAsNumber)} className="w-20 rounded border px-2 py-1" />
        </label>
        <p>Subtotal: {moneda(item.precio_unitario * item.cantidad)}</p>
        <button type="button" className="text-red-700 underline dark:text-red-300" onClick={() => quitar(item.producto_id)}>Quitar<span className="sr-only"> {item.nombre}</span></button>
      </li>)}</ul>
      <p className="mt-6 text-xl font-bold">Total estimado: {moneda(total())}</p>
      <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">Los precios definitivos se calculan al confirmar el pedido.</p>
      <div className="mt-6 flex flex-wrap gap-4"><button type="button" className="rounded border px-4 py-2" onClick={vaciar}>Vaciar carrito</button><Link to="/checkout" className="rounded bg-blue-700 px-4 py-2 text-white">Continuar compra</Link></div>
    </>}
  </main>
}
