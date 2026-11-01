import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import type { Page } from "playwright";

let visualCaptureIndex = 0;

export async function captureVisual(page: Page, label: string): Promise<void> {
  const output = process.env.REQ021_EVIDENCE_DIR;
  if (!output) return;
  await mkdir(output, { recursive: true });
  const width = page.viewportSize()?.width ?? 0;
  const lang = await page.locator("html").getAttribute("lang").catch(() => "unknown");
  visualCaptureIndex += 1;
  const name = `${String(visualCaptureIndex).padStart(3, "0")}-${label}-${width}-${lang}`;
  const metadata = await page.evaluate(() => ({
    documentLang: document.documentElement.lang,
    mainLang: document.querySelector("main")?.getAttribute("lang") ?? null,
    headerLang: document.querySelector("header")?.getAttribute("lang") ?? null,
    accountPopupLang: document.querySelector("[aria-label=Account], [aria-label=Cuenta]")?.getAttribute("lang") ?? null,
    path: location.pathname,
    viewport: { width: window.innerWidth, height: window.innerHeight },
  }));
  await writeFile(path.join(output, `${name}.json`), JSON.stringify(metadata, null, 2));
  await page.screenshot({ path: path.join(output, `${name}.png`), fullPage: true, animations: "disabled" });
}
