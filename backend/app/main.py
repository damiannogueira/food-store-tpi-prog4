from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import register_models
from app.modules.auth.router import router as auth_router
from app.modules.categorias.router import router as categoria_router
from app.modules.pedidos.router import router as pedido_router
from app.modules.productos.router import router as producto_router
from app.modules.usuarios.router import router as usuario_router

register_models()

app = FastAPI(
    title="Food Store - TPI",
    description="API del TPI con catálogo, usuarios y pedidos transaccionales.",
    version="0.2.0",
)


@app.exception_handler(RequestValidationError)
async def error_validacion(
    _request: Request, error: RequestValidationError
) -> JSONResponse:
    # Conservo el detalle sin devolver contraseñas u otros valores ingresados.
    detalles = [
        {"type": item["type"], "loc": item["loc"], "msg": item["msg"]}
        for item in error.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": detalles})


app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (
    auth_router,
    usuario_router,
    categoria_router,
    producto_router,
    pedido_router,
):
    app.include_router(router, prefix="/api/v1")
