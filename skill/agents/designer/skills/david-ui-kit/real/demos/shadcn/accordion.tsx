import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Example } from "@kit/demo";

export default function AccordionDemo() {
  return (
    <>
      <Example title="Preguntas frecuentes (abre y cierra para ver el movimiento)">
        <Accordion defaultValue={["entrega"]} className="max-w-md">
          <AccordionItem value="entrega">
            <AccordionTrigger>¿Cuándo llega el montaje?</AccordionTrigger>
            <AccordionContent>El equipo llega dos horas antes del evento al salón elegido.</AccordionContent>
          </AccordionItem>
          <AccordionItem value="cambios">
            <AccordionTrigger>¿Puedo cambiar los colores?</AccordionTrigger>
            <AccordionContent>Hasta 72 horas antes sin costo adicional.</AccordionContent>
          </AccordionItem>
          <AccordionItem value="pago">
            <AccordionTrigger>¿Cómo se paga?</AccordionTrigger>
            <AccordionContent>Un anticipo del 50 % y el saldo el día de la entrega.</AccordionContent>
          </AccordionItem>
        </Accordion>
      </Example>
      <Example title="Varios abiertos y un ítem deshabilitado">
        <Accordion multiple defaultValue={["a", "b"]} className="max-w-md">
          <AccordionItem value="a"><AccordionTrigger>Materiales</AccordionTrigger><AccordionContent>180 globos de látex y 40 de foil.</AccordionContent></AccordionItem>
          <AccordionItem value="b"><AccordionTrigger>Equipo</AccordionTrigger><AccordionContent>Tres decoradores y un coordinador.</AccordionContent></AccordionItem>
          <AccordionItem value="c" disabled><AccordionTrigger>Facturación (no disponible)</AccordionTrigger><AccordionContent>—</AccordionContent></AccordionItem>
        </Accordion>
      </Example>
    </>
  );
}
