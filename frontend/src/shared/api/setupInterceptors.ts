import axios from 'axios'
import { axiosInstance } from './api'
import { useNotificationStore } from '@/store/notificationStore'

axiosInstance.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (axios.isAxiosError<{ detail?: unknown }>(error)) {
      const status = error.response?.status
      const path = error.config?.url?.split('?')[0]
      const desactivada = status === 400 && error.response?.data?.detail === 'Cuenta de usuario desactivada'
      if (status === 403) useNotificationStore.getState().showNotification('Acceso denegado')
      if (desactivada || (status === 401 && path !== '/auth/token' && path !== '/auth/me')) {
        window.dispatchEvent(new Event('auth:expired'))
      }
    }
    return Promise.reject(error)
  },
)
