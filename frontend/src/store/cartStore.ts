import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface ItemCarrito {
  producto_id: number
  nombre: string
  precio_unitario: number
  cantidad: number
}

interface CartState {
  items: ItemCarrito[]
  agregar: (producto: Omit<ItemCarrito, 'cantidad'>) => void
  quitar: (id: number) => void
  cambiarCantidad: (id: number, cantidad: number) => void
  vaciar: () => void
  total: () => number
}

export const useCartStore = create<CartState>()(persist((set, get) => ({
  items: [],
  agregar: (producto) => set((state) => {
    const existente = state.items.find((item) => item.producto_id === producto.producto_id)
    if (existente && !Number.isSafeInteger(existente.cantidad + 1)) return state
    return {
      items: existente
        ? state.items.map((item) => item.producto_id === producto.producto_id ? { ...producto, cantidad: item.cantidad + 1 } : item)
        : [...state.items, { ...producto, cantidad: 1 }],
    }
  }),
  quitar: (id) => set((state) => ({ items: state.items.filter((item) => item.producto_id !== id) })),
  cambiarCantidad: (id, cantidad) => {
    if (!Number.isSafeInteger(cantidad) || cantidad < 1) return
    set((state) => ({ items: state.items.map((item) => item.producto_id === id ? { ...item, cantidad } : item) }))
  },
  vaciar: () => set({ items: [] }),
  total: () => get().items.reduce((total, item) => total + item.precio_unitario * item.cantidad, 0),
}), { name: 'food-store-cart', partialize: (state) => ({ items: state.items }) }))
