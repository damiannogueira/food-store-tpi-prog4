import '@/shared/api/setupInterceptors'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { queryClient } from '@/shared/api/queryClient'
import { App } from '@/App'
import './index.css'

const expirada = () => {
  useAuthStore.getState().limpiarSesion()
  queryClient.clear()
}
window.addEventListener('auth:expired', expirada)
import.meta.hot?.dispose(() => window.removeEventListener('auth:expired', expirada))

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter><App /></BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
)
