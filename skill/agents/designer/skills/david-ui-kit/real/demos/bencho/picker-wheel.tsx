import { Picker } from "@/components/bencho/picker/Picker";
import "@/components/bencho/picker/Picker.css";
import { Example } from "@kit/demo";

export default function PickerWheelDemo() {
  return (
    <>
      <Example title="Selector de asignados (en el catálogo se llama Picker Wheel; el bloque publicado es Assignees)">
        <div className="bencho flex justify-center p-6"><Picker /></div>
      </Example>
      <Example title="Disposición en cuadrícula">
        <div className="bencho flex justify-center p-6"><Picker stack="Grid" overlap={14} /></div>
      </Example>
    </>
  );
}
