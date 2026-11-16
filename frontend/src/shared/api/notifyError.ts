import { ApiError, mensajeError } from './request'
import { useNotificationStore } from '@/store/notificationStore'

export function notificarError(error: unknown) {
  if (error instanceof ApiError && error.status === 403) return
  useNotificationStore.getState().showNotification(mensajeError(error))
}
