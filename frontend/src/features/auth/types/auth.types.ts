export interface UsuarioAuth {
  id: number
  username: string
  full_name: string
  email: string
  role: 'user' | 'admin'
  disabled: boolean
  created_at: string
}

export interface Credenciales { username: string; password: string }
export interface Registro extends Credenciales { full_name: string; email: string }
export interface MensajeAuth { message: string }
