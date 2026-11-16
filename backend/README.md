# Food Store — backend del TPI

Backend FastAPI y SQLModel con autenticación JWT en cookie HttpOnly, roles, catálogo y pedidos transaccionales. Incluye seed idempotente. La etapa 3 se verificó con PostgreSQL 18.6 y Python 3.13.2 en un entorno virtual propio del TPI.

## Configuración

Requisitos del enunciado: Python 3.11–3.13 y PostgreSQL 15 o superior. Las dependencias están fijadas en `requirements.txt`, incluidas `passlib[bcrypt]==1.7.4` y `bcrypt==4.0.1`.

Desde esta carpeta:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Preparar `.env` a partir de `.env.example` solo si todavía no existe, completar las credenciales de una base **nueva e independiente**, `foodstore_tpi`, y una clave propia de al menos 32 caracteres. No reutilizar la base ni el `.env` de U9. No se incluyen credenciales reales.

Variables: `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `COOKIE_SECURE` y `FRONTEND_ORIGIN`.

La base debe existir antes de ejecutar el seed. El seed crea las cinco tablas del UML si faltan, sin borrar ni migrar tablas existentes. Utilizarlo exclusivamente con una base del TPI.

```powershell
python -m app.db.seed
```

Crea `admin` con contraseña inicial `Admin1234!`, rol admin, tres categorías y ocho productos con stock. La contraseña se almacena con bcrypt. Al repetirlo no duplica registros ni restablece contraseñas, stock o bajas. Si ya existe un usuario admin desactivado o sin rol admin, informa el conflicto sin sobrescribirlo.

```powershell
uvicorn app.main:app --reload
```

La documentación se expone en `/docs` y `/redoc`, con rutas bajo `/api/v1`. El arranque de Uvicorn no modifica el esquema: la preparación inicial corresponde al seed.

## Organización

`app/core` contiene configuración, seguridad, dependencias, factoría de sesiones, Unit of Work y repositorio base. `app/modules` agrupa auth, usuarios, categorias, productos y pedidos. Pedido y DetallePedido comparten el módulo pedidos.

El Router recibe el Service con `Depends`. El Service abre el UoW y construye el schema de salida dentro del bloque. El UoW abre la sesión y realiza commit o rollback y cierre; los repositorios solo acceden a datos.

## Verificación aislada

```powershell
python -B -m unittest discover -s tests -v
pip install -r requirements-dev.txt
python -B -m ruff check --no-cache app tests --select E,F,I
python -B -m ruff format --no-cache --check app tests
```

`test_base_tpi.py` usa sesiones simuladas y bloquea conexiones durante sus casos. `test_pedidos.py` crea una base SQLite nueva en memoria por prueba y ejercita los Services, repositorios, UoW y rutas HTTP con TestClient, incluyendo login con cookie, compra, rollback, stock, estados, cancelación y resumen. No utiliza bases anteriores ni archivos de base de datos.

La concurrencia usa `SELECT FOR UPDATE` en PostgreSQL; SQLite no implementa ese bloqueo. La suite PostgreSQL comprueba compras simultáneas, cancelaciones simultáneas, cancelación frente a avance y carritos en orden inverso. Usa conexiones diferentes y verifica esperas reales en `pg_stat_activity`.

Para ejecutarla, preparar otra base nueva cuyo nombre comience con `foodstore_tpi_test_`, asignar su URL a `TPI_TEST_DATABASE_URL` en la terminal y ejecutar:

```powershell
python -B -m unittest tests.verificar_postgresql -v
```

La suite rechaza otros nombres de base. Crea las tablas y datos de prueba en esa base; conserva los registros para inspección y utiliza nombres distintos en cada ejecución. No ejecuta DROP ni TRUNCATE. Requiere consultar las sesiones propias en `pg_stat_activity`. No debe apuntar a la base de uso de la aplicación.

`PATCH /pedidos/{id}/cancelar` solo admite pedidos propios en PENDIENTE, también cuando el dueño es admin. Para cancelar un pedido ajeno o en preparación, el administrador utiliza `PATCH /pedidos/{id}/estado`.

`pedidos_hoy` cuenta el día UTC según `created_at`, usando un intervalo desde las 00:00 inclusive hasta el día siguiente exclusive. Los ingresos suman todos los pedidos `ENTREGADO`, sin limitarse al día.

La etapa 3 conserva sus resultados en `../docs/informe-backend-etapa3.md`. El frontend ya está implementado y la auditoría integral se documenta en `../docs/auditoria-final-tpi.md`. Para instalar el conjunto, seguir el `../README.md` de la raíz. Los enlaces públicos del repositorio y del video y la entrega definitiva siguen pendientes.
