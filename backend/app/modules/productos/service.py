from app.modules.productos.models import Producto
from app.modules.productos.schemas import (
    ProductoCreate,
    ProductoRead,
    ProductosPaginados,
    ProductoStockUpdate,
    ProductoUpdate,
)
from app.modules.productos.unit_of_work import ProductoUnitOfWork


class CategoriaNoEncontrada(Exception):
    pass


class ProductoNoEncontrado(Exception):
    pass


class ProductoInvalido(Exception):
    pass


def validar_producto(producto: Producto) -> None:
    if not producto.nombre or producto.precio_base < 0 or producto.stock < 0:
        raise ProductoInvalido("Reviso el nombre, el precio y el stock del producto")


class ProductoService:
    def __init__(self, uow: ProductoUnitOfWork):
        self.uow = uow

    def listar(
        self,
        skip: int,
        limit: int,
        search: str | None,
        categoria_id: int | None,
        disponible: bool | None,
    ) -> ProductosPaginados:
        with self.uow as uow:
            total, items = uow.productos.search(
                skip, limit, search, categoria_id, disponible
            )
            return ProductosPaginados(
                total=total,
                items=[ProductoRead.model_validate(p) for p in items],
            )

    def obtener(self, id: int) -> ProductoRead:
        with self.uow as uow:
            producto = uow.productos.get_by_id(id)
            if producto is None or not producto.activo:
                raise ProductoNoEncontrado("Producto no encontrado")
            return ProductoRead.model_validate(producto)

    def crear(self, datos: ProductoCreate) -> ProductoRead:
        with self.uow as uow:
            categoria = uow.categorias.get_by_id(datos.categoria_id)
            if categoria is None or not categoria.activo:
                raise CategoriaNoEncontrada("Categoría no encontrada")
            producto = Producto.model_validate(datos)
            validar_producto(producto)
            uow.productos.add(producto)
            return ProductoRead.model_validate(producto)

    def actualizar(
        self, id: int, datos: ProductoUpdate | ProductoStockUpdate
    ) -> ProductoRead:
        with self.uow as uow:
            producto = uow.productos.get_by_id(id)
            if producto is None or not producto.activo:
                raise ProductoNoEncontrado("Producto no encontrado")
            cambios = datos.model_dump(exclude_unset=True)
            if "categoria_id" in cambios:
                categoria = uow.categorias.get_by_id(cambios["categoria_id"])
                if categoria is None or not categoria.activo:
                    raise CategoriaNoEncontrada("Categoría no encontrada")
            producto.sqlmodel_update(cambios)
            validar_producto(producto)
            uow.productos.add(producto)
            uow.productos.refresh_categoria(producto)
            return ProductoRead.model_validate(producto)

    def eliminar(self, id: int) -> None:
        with self.uow as uow:
            producto = uow.productos.get_by_id(id)
            if producto is None or not producto.activo:
                raise ProductoNoEncontrado("Producto no encontrado")
            producto.activo = False
            uow.productos.add(producto)
