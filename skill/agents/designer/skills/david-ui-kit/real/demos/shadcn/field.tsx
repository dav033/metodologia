import { Checkbox } from "@/components/ui/checkbox";
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel, FieldLegend, FieldSet } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Example } from "@kit/demo";

export default function FieldDemo() {
  return (
    <>
      <Example title="Formulario de cliente">
        <FieldSet className="max-w-md">
          <FieldLegend>Datos del cliente</FieldLegend>
          <FieldGroup>
            <Field>
              <FieldLabel htmlFor="f-nombre">Nombre</FieldLabel>
              <Input id="f-nombre" defaultValue="Laura Ruiz" />
              <FieldDescription>Como aparecerá en la factura.</FieldDescription>
            </Field>
            <Field>
              <FieldLabel htmlFor="f-nota">Notas del evento</FieldLabel>
              <Textarea id="f-nota" placeholder="Colores, temática, accesos…" />
            </Field>
          </FieldGroup>
        </FieldSet>
      </Example>
      <Example title="Error y deshabilitado">
        <FieldGroup className="max-w-md">
          <Field data-invalid>
            <FieldLabel htmlFor="f-mail">Correo</FieldLabel>
            <Input id="f-mail" aria-invalid defaultValue="laura@ruiz" />
            <FieldError>Escribe un correo válido, por ejemplo laura@ruiz.co.</FieldError>
          </Field>
          <Field data-disabled>
            <FieldLabel htmlFor="f-id">Identificador</FieldLabel>
            <Input id="f-id" disabled defaultValue="CLI-0042" />
          </Field>
        </FieldGroup>
      </Example>
      <Example title="Horizontal con casilla">
        <Field orientation="horizontal" className="max-w-md">
          <Checkbox id="f-fact" defaultChecked />
          <FieldLabel htmlFor="f-fact">Enviar factura por correo</FieldLabel>
        </Field>
      </Example>
    </>
  );
}
