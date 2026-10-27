import TextType from "@/components/react-bits/TextType";
import { Example } from "@kit/demo";
import { useMotionProfile } from "@kit/motion";

export default function TextTypeDemo() {
  const { reduced } = useMotionProfile();
  return (
    <>
      <Example title="Frases en bucle con cursor">
        {reduced ? <p className="text-3xl font-semibold">Cumpleaños infantiles · Bodas y aniversarios · Eventos corporativos</p> :
          <TextType text={["Cumpleaños infantiles", "Bodas y aniversarios", "Eventos corporativos"]} typingSpeed={60}
            pauseDuration={1400} loop cursorStyle="bar" className="text-3xl font-semibold" />}
      </Example>
      <Example title="Con prefijo y colores por frase">
        {reduced ? <p className="font-mono text-xl">Estado: Entregado · En montaje · Pendiente de pago</p> :
        <TextType text={["Entregado", "En montaje", "Pendiente de pago"]} prefix="Estado: " loop
          textColors={["var(--success)", "var(--primary)", "var(--destructive)"]} cursorStyle="block"
          className="font-mono text-xl" />}
      </Example>
      <Example title="Una sola frase, borrado con errores de tecleo">
        {reduced ? <p className="text-xl text-muted-foreground">Tu evento, sin estrés.</p> :
          <TextType text="Tu evento, sin estrés." loop={false} mistakes={1} typeEffect="rise" cursorStyle="underscore"
            className="text-xl text-muted-foreground" />}
      </Example>
    </>
  );
}
