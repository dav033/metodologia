// The planning-mockup shell for real components: renders the planning bar with the native selects the plan page drives
// (ids view, state, scene, theme; labels Vista, Estado, Diálogo, Tema; plus Movimiento) OUTSIDE the product root, and
// gives the product the current values through useMockup(). The selects stay plain DOM so assets/mockup-bridge.js and
// kit/audit_mockup.py can set them (value + change event) exactly as they do on hand-written mockups.
import * as React from "react";
import { createRoot } from "react-dom/client";
import { flushSync } from "react-dom";
import { MotionProfile, prefersReduced, type Profile } from "./motion";

export type Option = { id: string; label: string };
export type MockupConfig = {
  title: string;                 // product screen name, shown in the bar
  views: Option[];
  states: Option[];
  scenes?: Option[];             // dialogs/sheets; the first option should be { id: "", label: "Ninguno" }
  motion?: Profile;              // starting profile; mockups default to expressive
};
export type MockupState = { view: string; state: string; scene: string; theme: "light" | "dark"; motion: Profile; reduced: boolean };

const Ctx = React.createContext<MockupState & { set: (k: "view" | "state" | "scene", v: string) => void }>(null as never);

/** The current view/state/scene/theme/motion, and `set` to move between them from inside the product (e.g. a button
 *  that opens a dialog sets scene). */
export function useMockup() {
  return React.useContext(Ctx);
}

/** Shows children only on the given views/states/scenes (any omitted axis matches everything). */
export function Show({ view, state, scene, children }: { view?: string | string[]; state?: string | string[]; scene?: string | string[]; children: React.ReactNode }) {
  const m = useMockup();
  const hit = (want: string | string[] | undefined, cur: string) => want === undefined || (Array.isArray(want) ? want.includes(cur) : want === cur);
  return hit(view, m.view) && hit(state, m.state) && hit(scene, m.scene) ? <>{children}</> : null;
}

const THEMES: Option[] = [{ id: "light", label: "Claro" }, { id: "dark", label: "Oscuro" }];
const MOTIONS: Option[] = [{ id: "expressive", label: "Expresivo" }, { id: "natural", label: "Natural" }, { id: "subtle", label: "Sutil" }, { id: "still", label: "Quieto" }];

function bar(cfg: MockupConfig): HTMLElement {
  const header = document.createElement("header");
  header.className = "mockup-bar";
  header.setAttribute("data-mockup-chrome", "");
  const tag = document.createElement("strong");
  tag.textContent = `Mockup · ${cfg.title}`;
  header.append(tag);
  const add = (id: string, label: string, opts: Option[], first?: string) => {
    if (!opts.length) return;
    const wrap = document.createElement("label");
    wrap.htmlFor = id;
    const span = document.createElement("span");
    span.textContent = label;
    const sel = document.createElement("select");
    sel.id = id;
    for (const o of opts) sel.add(new Option(o.label, o.id));
    if (first) sel.value = first;
    wrap.append(span, sel);
    header.append(wrap);
  };
  add("view", "Vista", cfg.views);
  add("state", "Estado", cfg.states);
  add("scene", "Diálogo", cfg.scenes || []);
  add("theme", "Tema", THEMES);
  add("motion", "Movimiento", MOTIONS, prefersReduced() ? "still" : cfg.motion || "expressive");
  return header;
}

const BAR_CSS = `.mockup-bar{position:sticky;top:0;z-index:60;display:flex;flex-wrap:wrap;align-items:center;gap:8px 16px;padding:8px 16px;
background:#11111b;color:#cdd6f4;font:500 12px/1.4 ui-sans-serif,system-ui,sans-serif;border-bottom:1px solid #45475a}
.mockup-bar strong{margin-right:auto;font-weight:600}.mockup-bar label{display:inline-flex;align-items:center;gap:6px}
.mockup-bar select{font:inherit;color:#cdd6f4;background:#1e1e2e;border:1px solid #8a8fa8;border-radius:6px;padding:3px 6px}
.mockup-bar select:focus-visible{outline:2px solid #cba6f7;outline-offset:2px}
#app{position:relative;min-height:calc(100svh - var(--mockup-bar-h,0px))}
#app [data-slot="sidebar-container"]{top:var(--mockup-bar-h,0px);height:calc(100svh - var(--mockup-bar-h,0px))}`;

function read(): MockupState {
  const v = (id: string) => (document.getElementById(id) as HTMLSelectElement | null)?.value ?? "";
  const motion = v("motion") || "expressive";
  const theme = v("theme") === "dark" ? "dark" : "light";
  return { view: v("view"), state: v("state"), scene: v("scene"), theme, motion: (motion === "still" ? "natural" : motion) as Profile,
           reduced: motion === "still" || prefersReduced() };
}

function Root({ App }: { App: React.ComponentType }) {
  const [s, setS] = React.useState<MockupState>(read);
  React.useEffect(() => {
    const on = (e: Event) => { if ((e.target as HTMLElement)?.closest?.(".mockup-bar")) setS(read()); };
    const message = (ev: MessageEvent<unknown>) => {
      const d = ev.data;
      if (ev.source !== parent || typeof d !== "object" || d === null || !("kit" in d) || d.kit !== "set") return;
      const theme = document.getElementById("theme") as HTMLSelectElement | null;
      const motion = document.getElementById("motion") as HTMLSelectElement | null;
      if (theme && "theme" in d && typeof d.theme === "string" && ["light", "dark"].includes(d.theme)) theme.value = d.theme;
      if (motion) {
        if ("reduced" in d && d.reduced === true) motion.value = "still";
        else if ("motion" in d && typeof d.motion === "string" && ["subtle", "natural", "expressive"].includes(d.motion)) motion.value = d.motion;
      }
      setS(read());
    };
    document.addEventListener("change", on, true);
    document.addEventListener("input", on, true);
    window.addEventListener("message", message);
    const media = matchMedia("(prefers-reduced-motion: reduce)");
    const preference = () => setS(read());
    media.addEventListener("change", preference);
    return () => {
      document.removeEventListener("change", on, true); document.removeEventListener("input", on, true);
      window.removeEventListener("message", message);
      media.removeEventListener("change", preference);
    };
  }, []);
  React.useLayoutEffect(() => {
    const root = document.documentElement;
    root.classList.toggle("dark", s.theme === "dark");
    root.dataset.theme = s.theme;
    if (s.reduced) {
      // skipAnimations affects future Motion starts. Finish existing WAAPI/CSS effects too, without remounting
      // the product (which would erase its selected event/filter when the owner switches to Quieto).
      const settle = () => {
        for (const animation of document.getAnimations()) {
          if (animation.playbackRate !== 0 && Number.isFinite(animation.effect?.getComputedTiming().endTime)) animation.finish();
          else animation.cancel();
        }
      };
      settle();
      // Motion may attach a replacement WAAPI animation in its next frame after the context update.
      // Cover those two render phases without a persistent timer or resetting product state.
      let next = 0;
      const first = requestAnimationFrame(() => { settle(); next = requestAnimationFrame(settle); });
      return () => { cancelAnimationFrame(first); cancelAnimationFrame(next); };
    }
  }, [s.theme, s.reduced]);
  const set = React.useCallback((k: "view" | "state" | "scene", v: string) => {
    const sel = document.getElementById(k) as HTMLSelectElement | null;
    if (sel && [...sel.options].some((o) => o.value === v)) { sel.value = v; sel.dispatchEvent(new Event("change", { bubbles: true })); }
  }, []);
  return (
    <Ctx.Provider value={{ ...s, set }}>
      <MotionProfile profile={s.motion} reduced={s.reduced}>
        <App key={`${s.view}|${s.state}`} />
      </MotionProfile>
    </Ctx.Provider>
  );
}

/** Mount a mockup: `mountMockup(App, { title, views, states, scenes })` at the end of the entry file. */
export function mountMockup(App: React.ComponentType, cfg: MockupConfig): void {
  const style = document.createElement("style");
  style.textContent = BAR_CSS;
  document.head.append(style);
  document.body.prepend(bar(cfg));
  const query = new URLSearchParams(location.search);
  for (const id of ["theme", "motion"]) {
    const sel = document.getElementById(id) as HTMLSelectElement;
    const value = query.get(id);
    if (value && [...sel.options].some(o => o.value === value)) sel.value = value;
  }
  if (query.get("rm") === "1" || prefersReduced()) (document.getElementById("motion") as HTMLSelectElement).value = "still";
  let main = document.getElementById("app");
  if (!main) {
    main = document.createElement("main");
    main.id = "app";
    document.body.append(main);
  }
  // the product lives below the sticky bar: shadcn's Sidebar is `fixed inset-y-0`, so it is moved down by the bar's
  // height (CSS above) instead of hiding behind it; dialogs, menus and toasts keep the whole viewport
  const barH = Math.ceil(document.querySelector<HTMLElement>(".mockup-bar")?.getBoundingClientRect().height || 0);
  document.documentElement.style.setProperty("--mockup-bar-h", `${barH}px`);
  new ResizeObserver(([entry]) => {
    document.documentElement.style.setProperty("--mockup-bar-h", `${Math.ceil(entry.target.getBoundingClientRect().height)}px`);
  }).observe(document.querySelector(".mockup-bar")!);
  const root = createRoot(main);
  flushSync(() => root.render(<Root App={App} />));   // rendered before DOMContentLoaded: the bridge sees the product
}
