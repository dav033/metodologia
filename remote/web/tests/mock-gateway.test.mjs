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
  assert.deepEqual(await session.json(), { authenticated: true });

  const response = await fetch(`${origin}/api/remote/v1/snapshot`);
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /application\/json/);

  const body = await response.json();
  assert.equal(body.schemaVersion, 1);
  assert.equal(body.cursor, "mock-cursor-v1");
  assert.deepEqual(body.runs.map((run) => run.req_id), ["REQ-027", "REQ-018"]);
  assert.equal(body.runs[0].last_sign_of_life, "2026-10-19T11:59:45Z");
  assert.equal(body.plans[0].acceptance_criteria[0], "Owner reviews and approves the plan");
  const events = await fetch(`${origin}/api/remote/v1/events?after=&limit=100`);
  const eventBody = await events.json();
  assert.equal(eventBody.events[0].target.run, "lotm/REQ-027");
  assert.equal(eventBody.events[0].target.task, "T15a");
  assert.equal(eventBody.nextCursor, "mock-event-cursor-2");

  const review = await fetch(`${origin}/api/remote/v1/attempts/att-failed-02/review`);
  const reviewBody = await review.json();
  assert.equal(reviewBody.attemptId, "att-failed-02");
  assert.equal(reviewBody.diff.files.length, 2);
  assert.equal(reviewBody.logTail.split("\n").length, 240);
});

test("mock gateway accepts versioned, idempotent control commands", async () => {
  const response = await fetch(`${origin}/api/remote/v1/commands`, {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ idempotency_key: "test-idempotency-key", command: "cancel-attempt", target: "lotm/REQ-027", origin: "web", precondition: { state: "running" }, params: { attempt: "att-0008" } }),
  });
  assert.equal(response.status, 200);
  assert.equal((await response.json()).idempotency_key, "test-idempotency-key");
});
