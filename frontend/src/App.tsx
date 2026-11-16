import { useEffect } from 'react'
import { useAuthStore } from '@/features/auth'
import { AppRouter } from '@/routes/AppRouter'
import { Toast } from '@/shared/components/Toast'

export const App = () => {
  useEffect(() => {
    void useAuthStore.getState().checkSession()
  }, [])
  return <>
    <AppRouter />
    <Toast />
  </>
}
