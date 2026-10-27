// Layout helpers for gallery demos only (not for mockups): a titled example block and a row of variants.
import * as React from "react";

export function Example({ title, children, className = "" }: { title: string; children: React.ReactNode; className?: string }) {
  return (
    <section className="flex min-w-0 flex-col gap-3">
      <h2 className="text-xs font-medium text-muted-foreground">{title}</h2>
      <div className={`min-w-0 ${className}`}>{children}</div>
    </section>
  );
}

export function Row({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <div className={`flex flex-wrap items-center gap-3 ${className}`}>{children}</div>;
}

/** A soft, data-URI image (no network) for demos that need pictures: a gradient with a label. */
export function picture(label: string, hue = 280, w = 640, h = 420): string {
  const svg = `<svg xmlns='http://www.w3.org/2000/svg' width='${w}' height='${h}' viewBox='0 0 ${w} ${h}'><defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='hsl(${hue} 70% 62%)'/><stop offset='1' stop-color='hsl(${(hue + 60) % 360} 70% 38%)'/></linearGradient></defs><rect width='100%' height='100%' fill='url(#g)'/><circle cx='${w * 0.72}' cy='${h * 0.32}' r='${h * 0.18}' fill='hsl(${(hue + 30) % 360} 90% 82% / .55)'/><text x='32' y='${h - 36}' font-family='system-ui,sans-serif' font-size='34' font-weight='700' fill='white'>${label}</text></svg>`;
  return "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
}
