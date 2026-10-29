import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";
import { parseFailureReview, parseFlowEvent, parseQuotas, parseRoutes, parseSnapshot, runReopen } from "../src/app/remote-contract.ts";

// Producer-shaped fixtures; test_remote_contracts validates each one against the Pydantic contract.
const fixture = async (name) => JSON.parse(await readFile(new URL(`../../contract/fixtures/${name}.json`, import.meta.url), "utf8"));
const gatewaySnapshot = async () => ({ ...await fixture("snapshot"), laptop: { online: true }, online: true, cachedAt: 1792411200, lastEventId: "fixture:0" });

test("F41: the phone keeps every account and window the laptop quota endpoint returns", async () => {
  const parsed = parseQuotas(await fixture("quotas"));
  assert.equal(parsed.accounts.length, 1);
  assert.equal(parsed.accounts[0].account, "codex-work");
  assert.equal(parsed.accounts[0].observedAt, "2026-10-19T12:00:00+00:00");
  assert.deepEqual(parsed.accounts[0].windows.map((window) => [window.window, window.usedPercent, window.resetsAt]),
    [["five_hour", 27, "2026-10-19T13:00:00+00:00"], ["seven_day", 64, "2026-10-25T12:00:00+00:00"]]);
  assert.equal(parsed.checkedAt, "2026-10-19T12:00:00Z");
});

test("F21: run-level reopen names a reopenable task and uses that task's state as precondition", async () => {
  const snapshot = parseSnapshot(await gatewaySnapshot());
  const run = snapshot.runs.find((item) => item.req === "REQ-018");
  assert.deepEqual(runReopen({ ...run, state: "blocked" }), {
    target: { kind: "task", project: "pictures", req: "REQ-018", taskId: "T2" }, precondition: { state: "blocked" },
  });
  for (const state of ["running", "paused", "completed", "cancelled"]) assert.equal(runReopen({ ...run, state }), null, state);
  assert.equal(runReopen({ ...run, state: "blocked", tasks: [] }), null, "a blocked run without a reopenable task offers nothing");
  // A durable run's task carries the projection sequence of its last change: the reopen pins it (stale views refused).
  const durable = { ...run, state: "blocked", tasks: run.tasks.map((task) => ({ ...task, revision: 41 })) };
  assert.deepEqual(runReopen(durable).precondition, { state: "blocked", revision: 41 });
});

test("snapshot parsing keeps the producer's activity times and review attempts", async () => {
  const snapshot = parseSnapshot(await gatewaySnapshot());
  const [run] = snapshot.runs;
  assert.equal(run.lastActivityAt, "2026-10-19T11:59:45Z");
  assert.equal(run.tasks[0].activeAttempt?.lastActivityAt, "2026-10-19T11:59:45Z");
  assert.equal(run.tasks[1].reviewAttempt?.id, "att-rejected-fixture");
  assert.equal(snapshot.laptop.online, true);
  assert.equal(snapshot.decisionRequests[0].options.length, 2);
  assert.equal(snapshot.rounds[0].questions[0].type, "choice");
});

test("feed events, routes and the failure review parse from the producer's dialect", async () => {
  const [failed, , quota] = await fixture("events");
  assert.equal(parseFlowEvent(failed)?.task, "T15a");
  assert.equal(parseFlowEvent(quota), null, "system events have no run row in the feed");
  const routes = parseRoutes(await fixture("routes"));
  assert.deepEqual(routes.map((route) => route.routeId), ["route-codex-work"]);
  const review = parseFailureReview(await fixture("review"));
  assert.equal(review.attemptId, "att-rejected-fixture");
  assert.doesNotMatch(review.cause, /ghp_/);
});
