import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createProducto, deleteProducto, getProductos, updateProducto, actualizarStock } from '../services/productos.service'
import type { ProductoDatos } from '../types/producto'

export function useAdminProducts() {
  const client = useQueryClient()
  const query = useQuery({ queryKey: ['productos', 'admin'], queryFn: async () => {
    const primera = await getProductos({ skip: 0, limit: 100 })
    const items = [...primera.items]
    for (let skip = 100; skip < primera.total; skip += 100) items.push(...(await getProductos({ skip, limit: 100 })).items)
    return items
  } })
  const actualizar = async () => { await client.invalidateQueries({ queryKey: ['productos'] }) }
  const guardar = useMutation({ mutationFn: ({ id, datos, categoriaActual }: { id?: number; datos: ProductoDatos; categoriaActual?: number }) => id ? updateProducto(id, {
    nombre: datos.nombre, descripcion: datos.descripcion, precio_base: datos.precio_base, imagen_url: datos.imagen_url,
    ...(datos.categoria_id !== categoriaActual ? { categoria_id: datos.categoria_id } : {}),
  }) : createProducto(datos), onSuccess: actualizar })
  const stock = useMutation({ mutationFn: ({ id, stock, disponible }: { id: number; stock: number; disponible: boolean }) => actualizarStock(id, { stock, disponible }), onSuccess: actualizar })
  const eliminar = useMutation({ mutationFn: deleteProducto, onSuccess: actualizar })
  return { query, guardar, stock, eliminar }
}
