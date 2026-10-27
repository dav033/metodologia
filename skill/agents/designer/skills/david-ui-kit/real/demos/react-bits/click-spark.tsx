import * as React from "react";
import ClickSpark from "@/components/react-bits/ClickSpark";
import { Example } from "@kit/demo";

function useDark() {
  const [d, setD] = React.useState(() => document.documentElement.classList.contains("dark"));
  React.useEffect(() => {
    const o = new MutationObserver(() => setD(document.documentElement.classList.contains("dark")));
    o.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
    return () => o.disconnect();
  }, []);
  return d;
}

export default function ClickSparkDemo() {
  const dark = useDark();
  const c = dark ? ["#cba6f7", "#89b4fa", "#94e2d5"] : ["#7a2ee0", "#1858d8", "#13777d"];
  return (
    <>
      <Example title="Chispas al hacer clic en cualquier punto del recuadro">
        <ClickSpark sparkColor={c} sparkCount={10} sparkRadius={24}>
          <div className="flex h-56 items-center justify-center rounded-xl border border-input bg-card text-sm text-muted-foreground">
            Haz clic aquí para celebrar un pedido
          </div>
        </ClickSpark>
      </Example>
      <Example title="Estrellas con anillo">
        <ClickSpark sparkColor={dark ? "#f9a98b" : "#c2410c"} shape="star" ring sparkCount={8} gravity={0.2}>
          <div className="flex h-40 items-center justify-center rounded-xl border border-input bg-card text-sm text-muted-foreground">
            Clic para estrellas
          </div>
        </ClickSpark>
      </Example>
    </>
  );
}
