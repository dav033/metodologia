import assert from "node:assert/strict";
import { once } from "node:events";
import { after, before, test } from "node:test";
import { createMockGatewayServer } from "../mocks/gateway.mjs";

let server;
let origin;

before(async () => {
  server = await createMockGatewayServer();
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  const address = server.address();
  assert.ok(address && typeof address !== "string");
  origin = `http://127.0.0.1:${address.port}`;
});

after(async () => {
  if (!server?.listening) return;
  server.close();
  await once(server, "close");
});

test("mock gateway returns the v1 snapshot and session contracts consumed by the panel", async () => {
  const session = await fetch(`${origin}/api/auth/session`);
  assert.deepEqual(await session.json(), { login: "owner" });

  const response = await fetch(`${origin}/api/remote/v1/snapshot`);
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /application\/json/);

  const body = await response.json();
  assert.equal(body.schemaVersion, 1);
  assert.equal(body.cursor, "");
  assert.deepEqual(body.runs.map((run) => run.reqId), ["REQ-027", "REQ-018"]);
  assert.equal(body.runs[0].lastSignOfLife, "2026-10-19T11:59:45Z");
  assert.equal(body.plans[0].planStatus, "review");
  assert.equal(body.plans[0].rounds[0].questions.length, 2);
  assert.match(body.plans[1].decisions[0].options[0].consequence, /Gasta un intento/);
  const events = await fetch(`${origin}/api/remote/v1/events`);
  const eventBody = await events.text();
  assert.match(events.headers.get("content-type") ?? "", /text\/event-stream/);
  assert.match(eventBody, /event: flow/);
  assert.match(eventBody, /"target":\{"run":"lotm\/REQ-027","task":"T15a"\}/);
  const history = await fetch(`${origin}/api/remote/v1/commands?after=&limit=100`);
  assert.equal((await history.json()).commands[0].origin, "telegram");

  const review = await fetch(`${origin}/api/remote/v1/attempts/att-failed-02/review`);
  const reviewBody = await review.json();
  assert.equal(reviewBody.attemptId, "att-failed-02");
  assert.equal(reviewBody.diff.files.length, 2);
  assert.equal(reviewBody.logTail.split("\n").length, 240);
});

test("mock gateway accepts versioned, idempotent control commands", async () => {
  const response = await fetch(`${origin}/api/remote/v1/commands`, {
    method: "POST", headers: { "content-type": "application/json", "x-flow-request": "1" },
    body: JSON.stringify({ schemaVersion: 1, idempotencyKey: "test-idempotency-key", type: "cancel-attempt", target: { kind: "attempt", project: "lotm", req: "REQ-027", attemptId: "att-0008" }, precondition: { state: "running" }, reason: "Stalled" }),
  });
  assert.equal(response.status, 202);
  assert.equal((await response.json()).idempotencyKey, "test-idempotency-key");
});

test("mock gateway refuses state-changing requests without the CSRF marker, like the real gateway", async () => {
  const response = await fetch(`${origin}/api/remote/v1/commands`, { method: "POST", headers: { "content-type": "application/json" }, body: "{}" });
  assert.equal(response.status, 403);
});
