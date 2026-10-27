import ScrollStack, { ScrollStackItem } from "@/components/react-bits/ScrollStack";
import { Example } from "@kit/demo";
import { useMotionProfile } from "@kit/motion";

const pasos = [
  ["1 · Cotización", "Elegimos paleta, tamaños y cantidad de globos según el salón y el presupuesto."],
  ["2 · Diseño", "Boceto del arco, columnas y centros de mesa; aprobación del cliente."],
  ["3 · Producción", "Inflado, amarre y armado de estructuras en el taller."],
  ["4 · Montaje", "Instalación en el salón dos horas antes del evento."],
];

export default function ScrollStackDemo() {
  const { reduced } = useMotionProfile();
  return (
    <>
      <Example title="Tarjetas que se apilan al desplazar (scroll dentro del recuadro)">
        <div className="h-[28rem] overflow-hidden rounded-xl border border-input bg-background">
          <ScrollStack itemDistance={60} itemStackDistance={20} stackPosition="12%" baseScale={0.85} smoothScroll={!reduced}>
            {pasos.map(([t, d]) => (
              <ScrollStackItem key={t}>
                <h3 className="text-2xl font-semibold">{t}</h3>
                <p className="mt-3 max-w-md text-base opacity-80">{d}</p>
              </ScrollStackItem>
            ))}
          </ScrollStack>
        </div>
      </Example>
    </>
  );
}
