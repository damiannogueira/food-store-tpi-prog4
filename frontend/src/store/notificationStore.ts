import { create } from 'zustand'

interface NotificationState {
  message: string
  show: boolean
  notificationId: number
  showNotification: (message: string) => void
  hideNotification: () => void
}

export const useNotificationStore = create<NotificationState>((set) => ({
  message: '',
  show: false,
  notificationId: 0,
  showNotification: (message) => set((state) => ({ message, show: true, notificationId: state.notificationId + 1 })),
  hideNotification: () => set({ message: '', show: false }),
}))
