import { useEffect } from 'react'
import { useNotificationStore } from '@/store/notificationStore'

export function Toast() {
  const { message, show, notificationId, hideNotification } = useNotificationStore()

  useEffect(() => {
    if (!show) return
    const timer = window.setTimeout(hideNotification, 3000)
    return () => window.clearTimeout(timer)
  }, [show, notificationId, hideNotification])

  if (!show) return null
  return <div role="status" aria-live="polite" aria-atomic="true" className="fixed right-4 bottom-4 z-50 max-w-sm rounded-lg bg-gray-800 px-4 py-3 text-white shadow-lg dark:bg-gray-200 dark:text-gray-900">{message}</div>
}
