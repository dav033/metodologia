// Heavy effects (WebGL/canvas backgrounds, pointer physics): mounted only while on screen and the tab is visible, and
// replaced by a static fallback under reduced motion. Wrap every React Bits background and continuous effect in it.
import * as React from "react";
import { useMotionProfile } from "./motion";

export function Effect({ fallback, children, className, style }: {
  fallback: React.ReactNode; children: React.ReactNode; className?: string; style?: React.CSSProperties;
}) {
  const { reduced } = useMotionProfile();
  const ref = React.useRef<HTMLDivElement>(null);
  const [visible, setVisible] = React.useState(false);
  const [shown, setShown] = React.useState(() => typeof document === "undefined" || !document.hidden);
  React.useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(([e]) => setVisible(e.isIntersecting), { rootMargin: "120px" });
    io.observe(el);
    const vis = () => setShown(!document.hidden);
    document.addEventListener("visibilitychange", vis);
    return () => { io.disconnect(); document.removeEventListener("visibilitychange", vis); };
  }, []);
  const live = visible && shown && !reduced;
  return (
    <div ref={ref} className={className} style={{ position: "relative", ...style }} data-effect={live ? "live" : "still"}>
      {live ? children : fallback}
    </div>
  );
}
