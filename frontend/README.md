# Food Store · frontend del TPI

Frontend de Programación IV (UTN), adaptado desde la entrega de Unidad 10. Implementa catálogo público, sesión, carrito, checkout, pedidos propios y panel administrativo.

## Entorno e instalación

Se verificó con Node.js 24.13.0 y pnpm 10.32.1. Se necesita el backend del TPI con su propia base PostgreSQL, iniciado en `http://localhost:8000`, y CORS para `http://localhost:5173` con credenciales. Consultar [las instrucciones del backend](../backend/README.md).

Desde `frontend/`:

```powershell
pnpm.cmd install --frozen-lockfile
```

Si no existe una configuración local, copiar `.env.example` a `.env`. No sobrescribir archivos de entorno existentes.

```dotenv
VITE_API_URL=http://localhost:8000/api/v1
```

El prefijo `/api/v1` pertenece a la URL base; los servicios agregan rutas como `/productos` o `/auth/me`. Usar `localhost` tanto en el navegador como en la URL de la API. Reiniciar Vite al cambiar variables.

```powershell
pnpm.cmd dev --host localhost --port 5173 --strictPort
```

Abrir `http://localhost:5173`. En otros sistemas se puede usar `pnpm` sin `.cmd`.

## Arquitectura y navegación

| Carpeta | Responsabilidad |
| --- | --- |
| `src/features/auth` | Formularios y servicios de autenticación; código reutilizable de usuarios |
| `src/features/categories` | Tipos, servicios y componentes reutilizables de categorías |
| `src/features/products` | Catálogo, tarjetas, consultas y contratos de productos |
| `src/features/pedidos` | Carrito, checkout, pedidos propios, detalles y mutaciones |
| `src/shared` | Axios, QueryClient, errores, componentes compartidos y formato monetario |
| `src/store` | Sesión, carrito, tema y notificaciones |
| `src/routes` | Navegación y protección por sesión/rol |

`/`, `/carrito`, `/login`, `/register` y `/unauthorized` son públicas. `/checkout` y `/mis-pedidos` requieren sesión confirmada por el backend. Las cinco rutas `/admin/resumen`, `/admin/categorias`, `/admin/productos`, `/admin/pedidos` y `/admin/usuarios` requieren rol admin. El panel tiene navegación propia y carga sus páginas al ingresar.

TanStack Query administra los datos del servidor. Zustand persiste el usuario mediante `partialize` y los cuatro campos de cada ítem del carrito. Nunca se almacena el JWT: Axios envía la cookie HttpOnly. Al montar se valida la sesión mediante `/auth/me`.

Los precios del carrito son informativos. La compra envía únicamente productos, cantidades, dirección, forma de pago y notas. El backend calcula precios y total, controla stock y autoriza las operaciones. Al comprar o cancelar se invalidan productos y pedidos.

TanStack Table 8.21.3 administra las tablas y su paginación local. Los listados administrativos de productos y pedidos consultan páginas de hasta 100 elementos a la API para completar sus datos. TanStack Form se utiliza para crear y editar categorías y productos. Stock y disponibilidad se cambian mediante el PATCH específico. Las bajas y cancelaciones requieren confirmación.

El resumen obtiene sus seis indicadores del backend. Los cambios de estado respetan los estados terminales y usan `/pedidos/{id}/estado`; las líneas y los importes no se editan. Usuarios permite activar/desactivar y oculta la autodesactivación. Los componentes anteriores con Table 9 o ingredientes se conservan como texto en [los antecedentes de U10](../docs/antecedentes-frontend-u10/), fuera del código compilado.

## Verificaciones

```powershell
pnpm.cmd exec tsc -b
pnpm.cmd lint
pnpm.cmd build
```

`build` también ejecuta TypeScript y genera `dist/`. Ambos proyectos TypeScript tienen `strict: true`.

Se probaron el panel y la regresión del cliente con Chrome real, el backend TPI y exclusivamente su base PostgreSQL de pruebas. Los resultados y límites están en [el informe de etapa 5](../docs/informe-frontend-etapa5.md), con evidencia JSON y comprobaciones SQL de solo lectura. El [informe de etapa 4](../docs/informe-frontend-etapa4.md) conserva los antecedentes del cliente. Playwright es una herramienta local de verificación, no una dependencia de ejecución del frontend.

No incluir `.env`, `node_modules/`, entornos virtuales ni herramientas privadas en la entrega. El README final general, repositorio público, ZIP y video se completarán después de validar todas las etapas.
