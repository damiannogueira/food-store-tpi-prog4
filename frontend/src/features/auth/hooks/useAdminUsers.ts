import { useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNotificationStore } from '@/store/notificationStore'
import { notificarError } from '@/shared/api/notifyError'
import { cambiarEstadoUsuario, listarUsuarios } from '@/features/auth/services/auth.service'

export function useAdminUsers() {
  const queryClient = useQueryClient()
  const query = useQuery({ queryKey: ['usuarios'], queryFn: listarUsuarios })
  useEffect(() => {
    if (query.isError) notificarError(query.error)
  }, [query.isError, query.error, query.errorUpdatedAt])
  const cambio = useMutation({
    mutationFn: ({ id, disabled }: { id: number; disabled: boolean }) => cambiarEstadoUsuario(id, disabled),
    onSuccess: async (_usuario, variables) => {
      await queryClient.invalidateQueries({ queryKey: ['usuarios'] })
      useNotificationStore.getState().showNotification(variables.disabled ? 'Usuario desactivado correctamente.' : 'Usuario activado correctamente.')
    },
    onError: notificarError,
  })

  return { query, cambio }
}
