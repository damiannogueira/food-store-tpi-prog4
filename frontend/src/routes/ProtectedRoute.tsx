import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/features/auth'

export function ProtectedRoute({ allowedRoles }: { allowedRoles?: string[] }) {
  const location = useLocation()
  const { usuario, cargando, verificada, errorSesion, checkSession } = useAuthStore()
  if (cargando) return <p role="status" className="p-6">Comprobando sesión...</p>
  if (!verificada) return <div className="p-6" role="alert"><p>{errorSesion}</p><button type="button" onClick={() => { void checkSession() }} className="underline">Reintentar</button></div>
  if (!usuario) return <Navigate to="/login" state={{ desde: location.pathname }} replace />
  if (allowedRoles && !allowedRoles.includes(usuario.role)) return <Navigate to="/unauthorized" replace />
  return <Outlet />
}
