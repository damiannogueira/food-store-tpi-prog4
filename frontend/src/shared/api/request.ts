import axios from 'axios'
import { axiosInstance } from '@/shared/api/api'

export class ApiError extends Error {
  status: number
  detail: unknown

  constructor(status: number, message: string, detail: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

export async function api<T>(path: string, options?: { method?: string; body?: unknown; params?: Record<string, string | number | boolean | undefined> }): Promise<T> {
  try {
    const response = await axiosInstance.request<T>({ url: path, method: options?.method ?? 'GET', data: options?.body, params: options?.params })
    return response.data
  } catch (error: unknown) {
    if (!axios.isAxiosError<unknown>(error) || !error.response) throw error
    const body = error.response.data
    const detail = body && typeof body === 'object' && 'detail' in body ? body.detail : body
    let message = `No se pudo completar la solicitud (HTTP ${error.response.status}).`
    if (error.response.status === 404) {
      message = path.startsWith('/categorias/')
        ? 'La categoría ya no existe.'
        : 'El recurso solicitado ya no existe.'
    }
    if (error.response.status === 409) {
      message = 'La operación entra en conflicto con los datos existentes.'
    }
    if (error.response.status === 422) {
      message = 'Revisá los datos ingresados.'
    }
    if (typeof detail === 'string') message = detail
    else if (body && typeof body === 'object' && 'message' in body && typeof body.message === 'string') {
      message = body.message
    }
    throw new ApiError(error.response.status, message, detail)
  }
}

export function mensajeError(error: unknown): string {
  return error instanceof ApiError ? error.message : 'No se pudo conectar con el servidor. Intentá nuevamente.'
}
