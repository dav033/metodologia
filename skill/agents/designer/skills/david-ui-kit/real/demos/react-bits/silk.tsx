import Silk from "@/components/react-bits/Silk";
import { Effect } from "@kit/effect";
import { Example } from "@kit/demo";

export default function SilkDemo() {
  return (
    <Example title="Fondo de héroe (WebGL; estático con movimiento reducido o fuera de pantalla)">
      <Effect className="h-72 overflow-hidden rounded-xl"
        fallback={<div className="size-full bg-gradient-to-br from-primary/60 via-chart-2/40 to-chart-5/50" />}>
        <Silk color="#7a2ee0" speed={4} scale={1} />
      </Effect>
    </Example>
  );
}
