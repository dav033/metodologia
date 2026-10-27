// One gallery preview: renders a demo with the theme, motion profile and reduced-motion the gallery asks for (query on
// first load, postMessage afterwards) and reports its height. The frame is sandboxed: only postMessage crosses.
import * as React from "react";
import { createRoot } from "react-dom/client";
import { MotionProfile, type Profile } from "./motion";

type S = { theme: string; motion: Profile; reduced: boolean };

function initial(): S {
  const q = new URLSearchParams(location.search);
  const motion = (["subtle", "natural", "expressive"].includes(q.get("motion") || "") ? q.get("motion") : "natural") as Profile;
  let reduced = q.get("rm") === "1";
  try { reduced = reduced || matchMedia("(prefers-reduced-motion: reduce)").matches; } catch { /* old engine */ }
  return { theme: q.get("theme") === "dark" ? "dark" : "light", motion, reduced };
}

function Host({ Demo }: { Demo: React.ComponentType }) {
  const [s, setS] = React.useState<S>(initial);
  React.useEffect(() => {
    const on = (ev: MessageEvent) => {
      const d = ev.data;
      if (!d || d.kit !== "set" || ev.source !== parent) return;
      setS((cur) => ({ theme: d.theme === "dark" ? "dark" : d.theme === "light" ? "light" : cur.theme,
        motion: ["subtle", "natural", "expressive"].includes(d.motion) ? d.motion : cur.motion,
        reduced: typeof d.reduced === "boolean" ? d.reduced : cur.reduced }));
    };
    window.addEventListener("message", on);
    return () => window.removeEventListener("message", on);
  }, []);
  React.useLayoutEffect(() => {
    document.documentElement.classList.toggle("dark", s.theme === "dark");
    document.documentElement.dataset.theme = s.theme;
  }, [s.theme]);
  return (
    <MotionProfile profile={s.motion} reduced={s.reduced}>
      <div className="kit-frame">
        <Demo key={`${s.motion}|${s.reduced}`} />
      </div>
    </MotionProfile>
  );
}

function size() {
  try { parent.postMessage({ kit: "height", h: document.documentElement.scrollHeight }, "*"); } catch { /* no parent */ }
}

export function mountFrame(Demo: React.ComponentType): void {
  const el = document.getElementById("root") || document.body.appendChild(document.createElement("div"));
  createRoot(el).render(<Host Demo={Demo} />);
  if ("ResizeObserver" in window) new ResizeObserver(size).observe(document.body);
  window.addEventListener("load", size);
  setTimeout(size, 50);
  setTimeout(size, 600);
}
