import SplitText from "@/components/react-bits/SplitText";
import { Example } from "@kit/demo";
import { useMotionProfile } from "@kit/motion";

export default function SplitTextDemo() {
  const { reduced } = useMotionProfile();
  return (
    <>
      <Example title="Por letras al entrar en pantalla">
        <SplitText text="Cada globo cuenta una historia" tag="h2" splitType="chars" delay={30} duration={0.8}
          className="text-4xl font-bold" textAlign="left" />
      </Example>
      <Example title="Por palabras con máscara, desde el centro">
        <SplitText text="Montaje completo en tres horas" tag="p" splitType="words" mask staggerFrom="center" delay={80}
          className="text-2xl font-medium" textAlign="left" />
      </Example>
      <Example title="Con realce al pasar el cursor y acento">
        <SplitText text="Pasa el cursor por el texto" tag="p" splitType="chars" hoverEffect="wave" trigger="load"
          loop={!reduced} loopDelay={3} accentColor="var(--primary)" className="text-xl text-muted-foreground" textAlign="left" />
      </Example>
    </>
  );
}
