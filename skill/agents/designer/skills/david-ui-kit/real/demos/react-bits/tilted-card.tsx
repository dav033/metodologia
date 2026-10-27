import TiltedCard from "@/components/react-bits/TiltedCard";
import { Example, Row, picture } from "@kit/demo";

export default function TiltedCardDemo() {
  return (
    <>
      <Example title="Tarjeta con inclinación 3D y brillo (mueve el cursor)">
        <Row className="gap-8">
          <TiltedCard imageSrc={picture("Salón Aurora", 280, 600, 400)} altText="Salón Aurora" captionText="Salón Aurora"
            containerHeight={300} containerWidth={300} imageHeight={300} imageWidth={300} rotateAmplitude={14} scaleOnHover={1.08}
            showTooltip glare={0.4}
            overlayContent={<p className="m-4 rounded-md bg-background/80 px-3 py-1 text-sm font-medium text-foreground">Salón Aurora</p>}
            displayOverlayContent />
          <TiltedCard imageSrc={picture("Arco orgánico", 200, 600, 400)} altText="Arco orgánico" containerHeight={300} containerWidth={300}
            imageHeight={300} imageWidth={300} flipOnClick rotateAmplitude={10}
            backContent={<div className="flex size-full flex-col justify-center gap-2 bg-card p-6 text-card-foreground">
              <h3 className="text-lg font-semibold">Arco orgánico</h3>
              <p className="text-sm text-muted-foreground">320 globos, tres paletas, montaje en 2 horas.</p>
            </div>} />
        </Row>
        <p className="mt-3 text-sm text-muted-foreground">La segunda tarjeta se voltea con clic o con Enter cuando tiene el foco.</p>
      </Example>
    </>
  );
}
