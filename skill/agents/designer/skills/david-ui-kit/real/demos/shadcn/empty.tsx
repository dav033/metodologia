import { CalendarX, PackageSearch, Plus } from "lucide-react";
import { Empty, EmptyContent, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from "@/components/ui/empty";
import { Button } from "@/components/ui/button";
import { Example } from "@kit/demo";

export default function EmptyDemo() {
  return (
    <>
      <Example title="Sin eventos, con acción">
        <Empty className="border border-dashed border-border">
          <EmptyHeader>
            <EmptyMedia variant="icon"><CalendarX /></EmptyMedia>
            <EmptyTitle>Aún no hay eventos</EmptyTitle>
            <EmptyDescription>Crea el primer evento para empezar a planear la decoración con globos.</EmptyDescription>
          </EmptyHeader>
          <EmptyContent>
            <Button><Plus data-icon="inline-start" />Nuevo evento</Button>
          </EmptyContent>
        </Empty>
      </Example>
      <Example title="Búsqueda sin resultados">
        <Empty className="border border-border">
          <EmptyHeader>
            <EmptyMedia variant="icon"><PackageSearch /></EmptyMedia>
            <EmptyTitle>Sin resultados</EmptyTitle>
            <EmptyDescription>No encontramos pedidos para “globos metalizados dorados”. Prueba con otro término.</EmptyDescription>
          </EmptyHeader>
          <EmptyContent>
            <Button variant="outline">Limpiar búsqueda</Button>
          </EmptyContent>
        </Empty>
      </Example>
    </>
  );
}
