import { useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '@/features/auth/store/authStore'
import { registrarUsuario } from '@/features/auth/services/auth.service'
import type { Registro } from '@/features/auth/types/auth.types'
import { useNotificationStore } from '@/store/notificationStore'
import { notificarError } from '@/shared/api/notifyError'

export function useAuth() {
  const { usuario, cargando, verificada, errorSesion, checkSession, login: iniciarSesion, logout: cerrarSesion } = useAuthStore()
  const queryClient = useQueryClient()

  async function login(username: string, password: string) {
    try {
      await iniciarSesion(username, password)
      queryClient.clear()
      useNotificationStore.getState().showNotification('Sesión iniciada correctamente.')
    } catch (error: unknown) {
      notificarError(error)
      throw error
    }
  }

  async function logout() {
    try {
      await cerrarSesion()
      queryClient.clear()
      useNotificationStore.getState().showNotification('Sesión cerrada correctamente.')
    } catch (error: unknown) {
      notificarError(error)
      throw error
    }
  }

  async function register(datos: Registro) {
    try {
      const usuario = await registrarUsuario(datos)
      useNotificationStore.getState().showNotification('Cuenta creada. Ya puedo iniciar sesión.')
      return usuario
    } catch (error: unknown) {
      notificarError(error)
      throw error
    }
  }

  return {
    usuario, cargando, verificada, errorSesion, checkSession,
    esAdmin: usuario?.role === 'admin',
    login, logout, register,
  }
}
