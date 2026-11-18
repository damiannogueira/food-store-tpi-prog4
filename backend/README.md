# Food Store — Backend

Desarrollé el backend con FastAPI, SQLModel y PostgreSQL. Incluye autenticación JWT mediante cookie HttpOnly, roles, catálogo y pedidos con control transaccional de stock.

La instalación completa, la creación de PostgreSQL y los enlaces del proyecto están en el [README de la raíz](../README.md).

## Configuración y ejecución

Se requiere Python 3.11 a 3.13 y PostgreSQL 15 o superior. Las dependencias están fijadas en `requirements.txt`, incluidas `passlib[bcrypt]==1.7.4` y `bcrypt==4.0.1`.

Desde `backend/`, crear y activar el entorno virtual e instalar las dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Si todavía no existe `.env`, copiar `.env.example`. Completar `DATABASE_URL` con las credenciales de la base independiente `foodstore_tpi_entrega`, siguiendo el ejemplo del README raíz, y generar una `SECRET_KEY` propia de al menos 32 caracteres.

Las demás variables son `ALGORITHM=HS256`, `ACCESS_TOKEN_EXPIRE_MINUTES=30`, `COOKIE_SECURE=false` para HTTP local y `FRONTEND_ORIGIN=http://localhost:5173`. No incluir `.env` ni credenciales privadas en la entrega.

Con PostgreSQL configurado, ejecutar:

```powershell
python -m app.db.seed
uvicorn app.main:app
```

El seed crea las cinco tablas del UML si faltan y carga `admin` con contraseña inicial `Admin1234!`, tres categorías y ocho productos con stock. Es idempotente: no duplica registros ni restablece contraseñas, stock o bajas. Si el usuario `admin` existente no es un administrador activo, informa el conflicto sin sobrescribirlo.

El servidor no crea las tablas al iniciar; primero debe ejecutarse el seed. La URL base de la API es `http://localhost:8000/api/v1`. La documentación está disponible en [Swagger](http://localhost:8000/docs) y [ReDoc](http://localhost:8000/redoc).

## Organización

Organicé el backend siguiendo **Router → Service → Unit of Work → Repository → Model**.

- `app/core`: configuración, seguridad, dependencias, sesiones, Unit of Work y repositorio base genérico.
- `app/modules`: autenticación, usuarios, categorías, productos y pedidos. Pedido y DetallePedido comparten el módulo de pedidos.

El Router obtiene el Service con `Depends`. El Service abre el Unit of Work y construye la respuesta dentro del bloque. El Unit of Work abre la sesión, confirma o revierte los cambios y siempre la cierra. Los repositorios se limitan al acceso a datos.

## Autenticación y API

El registro público crea usuarios con rol `user`. El login recibe un formulario OAuth2 y guarda el JWT únicamente en una cookie HttpOnly. `/auth/me` recupera el perfil y `/auth/logout` elimina la cookie. Las contraseñas se almacenan con hash bcrypt.

El catálogo permite buscar productos, filtrar por categoría y paginar. Categorías y productos tienen baja lógica; cada producto pertenece a una sola categoría. El administrador también puede actualizar stock y disponibilidad y activar o desactivar usuarios. No puede desactivar su propia cuenta.

Los pedidos descuentan stock al crearse y lo restituyen al cancelarse dentro de la misma transacción. El detalle conserva el nombre y precio originales; las líneas y el total no se editan. Los cambios de estado siguen las transiciones permitidas por la consigna.

`PATCH /pedidos/{id}/cancelar` permite cancelar únicamente pedidos propios en `PENDIENTE`, también cuando el propietario es administrador. Para gestionar pedidos ajenos o cancelar desde `EN_PREPARACION`, el administrador utiliza `PATCH /pedidos/{id}/estado`. El resumen administrativo se consulta en `GET /pedidos/resumen`.
