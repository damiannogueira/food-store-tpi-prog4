import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { cancelarPedido, crearPedido, getPedido, getPedidos } from '../api/pedidos'
import { useAuthStore } from '@/store/authStore'
import type { UsuarioAuth } from '@/features/auth/types/auth.types'

async function listarPropios(usuario: UsuarioAuth, skip: number, limit: number) {
  if (usuario.role !== 'admin') return getPedidos(skip, limit)
  // El listado del backend devuelve todos los pedidos al admin; acá muestro los propios.
  const primera = await getPedidos(0, 100)
  const propios = primera.items.filter((pedido) => pedido.usuario_id === usuario.id)
  for (let offset = 100; offset < primera.total; offset += 100) {
    const pagina = await getPedidos(offset, 100)
    propios.push(...pagina.items.filter((pedido) => pedido.usuario_id === usuario.id))
  }
  return { total: propios.length, items: propios.slice(skip, skip + limit) }
}

export function usePedidos(pagina: number, limite: number) {
  const usuario = useAuthStore((state) => state.usuario)
  return useQuery({
    queryKey: ['pedidos', 'propios', usuario?.id, pagina, limite],
    queryFn: () => {
      if (!usuario) throw new Error('No hay sesión')
      return listarPropios(usuario, pagina * limite, limite)
    },
    enabled: !!usuario,
  })
}

export function useDetallePedido(id: number) {
  const usuarioId = useAuthStore((state) => state.usuario?.id)
  return useQuery({ queryKey: ['pedidos', 'detalle', usuarioId, id], queryFn: () => getPedido(id) })
}

export function useCrearPedido() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: crearPedido,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['productos'] }),
        queryClient.invalidateQueries({ queryKey: ['pedidos'] }),
      ])
    },
  })
}

export function useCancelarPedido() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: cancelarPedido,
    onSuccess: async (pedido) => {
      queryClient.setQueryData(['pedidos', 'detalle', pedido.usuario_id, pedido.id], pedido)
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['pedidos'] }),
        queryClient.invalidateQueries({ queryKey: ['productos'] }),
      ])
    },
  })
}
