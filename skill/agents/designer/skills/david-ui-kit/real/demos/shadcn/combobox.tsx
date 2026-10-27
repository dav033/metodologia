import { Combobox, ComboboxContent, ComboboxEmpty, ComboboxInput, ComboboxItem, ComboboxList } from "@/components/ui/combobox";
import { Example, Row } from "@kit/demo";

const clientes = ["Laura Ruiz", "Camilo Mendoza", "Marta Pineda", "Julián Gómez", "Andrea Salcedo", "Eventos Aurora S.A.S."];

function ClienteCombobox({ defaultValue, disabled, placeholder = "Buscar cliente…" }: { defaultValue?: string; disabled?: boolean; placeholder?: string }) {
  return (
    <Combobox items={clientes} defaultValue={defaultValue} disabled={disabled}>
      <ComboboxInput placeholder={placeholder} disabled={disabled} aria-label="Cliente" className="w-64" />
      <ComboboxContent>
        <ComboboxEmpty>No se encontró ningún cliente.</ComboboxEmpty>
        <ComboboxList>
          {(item: string) => <ComboboxItem key={item} value={item}>{item}</ComboboxItem>}
        </ComboboxList>
      </ComboboxContent>
    </Combobox>
  );
}

export default function ComboboxDemo() {
  return (
    <>
      <Example title="Buscar cliente (escribe o abre la lista)" className="min-h-72">
        <ClienteCombobox />
      </Example>
      <Example title="Con valor y deshabilitado">
        <Row>
          <ClienteCombobox defaultValue="Marta Pineda" />
          <ClienteCombobox disabled defaultValue="Laura Ruiz" />
        </Row>
      </Example>
    </>
  );
}
