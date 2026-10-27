import * as React from "react";
import { ArrowUpDown, Search } from "lucide-react";
import {
  flexRender, getCoreRowModel, getFilteredRowModel, getPaginationRowModel, getSortedRowModel, useReactTable,
  type ColumnDef, type SortingState,
} from "@tanstack/react-table";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Example } from "@kit/demo";

type Order = { id: string; client: string; event: string; balloons: number; total: number };
const data: Order[] = [
  { id: "PED-1284", client: "Valentina Rojas", event: "Boda", balloons: 420, total: 2450000 },
  { id: "PED-1283", client: "Eventos Lumbre", event: "Corporativo", balloons: 260, total: 1180000 },
  { id: "PED-1282", client: "Andrés Gaviria", event: "Cumpleaños", balloons: 120, total: 640000 },
  { id: "PED-1281", client: "Colegio San Martín", event: "Graduación", balloons: 800, total: 3200000 },
  { id: "PED-1280", client: "Laura Pineda", event: "Baby shower", balloons: 150, total: 720000 },
  { id: "PED-1279", client: "Hotel Sol", event: "Aniversario", balloons: 330, total: 1560000 },
  { id: "PED-1278", client: "Camilo Ortiz", event: "Cumpleaños", balloons: 90, total: 410000 },
  { id: "PED-1277", client: "Fundación Brisa", event: "Gala benéfica", balloons: 540, total: 2890000 },
];
const cop = (n: number) => n.toLocaleString("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });

const columns: ColumnDef<Order>[] = [
  {
    id: "select",
    header: ({ table }) => (
      <Checkbox
        aria-label="Seleccionar todo"
        checked={table.getIsAllPageRowsSelected()}
        indeterminate={table.getIsSomePageRowsSelected() && !table.getIsAllPageRowsSelected()}
        onCheckedChange={(v) => table.toggleAllPageRowsSelected(!!v)}
      />
    ),
    cell: ({ row }) => (
      <Checkbox aria-label={`Seleccionar ${row.original.id}`} checked={row.getIsSelected()} onCheckedChange={(v) => row.toggleSelected(!!v)} />
    ),
  },
  { accessorKey: "id", header: "Pedido" },
  {
    accessorKey: "client",
    header: ({ column }) => (
      <Button variant="ghost" size="sm" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>
        Cliente<ArrowUpDown data-icon="inline-end" />
      </Button>
    ),
  },
  { accessorKey: "event", header: "Evento" },
  {
    accessorKey: "total",
    header: ({ column }) => (
      <div className="text-right">
        <Button variant="ghost" size="sm" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>
          Total<ArrowUpDown data-icon="inline-end" />
        </Button>
      </div>
    ),
    cell: ({ row }) => <div className="text-right tabular-nums">{cop(row.original.total)}</div>,
  },
];

function OrdersTable({ initialFilter = "", pageSize = 5 }: { initialFilter?: string; pageSize?: number }) {
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [filter, setFilter] = React.useState(initialFilter);
  const [rowSelection, setRowSelection] = React.useState({});
  const table = useReactTable({
    data, columns,
    state: { sorting, rowSelection, globalFilter: filter },
    onSortingChange: setSorting,
    onRowSelectionChange: setRowSelection,
    onGlobalFilterChange: setFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize } },
  });
  return (
    <div className="flex flex-col gap-3">
      <div className="relative max-w-xs">
        <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input className="pl-8" placeholder="Filtrar por cliente o evento…" aria-label="Filtrar pedidos" value={filter} onChange={(e) => setFilter(e.target.value)} />
      </div>
      <div className="overflow-hidden rounded-lg border border-border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((g) => (
              <TableRow key={g.id}>
                {g.headers.map((h) => <TableHead key={h.id}>{h.isPlaceholder ? null : flexRender(h.column.columnDef.header, h.getContext())}</TableHead>)}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id} data-state={row.getIsSelected() ? "selected" : undefined}>
                  {row.getVisibleCells().map((c) => <TableCell key={c.id}>{flexRender(c.column.columnDef.cell, c.getContext())}</TableCell>)}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center text-muted-foreground">Sin resultados.</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      <div className="flex items-center justify-between gap-3 text-sm text-muted-foreground">
        <span>{table.getFilteredSelectedRowModel().rows.length} de {table.getFilteredRowModel().rows.length} fila(s) seleccionada(s).</span>
        <div className="flex items-center gap-2">
          <span>Página {table.getPageCount() ? table.getState().pagination.pageIndex + 1 : 0} de {table.getPageCount()}</span>
          <Button variant="outline" size="sm" onClick={() => table.previousPage()} disabled={!table.getCanPreviousPage()}>Anterior</Button>
          <Button variant="outline" size="sm" onClick={() => table.nextPage()} disabled={!table.getCanNextPage()}>Siguiente</Button>
        </div>
      </div>
    </div>
  );
}

export default function DataTableDemo() {
  return (
    <>
      <Example title="Ordenar, filtrar, seleccionar y paginar">
        <OrdersTable />
      </Example>
      <Example title="Filtro sin coincidencias">
        <OrdersTable initialFilter="globos rosa" />
      </Example>
    </>
  );
}
