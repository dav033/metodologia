import TrueFocus from "@/components/react-bits/TrueFocus";
import { Example } from "@kit/demo";
import { useMotionProfile } from "@kit/motion";

export default function TrueFocusDemo() {
  const { reduced } = useMotionProfile();
  return (
    <>
      <Example title="Foco automático con esquinas">
        <div className="text-3xl font-semibold">
          <TrueFocus sentence="Globos Arcos Centros Columnas" focusStyle="brackets" borderColor="#7a2ee0" glowColor="#cba6f7"
            animationDuration={reduced ? 0 : 0.5} pauseBetweenAnimations={reduced ? 1e6 : 1.2} />
        </div>
      </Example>
      <Example title="Modo manual (pasa el cursor sobre cada palabra)">
        <div className="text-2xl font-medium">
          <TrueFocus sentence="Cotizar Reservar Montar Entregar" manualMode focusStyle="underline" borderColor="#1858d8" />
        </div>
      </Example>
      <Example title="Resaltado">
        <div className="text-2xl font-medium">
          <TrueFocus sentence="Pedido listo hoy" manualMode focusStyle="highlight" highlightColor="#13777d" borderColor="#13777d" />
        </div>
      </Example>
    </>
  );
}
