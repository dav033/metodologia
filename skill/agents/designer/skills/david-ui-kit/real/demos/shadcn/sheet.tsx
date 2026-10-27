import { Button } from "@/components/ui/button";
import { Field, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Sheet, SheetClose, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Example, Row } from "@kit/demo";

export default function SheetDemo() {
  return (
    <>
      <Example title="Panel lateral de pedido (abierto; ciérralo y reábrelo)" className="min-h-80">
        <Sheet defaultOpen>
          <SheetTrigger render={<Button />}>Detalle del pedido</SheetTrigger>
          <SheetContent>
            <SheetHeader>
              <SheetTitle>Pedido #1042</SheetTitle>
              <SheetDescription>Boda Ruiz · Salón Aurora · 14 de noviembre</SheetDescription>
            </SheetHeader>
            <div className="px-4">
              <Field>
                <FieldLabel htmlFor="s-cant">Cantidad de globos</FieldLabel>
                <Input id="s-cant" type="number" defaultValue={180} />
              </Field>
            </div>
            <SheetFooter>
              <Button>Guardar cambios</Button>
              <SheetClose render={<Button variant="outline" />}>Cerrar</SheetClose>
            </SheetFooter>
          </SheetContent>
        </Sheet>
      </Example>
      <Example title="Otros lados">
        <Row>
          {(["left", "top", "bottom"] as const).map((side) => (
            <Sheet key={side}>
              <SheetTrigger render={<Button variant="outline" />}>{{ left: "Izquierda", top: "Arriba", bottom: "Abajo" }[side]}</SheetTrigger>
              <SheetContent side={side}>
                <SheetHeader>
                  <SheetTitle>Filtros de pedidos</SheetTitle>
                  <SheetDescription>Filtra por salón, estado o fecha de entrega.</SheetDescription>
                </SheetHeader>
              </SheetContent>
            </Sheet>
          ))}
        </Row>
      </Example>
    </>
  );
}
