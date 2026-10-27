import { ToastStack } from "@/components/bencho/toast-stack/ToastStack";
import "@/components/bencho/toast-stack/ToastStack.css";
import { Example } from "@kit/demo";

export default function ToastStackDemo() {
  return (
    <>
      <Example title="Pila de avisos: pasar el cursor o enfocar los despliega">
        <div className="bencho flex justify-center p-6"><ToastStack /></div>
      </Example>
      <Example title="Separación amplia y esquinas rectas">
        <div className="bencho flex justify-center p-6"><ToastStack peek={20} gap={18} corner={8} /></div>
      </Example>
    </>
  );
}
