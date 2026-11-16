# Food Store — TPI de Programación IV

- **Estudiante:** Nogueira Damián Ignacio.
- **Materia:** Programación IV.
- **Carrera:** Tecnicatura Universitaria en Programación a Distancia (TUPaD).
- **Institución:** Universidad Tecnológica Nacional (UTN).
- **Año:** 2026.

Aplicación de pedidos de comida de la UTN. Los clientes consultan el catálogo, mantienen un carrito, compran y consultan o cancelan sus pedidos. El administrador gestiona categorías, productos, stock, pedidos y usuarios, y consulta un resumen.

Backend FastAPI/SQLModel con PostgreSQL y JWT en cookie HttpOnly. Frontend React/TypeScript con Vite, Tailwind, Axios, TanStack Query, Form y Table, y Zustand.

- **Repositorio público:** pendiente de creación y autorización de publicación.
- **Video público:** pendiente de grabación y verificación del enlace.

## Requisitos

- Python 3.11 a 3.13; verificado con 3.13.2.
- PostgreSQL 15 o superior; verificado con 18.6. Se necesita una cuenta administradora para crear la base y un usuario propio.
- Node.js compatible con Vite: 20.19+ de la rama 20, o 22.12+; verificado con 24.13.0.
- pnpm 9 o superior; verificado con 10.32.1.
- Dos terminales para mantener backend y frontend en ejecución.

Las dependencias directas están fijadas en backend/requirements.txt y frontend/package.json. Conservar frontend/pnpm-lock.yaml.

## 1. Preparar una base PostgreSQL independiente

Abrir SQL Shell (psql) o ejecutar `psql -h localhost -p 5432 -U postgres -d postgres` con las credenciales de administración de la instalación local. Si psql no está en PATH, usar SQL Shell instalado con PostgreSQL.

Elegir nombres nuevos. Los siguientes son ejemplos; si ya existen, elegir otros y ajustar DATABASE_URL. No borrar ni reiniciar bases existentes.

```sql
CREATE ROLE foodstore_tpi_local LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;
\password foodstore_tpi_local
CREATE DATABASE foodstore_tpi_entrega OWNER foodstore_tpi_local;
\q
```

El comando `\password` solicita una contraseña nueva sin escribirla en la instrucción SQL. Este usuario será dueño de su base y podrá crear las tablas allí; no necesita permisos de superusuario.

## 2. Instalar y configurar el backend

Desde la raíz del proyecto, en PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Si la política de PowerShell impide activar el entorno, ejecutar los comandos con `.\.venv\Scripts\python.exe`: por ejemplo, `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`, `.\.venv\Scripts\python.exe -m app.db.seed` y `.\.venv\Scripts\python.exe -m uvicorn app.main:app`. No es necesario cambiar la política del sistema.

Solo si no existe backend/.env:

```powershell
Copy-Item -LiteralPath .env.example -Destination .env
```

Editar .env y completar:

```dotenv
DATABASE_URL=postgresql+psycopg2://foodstore_tpi_local:CONTRASENA_URL@localhost:5432/foodstore_tpi_entrega
SECRET_KEY=REEMPLAZAR_POR_UNA_CLAVE_ALEATORIA_DE_AL_MENOS_32_CARACTERES
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
COOKIE_SECURE=false
FRONTEND_ORIGIN=http://localhost:5173
```

DATABASE_URL debe apuntar a la base nueva creada en el paso anterior. Si la contraseña contiene caracteres reservados de una URL, codificarlos para URL; CONTRASENA_URL es un marcador, no una credencial válida. No copiar configuraciones de otras entregas.

Para generar una SECRET_KEY, ejecutar localmente `python -c "import secrets; print(secrets.token_urlsafe(48))"` y pegar el resultado en .env. Mantener este archivo privado.

| Variable | Uso |
| --- | --- |
| DATABASE_URL | Conexión PostgreSQL mediante psycopg2 |
| SECRET_KEY | Firma del JWT; al menos 32 caracteres |
| ALGORITHM | HS256 |
| ACCESS_TOKEN_EXPIRE_MINUTES | Expiración de cookie y token; 30 minutos |
| COOKIE_SECURE | false para HTTP local; true si se configura HTTPS |
| FRONTEND_ORIGIN | Origen exacto permitido por CORS, sin barra final |

Crear tablas y cargar los datos iniciales:

```powershell
python -m app.db.seed
```

El seed crea las cinco tablas si faltan, el administrador, tres categorías y ocho productos con stock. Es idempotente: repetirlo no duplica registros ni restablece stock, contraseñas o bajas.

**Administrador inicial:** usuario `admin`, contraseña `Admin1234!`.

Iniciar la API y mantener esta terminal abierta:

```powershell
uvicorn app.main:app
```

Opcional para desarrollo: agregar `--reload`. El servidor usa `http://localhost:8000`; no crea tablas al arrancar, por eso debe ejecutarse primero el seed.

- Swagger: [http://localhost:8000/docs](http://localhost:8000/docs).
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc).
- API: `http://localhost:8000/api/v1`.

## 3. Instalar y ejecutar el frontend

En otra terminal, desde la raíz:

```powershell
cd frontend
pnpm install
```

Solo si no existe frontend/.env, copiar .env.example a .env y conservar:

```dotenv
VITE_API_URL=http://localhost:8000/api/v1
```

La URL base incluye /api/v1 una sola vez. Si existe una configuración local, revisarla sin sobrescribirla. Las variables VITE_ son públicas: no colocar contraseñas ni SECRET_KEY en el frontend.

```powershell
pnpm build
pnpm dev
```

Abrir [http://localhost:5173](http://localhost:5173). Mantener la terminal abierta. Usar localhost en navegador y API para las cookies. Si el puerto 5173 está ocupado, detener el proceso propio que lo ocupa o configurar explícitamente el nuevo origen en backend/.env; no usar sin advertir el puerto alternativo de Vite.

Como alternativa para exigir el puerto previsto: `pnpm dev --host localhost --port 5173 --strictPort`. Reiniciar Vite después de modificar su entorno. En Windows se puede usar `pnpm.cmd` si PowerShell bloquea el archivo pnpm.ps1.

## Uso

El catálogo y el carrito son públicos. Registrar un cliente, iniciar sesión y completar dirección de 5 a 200 caracteres y pago en efectivo o transferencia para comprar. El backend determina los precios definitivos y el stock. Mis pedidos permite ver el detalle y cancelar pedidos propios en PENDIENTE.

El administrador accede desde Administración a resumen, categorías, productos, pedidos y usuarios. La baja de una categoría no oculta sus productos ni libera su nombre. Los pedidos solo avanzan por sus estados permitidos; cancelar restituye el stock. No se editan líneas ni totales de pedidos. Un administrador no puede desactivar su propia cuenta.

La sesión viaja exclusivamente en cookie HttpOnly. JavaScript persiste el perfil y el carrito, nunca el JWT. No hay pasarela de pago ni envío de notificaciones externas.

## Organización y controles

`backend/app/core` contiene infraestructura; `backend/app/modules` agrupa auth, usuarios, categorias, productos y pedidos. Categorías, productos y pedidos siguen Router → Service → Unit of Work → Repository → Model. El UoW confirma o revierte y cierra la sesión.

`frontend/src/features` agrupa dominios, `shared` infraestructura y componentes, `store` sesión/carrito y `routes` navegación protegida. Query administra los datos del servidor; Zustand el estado del cliente.

Desde frontend: `pnpm lint` y `pnpm build`. Los resultados de instalación aislada, contratos, UML y navegador se documentan en [la auditoría final](docs/auditoria-final-tpi.md), cuando se adjunta la carpeta docs a la copia de revisión. Las pruebas no requieren ni deben utilizar bases de otras entregas.

## Pendientes de entrega

Faltan incorporar y verificar las URLs reales del repositorio público y del video de 10–15 minutos. El video debe incluir cámara al inicio, registro, compra como cliente, gestión administrativa y cancelación con restitución de stock. Todavía no se consideran completas CE-01, CE-02 ni CE-07.

El ZIP definitivo se preparará después de la revisión. Debe incluir backend/, frontend/ y este README.md en la raíz, conservar ambos .env.example y los archivos de dependencias, y excluir .env, entornos virtuales, node_modules, .local, cachés y compilaciones. No incluir credenciales privadas.
