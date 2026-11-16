import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { cerrarSesion, iniciarSesion, obtenerSesion } from '@/features/auth/services/auth.service'
import { ApiError, mensajeError } from '@/shared/api/request'
import type { UsuarioAuth } from '@/features/auth/types/auth.types'

interface AuthState {
  usuario: UsuarioAuth | null
  cargando: boolean
  verificada: boolean
  errorSesion: string | null
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  checkSession: () => Promise<void>
  limpiarSesion: () => void
}

let comprobacion: Promise<void> | null = null
let revision = 0

export const useAuthStore = create<AuthState>()(persist((set) => ({
  usuario: null,
  cargando: true,
  verificada: false,
  errorSesion: null,
  limpiarSesion: () => {
    revision += 1
    set({ usuario: null, cargando: false, verificada: true, errorSesion: null })
  },
  login: async (username, password) => {
    if (comprobacion) await comprobacion
    set({ cargando: true, usuario: null, errorSesion: null })
    try {
      await iniciarSesion({ username, password })
      const usuario = await obtenerSesion()
      set({ usuario, verificada: true })
    } finally {
      set({ cargando: false })
    }
  },
  logout: async () => {
    if (comprobacion) await comprobacion
    set({ cargando: true })
    try {
      await cerrarSesion()
      revision += 1
      set({ usuario: null, verificada: true, errorSesion: null })
    } finally {
      set({ cargando: false })
    }
  },
  checkSession: () => {
    // Comparto la comprobación inicial si React la solicita dos veces.
    if (comprobacion) return comprobacion
    const actual = revision
    set({ cargando: true, verificada: false, errorSesion: null })
    comprobacion = (async () => {
      try {
        const usuario = await obtenerSesion()
        if (actual === revision) set({ usuario, verificada: true })
      } catch (error: unknown) {
        const sinSesion = error instanceof ApiError && (
          error.status === 401 || (error.status === 400 && error.detail === 'Cuenta de usuario desactivada')
        )
        if (actual === revision) set({ usuario: null, verificada: sinSesion, errorSesion: sinSesion ? null : mensajeError(error) })
      } finally {
        if (actual === revision) set({ cargando: false })
        comprobacion = null
      }
    })()
    return comprobacion
  },
}), { name: 'food-store-auth', partialize: (state) => ({ usuario: state.usuario }) }))
