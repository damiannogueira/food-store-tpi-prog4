# Food Store — Trabajo Práctico Integrador de Programación IV

**Estudiante:** Nogueira Damián Ignacio

**Materia:** Programación IV

**Carrera:** Tecnicatura Universitaria en Programación a Distancia (TUPaD)

**Institución:** Universidad Tecnológica Nacional (UTN)

**Año:** 2026

## Descripción

Desarrollé Food Store como Trabajo Práctico Integrador de Programación IV. Es una aplicación web para realizar pedidos de comida.

Los clientes pueden consultar el catálogo, buscar productos, agregarlos al carrito, realizar compras y consultar o cancelar sus pedidos. El administrador puede gestionar categorías, productos, stock, pedidos y usuarios, además de consultar un resumen de las operaciones.

## Tecnologías utilizadas

**Backend:**

- Python y FastAPI.
- SQLModel y PostgreSQL.
- Autenticación JWT mediante cookies HttpOnly.

**Frontend:**

- React, TypeScript y Vite.
- Tailwind CSS.
- Axios.
- TanStack Query, Form y Table.
- Zustand y React Router.

## Requisitos

Para ejecutar el proyecto se necesita:

- Python 3.11 a 3.13.
- PostgreSQL 15 o superior.
- Node.js 20.19 o superior de la rama 20, o 22.12 o superior, compatible con Vite.
- pnpm 9 o superior.

Las siguientes instrucciones utilizan PowerShell en Windows.

Las dependencias están fijadas en `backend/requirements.txt` y `frontend/package.json`. Conservar `frontend/pnpm-lock.yaml` para instalar las mismas versiones del frontend.

## 1. Preparar la base de datos

Primero, iniciar PostgreSQL y abrir SQL Shell (psql) con el usuario administrador `postgres`.

Crear un usuario y una base de datos para Food Store:

```text
CREATE ROLE foodstore_tpi_local LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;
\password foodstore_tpi_local
CREATE DATABASE foodstore_tpi_entrega OWNER foodstore_tpi_local;
\q
```

El comando `\password` permite establecer la contraseña del usuario creado.

Estos nombres son ejemplos para una instalación nueva. Si ya existen, se deben utilizar otros y actualizar la conexión en el archivo `.env` del backend. No es necesario borrar ninguna base de datos existente.

## 2. Instalar y ejecutar el backend

Desde la raíz del proyecto, abrir una terminal y ejecutar:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Si PowerShell impide activar el entorno virtual, se pueden ejecutar los comandos con `.\.venv\Scripts\python.exe` sin cambiar la política del sistema: `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`, `.\.venv\Scripts\python.exe -m app.db.seed` y `.\.venv\Scripts\python.exe -m uvicorn app.main:app`.

Si todavía no existe el archivo `.env`, copiar el ejemplo:

```powershell
Copy-Item .env.example .env
```

Editar `backend/.env` con los datos correspondientes:

```dotenv
DATABASE_URL=postgresql+psycopg2://foodstore_tpi_local:TU_CONTRASENA@localhost:5432/foodstore_tpi_entrega
SECRET_KEY=TU_CLAVE_SECRETA_ALEATORIA
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
COOKIE_SECURE=false
FRONTEND_ORIGIN=http://localhost:5173
```

Se debe reemplazar `TU_CONTRASENA` por la contraseña de PostgreSQL y `TU_CLAVE_SECRETA_ALEATORIA` por una clave segura de al menos 32 caracteres.

`DATABASE_URL` debe apuntar a la base nueva. `SECRET_KEY` y `ALGORITHM` se utilizan para firmar el JWT; `ACCESS_TOKEN_EXPIRE_MINUTES` define su duración. `COOKIE_SECURE=false` permite usar la cookie por HTTP local; con HTTPS debe ser `true`. `FRONTEND_ORIGIN` indica el origen permitido por CORS, sin barra final.

Para generar una clave, se puede ejecutar:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Si la contraseña de PostgreSQL contiene caracteres especiales reservados para URL, deben codificarse correctamente en `DATABASE_URL`.

El archivo `.env` contiene información privada y no debe incluirse en la entrega.

### Crear las tablas y cargar los datos iniciales

Ejecutar:

```powershell
python -m app.db.seed
```

Este comando crea las tablas necesarias y carga un administrador, tres categorías y ocho productos iniciales.

El seed puede ejecutarse nuevamente sin duplicar los registros existentes. Conserva sus contraseñas, stock y bajas; no restablece datos modificados.

**Administrador inicial:**

- Usuario: `admin`
- Contraseña: `Admin1234!`

### Iniciar el servidor

```powershell
uvicorn app.main:app
```

El backend estará disponible en:

- URL base de la API: `http://localhost:8000/api/v1`.
- Documentación Swagger: [http://localhost:8000/docs](http://localhost:8000/docs).
- Documentación ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc).

Mantener esta terminal abierta mientras se utiliza la aplicación.

Ejecutar primero el seed: iniciar el servidor no crea las tablas.

## 3. Instalar y ejecutar el frontend

Abrir otra terminal desde la raíz del proyecto:

```powershell
cd frontend
pnpm install
```

Si todavía no existe `frontend/.env`, copiar el archivo de ejemplo:

```powershell
Copy-Item .env.example .env
```

Verificar que contenga la dirección de la API:

```dotenv
VITE_API_URL=http://localhost:8000/api/v1
```

La URL debe incluir `/api/v1` una sola vez. Las variables `VITE_` son públicas: no colocar contraseñas ni claves privadas en el frontend.

Después, ejecutar:

```powershell
pnpm build
pnpm dev
```

Abrir la aplicación en:

[http://localhost:5173](http://localhost:5173).

Es importante utilizar `localhost` tanto para el frontend como para el backend para mantener el funcionamiento de las cookies de sesión.

Antes de iniciar los servidores, comprobar que los puertos 8000 y 5173 estén libres. Si alguno está ocupado, detener únicamente el proceso propio correspondiente o configurar otro puerto explícitamente. Al cambiar el backend, actualizar `VITE_API_URL`; al cambiar el frontend, actualizar `FRONTEND_ORIGIN`. Reiniciar los servidores después de modificar sus variables de entorno.

Para que Vite no seleccione otro puerto automáticamente, se puede ejecutar `pnpm dev --host localhost --port 5173 --strictPort`.

En algunas configuraciones de PowerShell puede ser necesario ejecutar `pnpm.cmd` en lugar de `pnpm`.

## 4. Funcionamiento de la aplicación

### Cliente

El catálogo y el carrito se pueden utilizar sin iniciar sesión.

Para realizar una compra, el cliente debe registrarse o iniciar sesión. Después puede completar la dirección de entrega, seleccionar la forma de pago y confirmar el pedido.

Desde **Mis pedidos** puede consultar las compras realizadas y cancelar aquellas que todavía estén en estado `PENDIENTE`.

Cuando se confirma una compra, el sistema descuenta el stock correspondiente. Si el pedido se cancela, ese stock se restituye.

### Administrador

Al iniciar sesión con el usuario administrador, se habilitan las siguientes funciones:

- **Resumen:** consulta de los principales indicadores de pedidos.
- **Categorías:** creación, edición y baja lógica.
- **Productos:** creación, edición, baja lógica, stock y disponibilidad.
- **Pedidos:** consulta y actualización de estados.
- **Usuarios:** consulta, activación y desactivación de cuentas.

Los pedidos siguen los cambios de estado permitidos por la consigna. Sus detalles y totales se conservan para mantener el historial de las compras.

## 5. Organización del proyecto

Organicé el backend por módulos de autenticación, usuarios, categorías, productos y pedidos.

Para separar las responsabilidades utilicé la arquitectura **Router → Service → Unit of Work → Repository → Model**. El Service abre el Unit of Work, que administra el commit, rollback y cierre de la sesión.

En el frontend organicé las funcionalidades por carpetas dentro de `src/features`. Utilicé TanStack Query para consultar y actualizar datos del servidor, Zustand para manejar el estado de sesión y del carrito, y React Router para la navegación y las rutas protegidas.

## 6. Repositorio y demostración

**Repositorio de GitHub:**

[damiannogueira/food-store-tpi-prog4](https://github.com/damiannogueira/food-store-tpi-prog4).

**Video de demostración:**

[Ver video de demostración](https://youtu.be/DE6A6q7AkGs).