import "@fontsource-variable/bricolage-grotesque/index.css";
import TextPressure from "@/components/react-bits/TextPressure";
import { Effect } from "@kit/effect";
import { Example } from "@kit/demo";

const FONT = "'Bricolage Grotesque Variable'";

export default function TextPressureDemo() {
  return (
    <>
      <Example title="El peso reacciona al cursor (fuente variable local)">
        <Effect className="h-48 overflow-hidden rounded-xl border border-input bg-background px-4"
          fallback={<div className="flex size-full items-center justify-center text-7xl font-extrabold">GLOBOS</div>}>
          <div className="mx-auto h-full w-1/2 min-w-72"><TextPressure text="GLOBOS" fontFamily={FONT} fontUrl="" textColor="var(--foreground)" minFontSize={48} italic={false} width={false} /></div>
        </Effect>
      </Example>
      <Example title="Con animación en reposo y color de presión">
        <Effect className="h-48 overflow-hidden rounded-xl border border-input bg-background px-4"
          fallback={<div className="flex size-full items-center justify-center text-6xl font-bold text-primary">Fiesta</div>}>
          <div className="mx-auto h-full w-1/2 min-w-72"><TextPressure text="Fiesta" fontFamily={FONT} fontUrl="" idle="wave" textColor="var(--foreground)"
            pressureColor="var(--primary)" italic={false} alpha={false} width={false} minFontSize={40} /></div>
        </Effect>
      </Example>
    </>
  );
}
