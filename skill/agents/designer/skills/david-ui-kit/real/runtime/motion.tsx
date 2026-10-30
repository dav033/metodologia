// Motion profiles (david-ui SPEC R8) for the real components: one provider sets `data-motion` (CSS durations in
// theme.css), Motion's defaults (MotionConfig) and reduced motion. Components with their own fixed springs keep them;
// demos and mockups read `useMotionProfile()` to pass the profile's transition explicitly.
import * as React from "react";
import { MotionConfig, MotionGlobalConfig, type Transition } from "motion/react";

export type Profile = "subtle" | "natural" | "expressive";
export const PROFILES: Record<Profile, { spring: Transition; ease: Transition; stagger: number; distance: number }> = {
  subtle: { spring: { type: "spring", stiffness: 520, damping: 44, mass: 0.6 }, ease: { duration: 0.14, ease: [0.2, 0.8, 0.2, 1] }, stagger: 0.02, distance: 4 },
  natural: { spring: { type: "spring", stiffness: 340, damping: 30 }, ease: { duration: 0.22, ease: [0.2, 0.8, 0.2, 1] }, stagger: 0.05, distance: 10 },
  expressive: { spring: { type: "spring", stiffness: 220, damping: 16, mass: 0.9 }, ease: { duration: 0.42, ease: [0.34, 1.4, 0.64, 1] }, stagger: 0.09, distance: 22 },
};

type Ctx = { profile: Profile; reduced: boolean } & (typeof PROFILES)[Profile];
const MotionCtx = React.createContext<Ctx>({ profile: "natural", reduced: false, ...PROFILES.natural });

export function useMotionProfile(): Ctx {
  return React.useContext(MotionCtx);
}

export function prefersReduced(): boolean {
  try {
    return matchMedia("(prefers-reduced-motion: reduce)").matches || /[?&]still=1\b/.test(location.search);
  } catch {
    return false;
  }
}

export function MotionProfile({ profile, reduced, children }: { profile: Profile; reduced: boolean; children: React.ReactNode }) {
  const p = PROFILES[profile] ? profile : "natural";
  // Motion's own reduced mode still fades opacity and components pass explicit transitions; reduced motion here means
  // every Motion animation jumps to its end (the audit measures that settled state)
  MotionGlobalConfig.skipAnimations = reduced;
  React.useLayoutEffect(() => {
    const root = document.documentElement;
    root.dataset.motion = p;
    if (reduced) root.setAttribute("data-reduced-motion", "");
    else root.removeAttribute("data-reduced-motion");
  }, [p, reduced]);
  const value = React.useMemo(() => ({ profile: p, reduced, ...PROFILES[p] }), [p, reduced]);
  return (
    <MotionCtx.Provider value={value}>
      <MotionConfig transition={reduced ? { duration: 0 } : PROFILES[p].spring} reducedMotion={reduced ? "always" : "user"}>
        {children}
      </MotionConfig>
    </MotionCtx.Provider>
  );
}

/** Entrance props for a `motion.*` element: rises in with the profile's spring, `i` staggers it; under reduced motion it
 *  starts at its end state (Motion's own reduced mode still fades opacity, which the audit counts as motion).
 *  The reduced target is written as one-frame keyframes on purpose: Motion only animates a value whose target changed,
 *  and skipAnimations only applies to animations that start after it is set. With the same scalars, switching to
 *  reduced mid-entrance left the staggered springs running in Motion's transform compositor, which rebuilt the WAAPI
 *  animation every time the mockup's settle finished it (test_real_designer_kit, 2026-10-29: three springs still
 *  running 60 ms after "Quieto"). `[0]` differs from `0`, so each value restarts as an instant jump that stops its spring. */
export function useReveal() {
  const { reduced, spring, stagger, distance } = useMotionProfile();
  return (i = 0, from: { x?: number; y?: number; scale?: number } = { y: 1 }) =>
    reduced ? { initial: false as const, animate: { opacity: [1], x: [0], y: [0], scale: [1] } } : {
      initial: { opacity: 0, x: (from.x ?? 0) * distance, y: (from.y ?? 0) * distance, scale: from.scale ?? 1 },
      animate: { opacity: 1, x: 0, y: 0, scale: 1 },
      transition: { ...spring, delay: i * stagger },
    };
}
