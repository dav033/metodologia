import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCaption, TableCell, TableFooter, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Example } from "@kit/demo";

const orders = [
  { id: "PED-1284", client: "Valentina Rojas", event: "Boda · Salón Aurora", status: "Confirmado", total: 2450000 },
  { id: "PED-1283", client: "Eventos Lumbre", event: "Corporativo · Hotel Sol", status: "Pendiente", total: 1180000 },
  { id: "PED-1282", client: "Andrés Gaviria", event: "Cumpleaños · Casa Jardín", status: "Confirmado", total: 640000 },
  { id: "PED-1281", client: "Colegio San Martín", event: "Graduación · Auditorio", status: "Cancelado", total: 3200000 },
];
const cop = (n: number) => n.toLocaleString("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });

export default function TableDemo() {
  const total = orders.filter((o) => o.status !== "Cancelado").reduce((s, o) => s + o.total, 0);
  return (
    <>
      <Example title="Pedidos con pie y leyenda">
        <Table>
          <TableCaption>Pedidos de decoración de la semana.</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead>Pedido</TableHead>
              <TableHead>Cliente</TableHead>
              <TableHead>Evento</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead className="text-right">Total</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {orders.map((o) => (
              <TableRow key={o.id}>
                <TableCell className="font-medium">{o.id}</TableCell>
                <TableCell>{o.client}</TableCell>
                <TableCell className="text-muted-foreground">{o.event}</TableCell>
                <TableCell><Badge variant={o.status === "Cancelado" ? "destructive" : o.status === "Pendiente" ? "secondary" : "default"}>{o.status}</Badge></TableCell>
                <TableCell className="text-right tabular-nums">{cop(o.total)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
          <TableFooter>
            <TableRow>
              <TableCell colSpan={4}>Total activo</TableCell>
              <TableCell className="text-right tabular-nums">{cop(total)}</TableCell>
            </TableRow>
          </TableFooter>
        </Table>
      </Example>
      <Example title="Fila seleccionada">
        <Table>
          <TableHeader>
            <TableRow><TableHead>Salón</TableHead><TableHead className="text-right">Capacidad</TableHead></TableRow>
          </TableHeader>
          <TableBody>
            <TableRow><TableCell>Salón Aurora</TableCell><TableCell className="text-right">180</TableCell></TableRow>
            <TableRow data-state="selected"><TableCell>Casa Jardín</TableCell><TableCell className="text-right">90</TableCell></TableRow>
            <TableRow><TableCell>Hotel Sol</TableCell><TableCell className="text-right">250</TableCell></TableRow>
          </TableBody>
        </Table>
      </Example>
    </>
  );
}
