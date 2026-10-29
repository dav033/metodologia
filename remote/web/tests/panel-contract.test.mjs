import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const pagePath = fileURLToPath(new URL("../src/app/page.tsx", import.meta.url));
const panelsPath = fileURLToPath(new URL("../src/app/recovery-panels.tsx", import.meta.url));

test("reopened ready tasks keep recovery controls and send the authoritative state", async () => {
  const page = await readFile(pagePath, "utf8");

  assert.match(page, /commandType === "reopen"[\s\S]*?reopenedTasks\.current\.add/);
  // The snapshot speaks plan-status states: M1 `recovering` arrives as `rejected` (SNAPSHOT_TASK_STATES).
  assert.match(page, /reopenedTasks\.current\.has\(key\) && \["ready", "rejected"\]\.includes\(task\.state\)[\s\S]*?reopenedForRecovery: true/);
  assert.match(page, /const canRecover = task\.reopenedForRecovery === true/);
  assert.match(page, /\{canRecover && <RoutesPanel/);
  assert.match(page, /\{canRecover && <form className="recovery-form" onSubmit=\{editBriefForm/);
  assert.match(page, /precondition: \{ state: task\.state, \.\.\.\(typeof task\.revision === "number" \? \{ revision: task\.revision \}/);
  assert.match(page, /commandForm\("reopen", \{ kind: "task"[^)]*\}, task\.state, task\.revision,/);
  assert.match(page, /reopenable\(task\.state\) && !task\.reopenedForRecovery \? <form onSubmit=\{commandForm\("reopen", \{ kind: "task"[\s\S]*?Reabrir/);
  assert.match(page, /REOPENABLE_TASK_STATES/);
});

test("recovery entrypoint previews the next revision and renders each account quota window", async () => {
  const [page, panels] = await Promise.all([readFile(pagePath, "utf8"), readFile(panelsPath, "utf8")]);

  assert.match(page, /const nextRevision = \(plan\?\.revision \?\? run\.revision \?\? 0\) \+ 1/);
  assert.match(page, /Creará la revisión \{nextRevision\}\./);
  // F41: windows are the producer's list (QuotaWindow[]), not an object keyed by name.
  assert.match(panels, /account\.windows\.map\(\(window\) =>/);
  assert.match(panels, /windowLabel\(window\.window\)/);
  assert.match(panels, /parseQuotas\(/);
  assert.match(panels, /Cuotas en vivo/);
});

test("failure review scopes attempt lookup to its run target", async () => {
  const [page, panel] = await Promise.all([
    readFile(pagePath, "utf8"),
    readFile(fileURLToPath(new URL("../src/app/failure-review-panel.tsx", import.meta.url)), "utf8"),
  ]);

  assert.match(page, /<FailureReviewPanel attemptId=\{reviewAttemptId\} target=\{`\$\{run\.project\}\/\$\{run\.req\}`\} \/>/);
  assert.match(panel, /review\?target=\$\{encodeURIComponent\(target\)\}/);
  assert.match(panel, /\}, \[attemptId, target\]\);/);
});

test("F4: the live feed uses the gateway's stream path and its named SSE frames", async () => {
  const page = await readFile(pagePath, "utf8");
  const { STREAM } = await import("../src/contract.generated.ts");
  assert.equal(STREAM.path, "/api/remote/v1/stream");
  assert.doesNotMatch(page, /events\/stream|\.onmessage/);
  assert.match(page, /new EventSource\(STREAM\.path\)/);
  assert.match(page, /addEventListener\(STREAM\.event,/);
  assert.match(page, /addEventListener\(STREAM\.resync,/);
});
