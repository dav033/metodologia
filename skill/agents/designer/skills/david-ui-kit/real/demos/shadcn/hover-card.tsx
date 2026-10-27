import { CalendarDays } from "lucide-react";
import { HoverCard, HoverCardContent, HoverCardTrigger } from "@/components/ui/hover-card";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Example, Row } from "@kit/demo";

function Client({ name, initials, note }: { name: string; initials: string; note: string }) {
  return (
    <HoverCard>
      <HoverCardTrigger delay={100} closeDelay={150} render={<Button variant="link" className="px-0" />}>{name}</HoverCardTrigger>
      <HoverCardContent className="w-72">
        <div className="flex gap-3">
          <Avatar><AvatarFallback>{initials}</AvatarFallback></Avatar>
          <div className="flex flex-col gap-1">
            <h4 className="text-sm font-semibold">{name}</h4>
            <p className="text-sm">{note}</p>
            <span className="flex items-center gap-1.5 text-xs text-muted-foreground"><CalendarDays className="size-3.5" />Cliente desde marzo de 2024</span>
          </div>
        </div>
      </HoverCardContent>
    </HoverCard>
  );
}

export default function HoverCardDemo() {
  return (
    <>
      <Example title="Pasa el cursor o enfoca con el teclado">
        <Row className="gap-6">
          <Client name="Valentina Rojas" initials="VR" note="14 pedidos. Prefiere tonos pastel y arcos orgánicos." />
          <Client name="Eventos Lumbre" initials="EL" note="Agencia corporativa con 6 eventos al año." />
        </Row>
      </Example>
      <Example title="Abierta (vista estática)">
        <div className="min-h-44">
          <HoverCard defaultOpen>
            <HoverCardTrigger render={<Button variant="outline" />}>Salón Aurora</HoverCardTrigger>
            <HoverCardContent>
              <h4 className="text-sm font-semibold">Salón Aurora</h4>
              <p className="text-sm text-muted-foreground">Capacidad para 180 personas. Acceso lateral para montaje.</p>
            </HoverCardContent>
          </HoverCard>
        </div>
      </Example>
    </>
  );
}
