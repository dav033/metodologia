import { Counter } from "@/components/bencho/rolling-counter/Counter";
import "@/components/bencho/rolling-counter/Counter.css";
import { Example } from "@kit/demo";

export default function RollingNumberInputDemo() {
  return (
    <Example title="Contador editable: tocar, mantener o arrastrar (teclado: botones − y +)">
      <div className="bencho flex justify-center p-6"><Counter start={128} /></div>
    </Example>
  );
}
