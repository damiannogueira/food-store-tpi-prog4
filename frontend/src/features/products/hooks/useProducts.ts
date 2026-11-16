import { useQuery } from '@tanstack/react-query'
import { getProductos } from '../services/productos.service'
import type { FiltrosProductos } from '../types/producto'

export function useProducts(filtros: FiltrosProductos) {
  return useQuery({ queryKey: ['productos', filtros], queryFn: () => getProductos(filtros) })
}
