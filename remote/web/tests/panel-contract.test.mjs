import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const pagePath = fileURLToPath(new URL("../src/app/page.tsx", import.meta.url));
const panelsPath = fileURLToPath(new URL("../src/app/recovery-panels.tsx", import.meta.url));

test("reopened ready tasks keep recovery controls and send the authoritative state", async () => {
  const page = await readFile(pagePath, "utf8");

  assert.match(page, /commandType === "reopen"[\s\S]*?reopenedTasks\.current\.add/);
  assert.match(page, /reopenedTasks\.current\.has\(key\) && \["ready", "recovering"\]\.includes\(task\.state\)[\s\S]*?reopenedForRecovery: true/);
  assert.match(page, /const canRecover = task\.state === "recovering" \|\| task\.reopenedForRecovery === true/);
  assert.match(page, /\{canRecover && <RoutesPanel/);
  assert.match(page, /\{canRecover && <form className="recovery-form" onSubmit=\{editBriefForm/);
  assert.match(page, /precondition: \{ state: task\.state/);
  assert.match(page, /task\.state === "rejected"[\s\S]*?Reabrir/);
});

test("recovery entrypoint previews the next revision and renders each account quota window", async () => {
  const [page, panels] = await Promise.all([readFile(pagePath, "utf8"), readFile(panelsPath, "utf8")]);

  assert.match(page, /const nextRevision = \(plan\?\.revision \?\? run\.revision \?\? 0\) \+ 1/);
  assert.match(page, /Creará la revisión \{nextRevision\}\./);
  assert.match(panels, /Object\.entries\(account\.windows\)\.map/);
  assert.match(panels, /windowLabel\(name\)/);
  assert.match(panels, /Cuotas en vivo/);
});
