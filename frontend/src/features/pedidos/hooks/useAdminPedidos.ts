import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { cambiarEstado, getPedidos, getResumen } from '../api/pedidos'
import type { EstadoPedido } from '../types/pedido'

export function useAdminPedidos(estado: EstadoPedido | undefined) {
  return useQuery({ queryKey: ['pedidos', 'admin', estado], queryFn: async () => {
    const primera = await getPedidos(0, 100, estado)
    const items = [...primera.items]
    for (let skip = 100; skip < primera.total; skip += 100) items.push(...(await getPedidos(skip, 100, estado)).items)
    return items
  } })
}
export function useResumenPedidos() {
  return useQuery({ queryKey: ['pedidos', 'resumen'], queryFn: getResumen })
}
export function useCambiarEstado() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: ({ id, estado }: { id: number; estado: EstadoPedido }) => cambiarEstado(id, estado),
    onError: () => { void client.invalidateQueries({ queryKey: ['pedidos'] }) },
    onSuccess: async (_pedido, variables) => {
      await Promise.all([
        client.invalidateQueries({ queryKey: ['pedidos'] }),
        ...(variables.estado === 'CANCELADO' ? [client.invalidateQueries({ queryKey: ['productos'] })] : []),
      ])
    },
  })
}
