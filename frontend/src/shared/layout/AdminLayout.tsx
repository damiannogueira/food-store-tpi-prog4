import { Suspense } from 'react'
import { NavLink, Outlet } from 'react-router-dom'

const secciones = ['resumen', 'categorias', 'productos', 'pedidos', 'usuarios'] as const
const nombres = ['Resumen', 'Categorías', 'Productos', 'Pedidos', 'Usuarios']
export function AdminLayout() {
  return <><nav aria-label="Panel administrativo" className="flex flex-wrap justify-center gap-4 border-b p-4">
    {secciones.map((seccion, i) => <NavLink key={seccion} to={'/admin/' + seccion} className={({ isActive }) => isActive ? 'font-bold text-blue-700 underline dark:text-blue-300' : 'underline'}>{nombres[i]}</NavLink>)}
  </nav><Suspense fallback={<p role="status" className="p-6">Cargando panel...</p>}><Outlet /></Suspense></>
}
