import { Button } from "@/components/ui/button";
import { Drawer, DrawerClose, DrawerContent, DrawerDescription, DrawerFooter, DrawerHeader, DrawerTitle, DrawerTrigger } from "@/components/ui/drawer";
import { Example, Row } from "@kit/demo";

function Body({ title }: { title: string }) {
  return (
    <>
      <DrawerHeader>
        <DrawerTitle>{title}</DrawerTitle>
        <DrawerDescription>Boda Martínez · Salón Aurora · 14 de noviembre</DrawerDescription>
      </DrawerHeader>
      <ul className="flex flex-col gap-2 px-4 text-sm">
        <li className="flex justify-between"><span>Arco orgánico</span><span className="tabular-nums">1</span></li>
        <li className="flex justify-between"><span>Globos de látex</span><span className="tabular-nums">420</span></li>
        <li className="flex justify-between"><span>Letras foil</span><span className="tabular-nums">6</span></li>
      </ul>
      <DrawerFooter>
        <Button>Confirmar montaje</Button>
        <DrawerClose render={<Button variant="outline" />}>Cerrar</DrawerClose>
      </DrawerFooter>
    </>
  );
}

export default function DrawerDemo() {
  return (
    <>
      <Example title="Abierto desde abajo (arrastra hacia abajo o usa Cerrar)">
        <div className="min-h-80">
          <Drawer defaultOpen showSwipeHandle>
            <DrawerTrigger render={<Button variant="outline" />}>Ver resumen del pedido</DrawerTrigger>
            <DrawerContent><Body title="Resumen del pedido" /></DrawerContent>
          </Drawer>
        </div>
      </Example>
      <Example title="Otras direcciones">
        <Row>
          <Drawer swipeDirection="right" showSwipeHandle>
            <DrawerTrigger render={<Button variant="outline" />}>Panel derecho</DrawerTrigger>
            <DrawerContent><Body title="Detalle del evento" /></DrawerContent>
          </Drawer>
          <Drawer swipeDirection="left">
            <DrawerTrigger render={<Button variant="outline" />}>Panel izquierdo</DrawerTrigger>
            <DrawerContent><Body title="Filtros" /></DrawerContent>
          </Drawer>
        </Row>
      </Example>
    </>
  );
}
