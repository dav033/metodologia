import GlareHover from "@/components/react-bits/GlareHover";
import { Example, Row } from "@kit/demo";

export default function GlareHoverDemo() {
  return (
    <>
      <Example title="Destello que cruza al pasar el cursor">
        <Row className="gap-6">
          <GlareHover width="260px" height="160px" background="#7a2ee0" borderRadius="16px" glareColor="#ffffff" glareOpacity={0.4}>
            <div className="p-5 text-white"><p className="text-lg font-semibold">Salón Aurora</p><p className="text-sm">Capacidad 180</p></div>
          </GlareHover>
          <GlareHover width="260px" height="160px" background="#13777d" borderRadius="16px" glareColor="#ffffff" glareOpacity={0.35} glareAngle={-30}>
            <div className="p-5 text-white"><p className="text-lg font-semibold">Jardín Jazmín</p><p className="text-sm">Capacidad 120</p></div>
          </GlareHover>
        </Row>
      </Example>
    </>
  );
}
