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
  assert.deepEqual(body.runs.map((run) => run.req), ["REQ-027", "REQ-018"]);
  assert.equal(body.runs[0].lastSeenAt, "2026-10-19T11:59:45Z");
  assert.equal(body.plans[0].acceptanceCriteria[0], "Owner reviews and approves the plan");
  const events = await fetch(`${origin}/api/remote/v1/events?after=${body.cursor}&limit=100`);
  assert.deepEqual(await events.json(), { events: [], nextCursor: body.cursor, hasMore: false });
});

test("mock gateway accepts versioned, idempotent control commands", async () => {
  const response = await fetch(`${origin}/api/remote/v1/commands`, {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ schemaVersion: 1, idempotencyKey: "test-idempotency-key", type: "cancel-attempt" }),
  });
  assert.equal(response.status, 202);
  assert.equal((await response.json()).idempotencyKey, "test-idempotency-key");
});

test("queued command responses preserve the fallback and record origin and stale result", async () => {
  server.commandResponses.push({ status: 409, body: { code: "STALE_PRECONDITION", message: "stale" } });
  server.nextCommandResponse = { status: 422, body: { code: "REJECTED", message: "rejected" } };

  const submit = (idempotencyKey) => fetch(`${origin}/api/remote/v1/commands`, {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ schemaVersion: 1, idempotencyKey, type: "delete-plan", target: { project: "lotm", req: "REQ-027" } }),
  });

  assert.equal((await submit("queued-command")).status, 409);
  assert.equal(server.history.at(-1)?.origin, "Web");
  assert.equal(server.history.at(-1)?.result, "Rechazado: el estado cambió");

  assert.equal((await submit("fallback-command")).status, 422);
  assert.equal(server.history.at(-1)?.origin, "Web");
  assert.equal(server.history.at(-1)?.result, "Rechazado");
});
