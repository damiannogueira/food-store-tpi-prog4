import { useState } from 'react'
import { useForm } from '@tanstack/react-form'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { mensajeError } from '@/shared/api/request'
import { useAuth } from '@/features/auth/hooks/useAuth'

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const [error, setError] = useState<string | null>(null)
  const { login } = useAuth()
  const form = useForm({
    defaultValues: { username: '', password: '' },
    onSubmit: async ({ value }) => {
      setError(null)
      try {
        await login(value.username, value.password)
        navigate(location.state?.desde === '/checkout' ? '/checkout' : '/', { replace: true })
      } catch (error: unknown) { setError(mensajeError(error)) }
    },
  })
  return <main className="mx-auto max-w-md px-6 py-8">
    <h2 className="mb-6 text-3xl font-bold">Iniciar sesión</h2>
    {location.state?.registrado === true && <p role="status" className="mb-4 text-green-800 dark:text-green-300">Cuenta creada. Ya puedo iniciar sesión.</p>}
    <form className="space-y-4" onSubmit={(event) => { event.preventDefault(); void form.handleSubmit() }}>
      <form.Subscribe selector={(state) => state.isSubmitting}>
        {(pendiente) => <fieldset disabled={pendiente} className="space-y-4 disabled:opacity-60">
        <form.Field name="username">
          {(field) => <div><label htmlFor={field.name} className="mb-1 block font-medium">Usuario</label>
            <input id={field.name} name={field.name} required type="text" autoComplete="username" maxLength={50} value={field.state.value} onBlur={field.handleBlur} onChange={(event) => field.handleChange(event.target.value)} className="w-full rounded-md border border-gray-300 px-3 py-2 dark:border-gray-600" />
          </div>}
        </form.Field>
        <form.Field name="password">
          {(field) => <div><label htmlFor={field.name} className="mb-1 block font-medium">Contraseña</label>
            <input id={field.name} name={field.name} required type="password" autoComplete="current-password"  value={field.state.value} onBlur={field.handleBlur} onChange={(event) => field.handleChange(event.target.value)} className="w-full rounded-md border border-gray-300 px-3 py-2 dark:border-gray-600" />
          </div>}
        </form.Field>
        {error && <p role="alert" className="text-red-700 dark:text-red-300">{error}</p>}
        <button type="submit" className="rounded-md bg-blue-700 px-4 py-2 text-white">{pendiente ? 'Enviando...' : 'Ingresar'}</button>
        </fieldset>}
      </form.Subscribe>
    </form>
    <Link className="mt-6 block text-blue-700 underline dark:text-blue-300" to="/register">Crear una cuenta</Link>
  </main>
}
