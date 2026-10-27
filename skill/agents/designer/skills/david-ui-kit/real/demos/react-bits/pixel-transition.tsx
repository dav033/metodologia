import PixelTransition from "@/components/react-bits/PixelTransition";
import { Example, Row, picture } from "@kit/demo";

const front = (label: string, hue: number) => (
  <img src={picture(label, hue, 480, 320)} alt={label} className="size-full object-cover" />
);
const back = (title: string, text: string) => (
  <div className="flex size-full flex-col justify-center gap-2 bg-card p-6 text-card-foreground">
    <h3 className="text-xl font-semibold">{title}</h3>
    <p className="text-sm text-muted-foreground">{text}</p>
  </div>
);

export default function PixelTransitionDemo() {
  return (
    <>
      <Example title="Cambia por píxeles al pasar el cursor (o con clic)">
        <Row className="items-start gap-6">
          <div className="w-72">
            <PixelTransition firstContent={front("Arco orgánico", 280)} secondContent={back("Arco orgánico", "320 globos · 2 horas de montaje")}
              pixelColor="#7a2ee0" gridSize={10} aspectRatio="3/2" className="overflow-hidden rounded-xl border border-input" />
          </div>
          <div className="w-72">
            <PixelTransition firstContent={front("Boda Jazmín", 330)} secondContent={back("Boda Jazmín", "120 invitados · jardín")}
              trigger="click" pattern="ripple" pixelShape="circle" pixelColor="#b4237f" gridSize={12} aspectRatio="3/2"
              className="overflow-hidden rounded-xl border border-input" />
          </div>
        </Row>
        <p className="mt-3 text-sm text-muted-foreground">La segunda tarjeta cambia con clic (también se activa con teclado si tiene foco).</p>
      </Example>
    </>
  );
}
