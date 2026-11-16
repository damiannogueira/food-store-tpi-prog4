import { api } from '@/shared/api/request'
import type { Producto, ProductoDatos, ProductosPaginados, FiltrosProductos } from '../types/producto'

export const getProductos = (filtros: FiltrosProductos): Promise<ProductosPaginados> => api('/productos', { params: { ...filtros } })
export const getProducto = (id: number): Promise<Producto> => api(`/productos/${id}`)
export const createProducto = (datos: ProductoDatos): Promise<Producto> => api('/productos', { method: 'POST', body: datos })
export const updateProducto = (id: number, datos: Partial<ProductoDatos>): Promise<Producto> =>
  api(`/productos/${id}`, { method: 'PUT', body: datos })
export const deleteProducto = (id: number): Promise<void> => api(`/productos/${id}`, { method: 'DELETE' })

export const actualizarStock = (id: number, datos: { stock: number; disponible: boolean }): Promise<Producto> => api(`/productos/${id}/stock`, { method: 'PATCH', body: datos })
