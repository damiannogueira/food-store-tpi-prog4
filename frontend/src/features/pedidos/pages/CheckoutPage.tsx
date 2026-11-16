import { useForm } from '@tanstack/react-form'
import { Link, useNavigate } from 'react-router-dom'
import { useCartStore } from '@/store/cartStore'
import { useCrearPedido } from '../hooks/usePedidos'
import type { FormaPago } from '../types/pedido'
import { mensajeError } from '@/shared/api/request'
import { moneda } from '@/shared/format'

export function CheckoutPage() {
  const { items, vaciar, total } = useCartStore()
  const compra = useCrearPedido()
  const navigate = useNavigate()
  const form = useForm({
    defaultValues: { direccion_entrega: '', forma_pago: 'EFECTIVO' as FormaPago, notas: '' },
    onSubmit: async ({ value }) => {
      if (items.length === 0 || compra.isPending) return
      try {
        await compra.mutateAsync({
          ...value, notas: value.notas || null,
          items: items.map(({ producto_id, cantidad }) => ({ producto_id, cantidad })),
        })
        vaciar()
        navigate('/mis-pedidos', { replace: true })
      } catch {
        // Conservo el carrito y muestro el error de la mutación.
      }
    },
  })

  if (items.length === 0) return <main className="mx-auto max-w-xl p-8"><h1 className="text-2xl font-bold">El carrito está vacío</h1><Link to="/" className="mt-4 block text-blue-700 underline dark:text-blue-300">Volver al catálogo</Link></main>
  return <main className="mx-auto max-w-xl px-6 py-8">
    <h1 className="mb-4 text-3xl font-bold">Confirmar pedido</h1>
    <p className="mb-6">Total estimado: {moneda(total())}. El servidor confirma los precios y el stock.</p>
    <form className="space-y-4" onSubmit={(event) => { event.preventDefault(); void form.handleSubmit() }}>
      <fieldset disabled={compra.isPending} className="space-y-4 disabled:opacity-60">
        <form.Field name="direccion_entrega" validators={{ onChange: ({ value }) => value.length >= 5 && value.length <= 200 ? undefined : 'La dirección debe tener entre 5 y 200 caracteres.' }}>
          {(field) => <div><label htmlFor="direccion_entrega" className="mb-1 block font-medium">Dirección de entrega</label>
            <input id="direccion_entrega" autoComplete="street-address" required minLength={5} maxLength={200} value={field.state.value} onBlur={field.handleBlur} onChange={(event) => field.handleChange(event.target.value)} aria-invalid={field.state.meta.errors.length > 0} aria-describedby="direccion-error" className="w-full rounded border px-3 py-2" />
            <p id="direccion-error" className="text-sm text-red-700 dark:text-red-300">{field.state.meta.errors.join(' ')}</p>
          </div>}
        </form.Field>
        <form.Field name="forma_pago" validators={{ onChange: ({ value }) => value === 'EFECTIVO' || value === 'TRANSFERENCIA' ? undefined : 'Elegí una forma de pago válida.' }}>
          {(field) => <div><label htmlFor="forma_pago" className="mb-1 block font-medium">Forma de pago</label>
            <select id="forma_pago" value={field.state.value} onBlur={field.handleBlur} onChange={(event) => { if (event.target.value === 'EFECTIVO' || event.target.value === 'TRANSFERENCIA') field.handleChange(event.target.value) }} className="w-full rounded border bg-white px-3 py-2 dark:bg-gray-900"><option value="EFECTIVO">Efectivo</option><option value="TRANSFERENCIA">Transferencia</option></select>
          </div>}
        </form.Field>
        <form.Field name="notas">{(field) => <div><label htmlFor="notas" className="mb-1 block font-medium">Notas (opcional)</label><textarea id="notas" value={field.state.value} onBlur={field.handleBlur} onChange={(event) => field.handleChange(event.target.value)} className="w-full rounded border px-3 py-2" /></div>}</form.Field>
        {compra.isError && <p role="alert" className="text-red-700 dark:text-red-300">{mensajeError(compra.error)}</p>}
        <button type="submit" className="rounded bg-blue-700 px-4 py-2 text-white">{compra.isPending ? 'Confirmando...' : 'Confirmar compra'}</button>
      </fieldset>
    </form>
  </main>
}
