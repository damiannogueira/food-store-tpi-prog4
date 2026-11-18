# Food Store — Frontend

Desarrollé el frontend con React, TypeScript, Vite y Tailwind CSS. Utilicé Axios, Zustand, TanStack Query, TanStack Form, TanStack Table 8 y React Router.

La instalación completa y los enlaces del repositorio y del video están en el [README de la raíz](../README.md).

## Configuración y ejecución

Se requiere Node.js 20.19 o superior de la rama 20, o 22.12 o superior, compatible con Vite, y pnpm 9 o superior.

Desde `frontend/`:

```powershell
pnpm install
```

Si todavía no existe `.env`, copiar `.env.example` y verificar:

```dotenv
VITE_API_URL=http://localhost:8000/api/v1
```

La URL debe incluir `/api/v1` una sola vez. No colocar secretos en variables `VITE_`, porque son públicas. Iniciar el backend según el README raíz y ejecutar:

```powershell
pnpm build
pnpm dev
```

Abrir [http://localhost:5173](http://localhost:5173). Usar `localhost` también en la API para las cookies de sesión. Para evitar que Vite cambie de puerto si está ocupado, utilizar `pnpm dev --host localhost --port 5173 --strictPort`. Al cambiar el origen del frontend, ajustar `FRONTEND_ORIGIN` en el backend; reiniciar los servidores después de modificar sus variables.

En PowerShell se puede utilizar `pnpm.cmd` si `pnpm.ps1` está bloqueado. `pnpm lint` comprueba el código y `pnpm build` verifica TypeScript y genera `dist/`. Los proyectos TypeScript tienen `strict: true`. Conservar `pnpm-lock.yaml` y no incluir `.env`, `node_modules` ni `dist/` en la entrega.

## Organización

Organicé las funcionalidades por features y separé los datos del servidor del estado del cliente.

| Carpeta | Contenido |
|---|---|
| `src/features/auth` | Registro, login y administración de usuarios |
| `src/features/categories` | Gestión de categorías |
| `src/features/products` | Catálogo y administración de productos y stock |
| `src/features/pedidos` | Carrito, checkout, pedidos propios y gestión administrativa |
| `src/shared` | Axios, QueryClient y componentes compartidos |
| `src/store` | Sesión, carrito, tema y avisos de la interfaz |
| `src/routes` | Navegación y protección por sesión y rol |

TanStack Query administra consultas e invalidaciones. Zustand persiste el perfil y el carrito; el JWT no se almacena en localStorage. Axios utiliza `withCredentials` e interceptores para manejar errores de sesión. Al iniciar la aplicación se valida el perfil mediante `/auth/me`.

## Pantallas y funcionamiento

El catálogo en `/` permite buscar, filtrar por categoría y paginar. Los textos nuevos se aplican con Buscar; al vaciar el campo se restablece la búsqueda y la página sin recargar. El carrito es público y persiste al recargar.

Registro, login y checkout utilizan TanStack Form. Para comprar se requiere sesión. El frontend envía productos, cantidades, dirección, forma de pago y notas; el backend calcula los importes y verifica el stock. Mis pedidos muestra los pedidos propios y permite cancelar los que están en `PENDIENTE`.

El panel administrativo incluye resumen, categorías, productos, pedidos y usuarios. Utilicé TanStack Table 8 para las tablas y TanStack Form para crear y editar categorías y productos. Stock y disponibilidad se actualizan mediante el PATCH específico. Las bajas y cancelaciones requieren confirmación. Los cambios de estado actualizan los datos correspondientes.

Las rutas protegidas comprueban sesión y rol, y el backend autoriza cada operación. La interfaz incluye estados de carga, vacío y error, un selector de tema claro u oscuro y avisos temporales para informar al usuario.
