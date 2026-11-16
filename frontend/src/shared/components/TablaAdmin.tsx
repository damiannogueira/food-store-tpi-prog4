import { flexRender, getCoreRowModel, getPaginationRowModel, useReactTable } from '@tanstack/react-table'
import type { ColumnDef } from '@tanstack/react-table'
import { useState } from 'react'

export function TablaAdmin<T>({ datos, columnas, titulo }: { datos: T[]; columnas: ColumnDef<T>[]; titulo: string }) {
  const [paginacion, setPaginacion] = useState({ pageIndex: 0, pageSize: 10 })
  const pagina = Math.min(paginacion.pageIndex, Math.max(0, Math.ceil(datos.length / paginacion.pageSize) - 1))
  // eslint-disable-next-line react-hooks/incompatible-library -- Uso Table 8 sin memoizar su instancia.
  const tabla = useReactTable({ data: datos, columns: columnas, getCoreRowModel: getCoreRowModel(), getPaginationRowModel: getPaginationRowModel(), state: { pagination: { ...paginacion, pageIndex: pagina } }, onPaginationChange: setPaginacion, autoResetPageIndex: false })
  return <><div className="overflow-x-auto"><table className="w-full text-left"><caption className="sr-only">{titulo}</caption>
    <thead className="bg-blue-50 dark:bg-gray-800">{tabla.getHeaderGroups().map((grupo) => <tr key={grupo.id}>{grupo.headers.map((header) => <th scope="col" className="p-3" key={header.id}>{header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}</th>)}</tr>)}</thead>
    <tbody>{tabla.getRowModel().rows.map((fila) => <tr key={fila.id} className="border-b dark:border-gray-700">{fila.getVisibleCells().map((celda) => <td className="p-3" key={celda.id}>{flexRender(celda.column.columnDef.cell, celda.getContext())}</td>)}</tr>)}</tbody>
  </table></div>{datos.length === 0 && <p role="status" className="p-4">No hay registros para mostrar.</p>}
  <nav aria-label="Paginación de tabla" className="mt-5 flex flex-wrap items-center justify-center gap-4">
    <button type="button" disabled={!tabla.getCanPreviousPage()} onClick={() => tabla.previousPage()} className="rounded border px-3 py-2 disabled:opacity-40">Anterior</button>
    <span>Página {tabla.getState().pagination.pageIndex + 1} de {Math.max(1, tabla.getPageCount())}</span>
    <button type="button" disabled={!tabla.getCanNextPage()} onClick={() => tabla.nextPage()} className="rounded border px-3 py-2 disabled:opacity-40">Siguiente</button>
  </nav></>
}
