import { BadgeCheck, Clock, Truck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Example, Row } from "@kit/demo";

export default function BadgeDemo() {
  return (
    <>
      <Example title="Variantes">
        <Row>
          <Badge>Confirmado</Badge>
          <Badge variant="secondary">Borrador</Badge>
          <Badge variant="outline">Pendiente</Badge>
          <Badge variant="destructive">Cancelado</Badge>
          <Badge variant="ghost">Archivado</Badge>
          <Badge variant="link">Ver más</Badge>
        </Row>
      </Example>
      <Example title="Con iconos">
        <Row>
          <Badge><BadgeCheck data-icon="inline-start" />Pagado</Badge>
          <Badge variant="secondary"><Clock data-icon="inline-start" />Entrega 15:00</Badge>
          <Badge variant="outline"><Truck data-icon="inline-start" />En camino</Badge>
        </Row>
      </Example>
      <Example title="Como enlace">
        <Row>
          <Badge render={<a href="#pedidos" />}>Pedidos 12</Badge>
          <Badge variant="outline" render={<a href="#clientes" />}>Clientes 48</Badge>
        </Row>
      </Example>
    </>
  );
}
