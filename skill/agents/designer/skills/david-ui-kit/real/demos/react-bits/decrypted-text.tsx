import DecryptedText from "@/components/react-bits/DecryptedText";
import { Example } from "@kit/demo";

export default function DecryptedTextDemo() {
  return (
    <>
      <Example title="Se descifra al entrar en pantalla">
        <DecryptedText text="Pedido #2048 · Salón Aurora · 14 de noviembre" animateOn="view" sequential revealDirection="start"
          speed={40} className="text-xl font-medium" encryptedClassName="text-muted-foreground" />
      </Example>
      <Example title="Al pasar el cursor, solo caracteres originales">
        <DecryptedText text="Arco orgánico de 320 globos" animateOn="hover" useOriginalCharsOnly speed={50}
          maxIterations={12} className="text-lg" encryptedClassName="text-muted-foreground" />
      </Example>
      <Example title="Clic para alternar, efecto de volteo">
        <DecryptedText text="Haz clic para revelar el total: $1.480.000" animateOn="click" clickMode="toggle" effect="flip"
          scrambleColor="var(--primary)" className="text-lg" />
      </Example>
    </>
  );
}
