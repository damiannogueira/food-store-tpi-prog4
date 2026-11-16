import { QueryClient } from '@tanstack/react-query'
import { ApiError } from './request'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: (count, error) => !(error instanceof ApiError && error.status < 500) && count < 1 },
  },
})
