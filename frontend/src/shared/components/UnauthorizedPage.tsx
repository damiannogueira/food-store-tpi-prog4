import { Link } from 'react-router-dom'

export function UnauthorizedPage() {
  return <main className="mx-auto max-w-xl p-8"><h2 className="text-2xl font-bold">Acceso denegado</h2><p className="my-4">Tu cuenta no tiene permisos para acceder a esta página.</p><Link to="/" className="text-blue-700 underline dark:text-blue-300">Volver al catálogo</Link></main>
}
