import { api } from '@/shared/api/request'
import type { Credenciales, Registro, UsuarioAuth } from '../types/auth.types'

export const iniciarSesion = (datos: Credenciales): Promise<{ message: string }> =>
  api('/auth/token', { method: 'POST', body: new URLSearchParams({ username: datos.username, password: datos.password }) })
export const cerrarSesion = (): Promise<{ mensaje: string }> => api('/auth/logout', { method: 'POST' })
export const obtenerSesion = (): Promise<UsuarioAuth> => api('/auth/me')
export const registrarUsuario = (datos: Registro): Promise<UsuarioAuth> =>
  api('/auth/register', { method: 'POST', body: datos })
export const listarUsuarios = (): Promise<UsuarioAuth[]> => api('/admin/usuarios')
export const cambiarEstadoUsuario = (id: number, disabled: boolean): Promise<UsuarioAuth> =>
  api(`/admin/usuarios/${id}/${disabled ? 'desactivar' : 'activar'}`, { method: 'POST' })
