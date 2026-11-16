import { useEffect, useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '@/features/auth'
import { mensajeError } from '@/shared/api/request'
import { useCartStore } from '@/store/cartStore'
import { useThemeStore } from '@/store/themeStore'

const claseEnlace = ({ isActive }: { isActive: boolean }) =>
  isActive
    ? 'font-semibold text-white underline underline-offset-4'
    : 'text-blue-200 hover:text-white'

export const Navbar = ({ titulo }: { titulo: string }) => {
  const cantidad = useCartStore((state) => state.items.reduce((total, item) => total + item.cantidad, 0))
  const { darkMode, toggleTheme } = useThemeStore()
  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode)
  }, [darkMode])
  const { usuario, cargando, logout } = useAuth()
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  async function salir() {
    setError(null)
    try {
      await logout()
      navigate('/login', { replace: true })
    } catch (error: unknown) { setError(mensajeError(error)) }
  }
  return <header className="bg-blue-900 px-6 py-4 text-white">
    <nav aria-label="Navegación principal" className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4">
      <h1 className="text-2xl font-bold">{titulo}</h1>
      <div className="flex flex-wrap items-center gap-4">
        <NavLink to="/" end className={claseEnlace}>Catálogo</NavLink>
        <NavLink to="/carrito" className={claseEnlace}>Carrito ({cantidad})</NavLink>
        {usuario ? <>
          <NavLink to="/mis-pedidos" className={claseEnlace}>Mis pedidos</NavLink>
          {usuario.role === 'admin' && <NavLink to="/admin/resumen" className={claseEnlace}>Administración</NavLink>}
          <span>{usuario.full_name} ({usuario.role})</span>
          <button type="button" disabled={cargando} className="underline disabled:opacity-50" onClick={() => { void salir() }}>Cerrar sesión</button>
        </> : <>
          <NavLink to="/login" className={claseEnlace}>Ingresar</NavLink>
          <NavLink to="/register" className={claseEnlace}>Registrarme</NavLink>
        </>}
        <button type="button" onClick={toggleTheme} aria-pressed={darkMode} className="rounded-md border border-blue-200 px-3 py-1 hover:bg-blue-800">{darkMode ? 'Modo claro' : 'Modo oscuro'}</button>
      </div>
    </nav>{error && <p role="alert">{error}</p>}
  </header>
}
