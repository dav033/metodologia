import * as React from "react";
import { Button } from "@/components/ui/button";
import { Progress, ProgressLabel, ProgressValue } from "@/components/ui/progress";
import { useMotionProfile } from "@kit/motion";
import { Example, Row } from "@kit/demo";

export default function ProgressDemo() {
  const { reduced } = useMotionProfile();
  const [value, setValue] = React.useState(reduced ? 72 : 12);
  React.useEffect(() => {
    if (reduced) return;
    const t = setTimeout(() => setValue(72), 400);
    return () => clearTimeout(t);
  }, [reduced]);
  return (
    <>
      <Example title="Avance del montaje (anima entre valores)">
        <div className="flex max-w-md flex-col gap-4">
          <Progress value={value}>
            <ProgressLabel>Montaje del salón</ProgressLabel>
            <ProgressValue />
          </Progress>
          <Row>
            {[0, 25, 50, 100].map((v) => <Button key={v} size="sm" variant="outline" onClick={() => setValue(v)}>{v}%</Button>)}
          </Row>
        </div>
      </Example>
      <Example title="Valores fijos">
        <div className="flex max-w-md flex-col gap-4">
          <Progress value={30}><ProgressLabel>Globos inflados</ProgressLabel><ProgressValue /></Progress>
          <Progress value={100}><ProgressLabel>Pedido completado</ProgressLabel><ProgressValue /></Progress>
        </div>
      </Example>
      <Example title="Indeterminado">
        <div className="max-w-md"><Progress value={null}><ProgressLabel>Sincronizando inventario…</ProgressLabel></Progress></div>
      </Example>
    </>
  );
}
