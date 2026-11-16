import { useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNotificationStore } from '@/store/notificationStore'
import { notificarError } from '@/shared/api/notifyError'
import { createCategoria, deleteCategoria, getCategorias, updateCategoria } from '@/features/categories/services/categorias.service'
import type { Categoria, CategoriaDatos } from '@/features/categories/types/categoria'

export function useCategories(opciones: { onGuardado?: () => void; onEliminado?: () => void } = {}) {
  const queryClient = useQueryClient()
  const query = useQuery({ queryKey: ['categorias'], queryFn: getCategorias })

  useEffect(() => {
    if (query.isError) notificarError(query.error)
  }, [query.isError, query.error, query.errorUpdatedAt])

  const guardar = useMutation({
    mutationFn: ({ categoria, datos }: { categoria: Categoria | null; datos: CategoriaDatos }) =>
      categoria ? updateCategoria(categoria.id, datos) : createCategoria(datos),
    onSuccess: (_categoria, variables) => {
      opciones.onGuardado?.()
      void queryClient.invalidateQueries({ queryKey: ['categorias'] })
      void queryClient.invalidateQueries({ queryKey: ['productos'] })
      useNotificationStore.getState().showNotification(variables.categoria ? 'Categoría actualizada correctamente.' : 'Categoría creada correctamente.')
    },
    onError: notificarError,
  })
  const eliminar = useMutation({
    mutationFn: deleteCategoria,
    onSuccess: () => {
      opciones.onEliminado?.()
      void queryClient.invalidateQueries({ queryKey: ['categorias'] })
      useNotificationStore.getState().showNotification('Categoría eliminada correctamente.')
    },
    onError: notificarError,
  })

  return { query, guardar, eliminar }
}
