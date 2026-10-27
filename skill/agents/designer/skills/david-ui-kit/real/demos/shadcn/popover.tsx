import { Button } from "@/components/ui/button";
import { Field, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverDescription, PopoverHeader, PopoverTitle, PopoverTrigger } from "@/components/ui/popover";
import { Example, Row } from "@kit/demo";

export default function PopoverDemo() {
  return (
    <>
      <Example title="Ajustar entrega (abierto; haz clic fuera para cerrar)" className="min-h-72">
        <Popover defaultOpen>
          <PopoverTrigger render={<Button variant="outline" />}>Hora de entrega</PopoverTrigger>
          <PopoverContent align="start" className="w-72">
            <PopoverHeader>
              <PopoverTitle>Hora de entrega</PopoverTitle>
              <PopoverDescription>Se avisará al cliente del cambio.</PopoverDescription>
            </PopoverHeader>
            <Field>
              <FieldLabel htmlFor="p-hora">Hora</FieldLabel>
              <Input id="p-hora" type="time" defaultValue="14:00" />
            </Field>
          </PopoverContent>
        </Popover>
      </Example>
      <Example title="Lados distintos">
        <Row className="pt-28 pb-4">
          <Popover>
            <PopoverTrigger render={<Button variant="secondary" />}>Arriba</PopoverTrigger>
            <PopoverContent side="top"><PopoverDescription>Quedan 24 arcos disponibles.</PopoverDescription></PopoverContent>
          </Popover>
          <Popover>
            <PopoverTrigger render={<Button variant="secondary" />}>Abajo</PopoverTrigger>
            <PopoverContent side="bottom"><PopoverDescription>Última revisión: hoy 09:15.</PopoverDescription></PopoverContent>
          </Popover>
        </Row>
      </Example>
    </>
  );
}
