import { useState } from 'react'
import { useForm } from '@tanstack/react-form'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { mensajeError } from '@/shared/api/request'
import { useAuth } from '@/features/auth/hooks/useAuth'

export function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [error, setError] = useState<string | null>(null)
  const form = useForm({
    defaultValues: { username: '', full_name: '', email: '', password: '' },
    onSubmit: async ({ value }) => {
      setError(null)
      try {
        await register(value)
        navigate('/login', { state: { registrado: true }, replace: true })
      } catch (error: unknown) { setError(mensajeError(error)) }
    },
  })
  return <main className="mx-auto max-w-md px-6 py-8">
    <h2 className="mb-6 text-3xl font-bold">Registrarme</h2>
    {location.state?.registrado === true && <p role="status" className="mb-4 text-green-800 dark:text-green-300">Cuenta creada. Ya puedo iniciar sesión.</p>}
    <form className="space-y-4" onSubmit={(event) => { event.preventDefault(); void form.handleSubmit() }}>
      <form.Subscribe selector={(state) => state.isSubmitting}>
        {(pendiente) => <fieldset disabled={pendiente} className="space-y-4 disabled:opacity-60">
        <form.Field name="username">
          {(field) => <div><label htmlFor={field.name} className="mb-1 block font-medium">Usuario</label>
            <input id={field.name} name={field.name} required type="text" autoComplete="username" maxLength={50} value={field.state.value} onBlur={field.handleBlur} onChange={(event) => field.handleChange(event.target.value)} className="w-full rounded-md border border-gray-300 px-3 py-2 dark:border-gray-600" />
          </div>}
        </form.Field>
        <form.Field name="full_name">
          {(field) => <div><label htmlFor={field.name} className="mb-1 block font-medium">Nombre completo</label>
            <input id={field.name} name={field.name} required type="text" autoComplete="name" maxLength={160} value={field.state.value} onBlur={field.handleBlur} onChange={(event) => field.handleChange(event.target.value)} className="w-full rounded-md border border-gray-300 px-3 py-2 dark:border-gray-600" />
          </div>}
        </form.Field>
        <form.Field name="email">
          {(field) => <div><label htmlFor={field.name} className="mb-1 block font-medium">Correo electrónico</label>
            <input id={field.name} name={field.name} required type="email" autoComplete="email"  value={field.state.value} onBlur={field.handleBlur} onChange={(event) => field.handleChange(event.target.value)} className="w-full rounded-md border border-gray-300 px-3 py-2 dark:border-gray-600" />
          </div>}
        </form.Field>
        <form.Field name="password">
          {(field) => <div><label htmlFor={field.name} className="mb-1 block font-medium">Contraseña</label>
            <input id={field.name} name={field.name} required type="password" autoComplete="new-password" minLength={8} maxLength={72} value={field.state.value} onBlur={field.handleBlur} onChange={(event) => field.handleChange(event.target.value)} className="w-full rounded-md border border-gray-300 px-3 py-2 dark:border-gray-600" />
          </div>}
        </form.Field>
        {error && <p role="alert" className="text-red-700 dark:text-red-300">{error}</p>}
        <button type="submit" className="rounded-md bg-blue-700 px-4 py-2 text-white">{pendiente ? 'Enviando...' : 'Crear cuenta'}</button>
        </fieldset>}
      </form.Subscribe>
    </form>
    <Link className="mt-6 block text-blue-700 underline dark:text-blue-300" to="/login">Ya tengo cuenta</Link>
  </main>
}
