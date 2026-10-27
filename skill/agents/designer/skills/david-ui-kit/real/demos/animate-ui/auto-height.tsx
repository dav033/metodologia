import { useState } from "react";
import { AutoHeight } from "@animate-ui/react/primitives/effects/auto-height";
import { useMotionProfile } from "@kit/motion";
import { Example } from "@kit/demo";

const detalles = [
  "Arco orgánico de 3 metros con globos pastel.",
  "Arco orgánico de 3 metros con globos pastel, columnas laterales de globos metalizados, letras gigantes con el nombre de la festejada y centros de mesa para 12 mesas. Montaje desde las 8:00 en el Salón Aurora.",
];

export default function AutoHeightDemo() {
  const [open, setOpen] = useState(false);
  const { spring, reduced } = useMotionProfile();
  return (
    <>
      <Example title="Contenedor que anima su altura al cambiar el contenido">
        <div className="max-w-md rounded-xl border border-input bg-card text-card-foreground">
          <AutoHeight transition={reduced ? { duration: 0 } : spring} deps={[open]}>
            <div className="p-4">
              <h3 className="text-sm font-semibold">Evento: XV años de Valentina</h3>
              <p className="mt-2 text-sm text-muted-foreground">{detalles[open ? 1 : 0]}</p>
              <button onClick={() => setOpen(!open)} aria-expanded={open} className="mt-3 rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground">
                {open ? "Ver menos" : "Ver más"}
              </button>
            </div>
          </AutoHeight>
        </div>
      </Example>
    </>
  );
}
