import { lazy } from 'react'
import { AdminLayout } from '@/shared/layout/AdminLayout'
import { Navigate, Route, Routes } from 'react-router-dom'
import { LoginPage, RegisterPage } from '@/features/auth'
import { CatalogoPage } from '@/features/products'
import { CarritoPage } from '@/features/pedidos/pages/CarritoPage'
import { CheckoutPage } from '@/features/pedidos/pages/CheckoutPage'
import { MisPedidosPage } from '@/features/pedidos/pages/MisPedidosPage'
import { UnauthorizedPage } from '@/shared/components/UnauthorizedPage'
import { Navbar } from '@/shared/components/Navbar'
import { ProtectedRoute } from './ProtectedRoute'

const AdminCategoriasPage = lazy(() => import('@/features/categories/pages/AdminCategoriasPage').then((modulo) => ({ default: modulo.AdminCategoriasPage })))
const AdminProductosPage = lazy(() => import('@/features/products/pages/AdminProductosPage').then((modulo) => ({ default: modulo.AdminProductosPage })))
const AdminPedidosPage = lazy(() => import('@/features/pedidos/pages/AdminPedidosPage').then((modulo) => ({ default: modulo.AdminPedidosPage })))
const AdminResumenPage = lazy(() => import('@/features/pedidos/pages/AdminResumenPage').then((modulo) => ({ default: modulo.AdminResumenPage })))
const AdminUsersPage = lazy(() => import('@/features/auth/pages/AdminUsersPage').then((modulo) => ({ default: modulo.AdminUsersPage })))

export function AppRouter() {
  return <>
    <Navbar titulo="Food Store" />
    <Routes>
      <Route path="/" element={<CatalogoPage />} />
      <Route path="/carrito" element={<CarritoPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/unauthorized" element={<UnauthorizedPage />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/checkout" element={<CheckoutPage />} />
        <Route path="/mis-pedidos" element={<MisPedidosPage />} />
      </Route>
      <Route element={<ProtectedRoute allowedRoles={['admin']} />}>
        <Route element={<AdminLayout />}>
          <Route path="/admin/resumen" element={<AdminResumenPage />} />
          <Route path="/admin/categorias" element={<AdminCategoriasPage />} />
          <Route path="/admin/productos" element={<AdminProductosPage />} />
          <Route path="/admin/pedidos" element={<AdminPedidosPage />} />
          <Route path="/admin/usuarios" element={<AdminUsersPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  </>
}
