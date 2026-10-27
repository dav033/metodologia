import { Checklist } from "@/components/bencho/checklist/Checklist";
import "@/components/bencho/checklist/Checklist.css";
import { Example } from "@kit/demo";

export default function ChecklistDemo() {
  return (
    <>
      <Example title="Lista de tareas: marcar tacha el texto">
        <div className="bencho flex justify-center p-6"><Checklist /></div>
      </Example>
      <Example title="Casillas grandes con más rebote">
        <div className="bencho flex justify-center p-6"><Checklist box={26} bounce={85} corner={12} /></div>
      </Example>
    </>
  );
}
