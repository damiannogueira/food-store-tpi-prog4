import { api } from '@/shared/api/request'
import type { Categoria, CategoriaDatos } from '@/features/categories/types/categoria'

export const getCategorias = (): Promise<Categoria[]> => api('/categorias')
export const getCategoria = (id: number): Promise<Categoria> => api(`/categorias/${id}`)
export const createCategoria = (datos: CategoriaDatos): Promise<Categoria> =>
  api('/categorias', {
    method: 'POST',
    body: datos,
  })
export const updateCategoria = (id: number, datos: CategoriaDatos): Promise<Categoria> =>
  api(`/categorias/${id}`, {
    method: 'PUT',
    body: datos,
  })
export const deleteCategoria = (id: number): Promise<void> =>
  api(`/categorias/${id}`, { method: 'DELETE' })
