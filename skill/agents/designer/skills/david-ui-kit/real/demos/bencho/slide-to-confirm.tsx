import { SlideConfirm } from "@/components/bencho/slide-confirm/SlideConfirm";
import "@/components/bencho/slide-confirm/SlideConfirm.css";
import { Example } from "@kit/demo";

export default function SlideToConfirmDemo() {
  return (
    <>
      <Example title="Deslizar para confirmar (teclado: foco en el control)">
        <div className="bencho flex justify-center p-6"><SlideConfirm /></div>
      </Example>
      <Example title="Pista ancha, esquina reducida">
        <div className="bencho flex justify-center p-6"><SlideConfirm width={360} corner={12} /></div>
      </Example>
    </>
  );
}
