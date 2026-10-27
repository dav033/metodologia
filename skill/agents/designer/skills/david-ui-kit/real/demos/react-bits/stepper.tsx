import * as React from "react";
import Stepper, { Step } from "@/components/react-bits/Stepper";
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

export default function StepperDemo() {
  const dark = useDark();
  const theme = dark ? "dark" : "light";
  const accent = dark ? "#cba6f7" : "#7a2ee0";
  return (
    <>
      <Example title="Asistente de cotización (horizontal, con números)">
        <Stepper theme={theme} accentColor={accent} frame width="100%" nextButtonText="Siguiente" backButtonText="Atrás"
          completeButtonText="Enviar cotización" completedContent={<p className="p-6 text-center font-medium">Cotización enviada. Te escribiremos hoy.</p>}>
          <Step title="Evento"><p className="text-sm">Cumpleaños infantil · 14 de noviembre · Salón Aurora</p></Step>
          <Step title="Decoración"><p className="text-sm">Arco orgánico de 320 globos en paleta lila y menta.</p></Step>
          <Step title="Contacto"><p className="text-sm">Camila Reyes · camila@correo.com · 300 555 0142</p></Step>
        </Stepper>
      </Example>
      <Example title="Vertical, indicador en puntos, sin transición, lineal">
        <Stepper theme={theme} accentColor={accent} frame orientation="vertical" indicator="dots" transition="none" linear width="100%" nextButtonText="Continuar" backButtonText="Atrás" completeButtonText="Finalizar">
          <Step title="Pedido recibido"><p className="text-sm">Confirmamos fecha y salón.</p></Step>
          <Step title="En producción"><p className="text-sm">Armado en el taller.</p></Step>
          <Step title="Entregado"><p className="text-sm">Montaje finalizado.</p></Step>
        </Stepper>
      </Example>
    </>
  );
}
