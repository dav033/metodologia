import { CalendarDays, MapPin } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardAction, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Example, Row, picture } from "@kit/demo";

export default function CardDemo() {
  return (
    <>
      <Example title="Pedido con acción y pie">
        <Card className="max-w-sm">
          <CardHeader>
            <CardTitle>Arco orgánico — Boda Ruiz</CardTitle>
            <CardDescription>Pedido #1042 · Cliente: Laura Ruiz</CardDescription>
            <CardAction><Badge variant="secondary">En producción</Badge></CardAction>
          </CardHeader>
          <CardContent className="flex flex-col gap-2 text-sm">
            <span className="flex items-center gap-2"><CalendarDays className="size-4" />Sábado 14 de noviembre</span>
            <span className="flex items-center gap-2"><MapPin className="size-4" />Salón Aurora, Bogotá</span>
          </CardContent>
          <CardFooter className="justify-end gap-2">
            <Button variant="outline">Ver detalle</Button>
            <Button>Confirmar</Button>
          </CardFooter>
        </Card>
      </Example>
      <Example title="Con imagen y tamaño compacto">
        <Row className="items-stretch">
          <Card className="w-64 pt-0">
            <img src={picture("Salón Aurora", 280, 480, 280)} alt="Salón Aurora" className="aspect-video w-full object-cover" />
            <CardHeader>
              <CardTitle>Salón Aurora</CardTitle>
              <CardDescription>Capacidad para 180 invitados</CardDescription>
            </CardHeader>
          </Card>
          <Card size="sm" className="w-64">
            <CardHeader>
              <CardTitle>Globos disponibles</CardTitle>
              <CardDescription>Inventario de hoy</CardDescription>
            </CardHeader>
            <CardContent><p className="text-3xl font-semibold">1.240</p></CardContent>
          </Card>
        </Row>
      </Example>
      <Example title="Estado vacío">
        <Card className="max-w-sm">
          <CardHeader>
            <CardTitle>Próximos eventos</CardTitle>
            <CardDescription>No hay eventos programados esta semana.</CardDescription>
          </CardHeader>
          <CardFooter><Button variant="outline">Crear evento</Button></CardFooter>
        </Card>
      </Example>
    </>
  );
}
