import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectSeparator, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Example, Row } from "@kit/demo";

const salones = [
  { value: "aurora", label: "Salón Aurora" },
  { value: "jardin", label: "Salón Jardín" },
  { value: "terraza", label: "Terraza Norte" },
];

export default function SelectDemo() {
  return (
    <>
      <Example title="Seleccionar salón (abre y mira la animación)">
        <Select items={salones} defaultValue="aurora">
          <SelectTrigger className="w-56" aria-label="Salón">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectLabel>Salones</SelectLabel>
              {salones.map((s) => <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>)}
            </SelectGroup>
          </SelectContent>
        </Select>
      </Example>
      <Example title="Con grupos, sin valor y pequeño">
        <Row>
          <Select items={[{ value: "arco", label: "Arco orgánico" }, { value: "col", label: "Columna" }, { value: "cen", label: "Centro de mesa" }, { value: "tel", label: "Telón de fondo" }]}>
            <SelectTrigger className="w-56" aria-label="Tipo de decoración">
              <SelectValue placeholder="Tipo de decoración" />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectLabel>Estructuras</SelectLabel>
                <SelectItem value="arco">Arco orgánico</SelectItem>
                <SelectItem value="col">Columna</SelectItem>
              </SelectGroup>
              <SelectSeparator />
              <SelectGroup>
                <SelectLabel>Mesa y fondo</SelectLabel>
                <SelectItem value="cen">Centro de mesa</SelectItem>
                <SelectItem value="tel">Telón de fondo</SelectItem>
              </SelectGroup>
            </SelectContent>
          </Select>
          <Select items={salones} defaultValue="jardin">
            <SelectTrigger size="sm" className="w-40" aria-label="Salón pequeño"><SelectValue /></SelectTrigger>
            <SelectContent>{salones.map((s) => <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>)}</SelectContent>
          </Select>
        </Row>
      </Example>
      <Example title="Deshabilitado y con error">
        <Row>
          <Select items={salones} defaultValue="aurora" disabled>
            <SelectTrigger className="w-56" aria-label="Bloqueado"><SelectValue /></SelectTrigger>
            <SelectContent>{salones.map((s) => <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>)}</SelectContent>
          </Select>
          <Select items={salones}>
            <SelectTrigger className="w-56" aria-invalid aria-label="Salón obligatorio"><SelectValue placeholder="Elige un salón" /></SelectTrigger>
            <SelectContent>{salones.map((s) => <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>)}</SelectContent>
          </Select>
        </Row>
      </Example>
    </>
  );
}
