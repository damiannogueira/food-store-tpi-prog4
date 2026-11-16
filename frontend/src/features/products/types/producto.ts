import type { Categoria } from '@/features/categories/types/categoria'

export interface Producto {
  id: number
  nombre: string
  descripcion: string | null
  precio_base: number
  imagen_url: string | null
  stock: number
  disponible: boolean
  activo: boolean
  categoria_id: number
  categoria: Categoria
}

export interface ProductoDatos {
  nombre: string
  descripcion: string | null
  precio_base: number
  imagen_url: string | null
  stock: number
  disponible: boolean
  categoria_id: number
}

export interface ProductosPaginados { total: number; items: Producto[] }
export interface FiltrosProductos { skip: number; limit: number; search?: string; categoria_id?: number; disponible?: boolean }
