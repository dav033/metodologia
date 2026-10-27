import * as React from "react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Example, Row } from "@kit/demo";

const tareas = ["Inflar globos", "Armar el arco", "Revisar el salón"];

export default function CheckboxDemo() {
  const [checks, setChecks] = React.useState<boolean[]>([true, false, false]);
  const all = checks.every(Boolean);
  const some = checks.some(Boolean) && !all;
  return (
    <>
      <Example title="Lista de tareas (marca para ver el trazo)">
        <div className="flex flex-col gap-3">
          <label className="flex items-center gap-2 text-sm font-medium">
            <Checkbox checked={all} indeterminate={some} onCheckedChange={(v) => setChecks(checks.map(() => !!v))} aria-label="Todas" />
            Todas las tareas
          </label>
          {tareas.map((t, i) => (
            <label key={t} className="flex items-center gap-2 pl-6 text-sm">
              <Checkbox checked={checks[i]} onCheckedChange={(v) => setChecks(checks.map((c, j) => (j === i ? !!v : c)))} />
              {t}
            </label>
          ))}
          <Row><Button size="sm" variant="outline" onClick={() => setChecks([false, false, false])}>Limpiar</Button></Row>
        </div>
      </Example>
      <Example title="Estados">
        <Row className="gap-6">
          <label className="flex items-center gap-2 text-sm"><Checkbox defaultChecked /> Marcado</label>
          <label className="flex items-center gap-2 text-sm"><Checkbox /> Sin marcar</label>
          <label className="flex items-center gap-2 text-sm"><Checkbox disabled /> Deshabilitado</label>
          <label className="flex items-center gap-2 text-sm"><Checkbox disabled defaultChecked /> Bloqueado</label>
          <label className="flex items-center gap-2 text-sm text-destructive"><Checkbox aria-invalid /> Acepto los términos</label>
        </Row>
      </Example>
    </>
  );
}
