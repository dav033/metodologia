import Magnet from "@/components/react-bits/Magnet";
import { Example, Row } from "@kit/demo";

export default function MagnetDemo() {
  return (
    <>
      <Example title="Los elementos se acercan al cursor">
        <Row className="gap-10 p-6">
          <Magnet padding={80} magnetStrength={3}>
            <button type="button" className="rounded-lg bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground">Cotizar evento</button>
          </Magnet>
          <Magnet padding={80} magnetStrength={4} axis="x" scale={1.1}>
            <button type="button" className="rounded-lg border border-input bg-background px-5 py-2.5 text-sm font-medium">Ver galería</button>
          </Magnet>
          <Magnet padding={60} tilt={12}>
            <span className="inline-flex size-14 items-center justify-center rounded-full bg-secondary text-lg font-semibold text-secondary-foreground">12</span>
          </Magnet>
        </Row>
      </Example>
      <Example title="Desactivado">
        <Row className="p-6"><Magnet disabled><button type="button" className="rounded-lg bg-muted px-5 py-2.5 text-sm font-medium text-muted-foreground">Sin imán</button></Magnet></Row>
      </Example>
    </>
  );
}
