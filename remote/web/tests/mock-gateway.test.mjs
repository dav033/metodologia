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

test("mock gateway returns its fixture snapshot at the gateway state endpoint", async () => {
  const response = await fetch(`${origin}/api/state`);
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /application\/json/);

  const body = await response.json();
  assert.equal(body.snapshot.etag, "mock-snapshot-v1");
  assert.equal(body.snapshot.runs[0].req, "REQ-027");
  assert.equal(body.laptop.online, true);
});

test("mock gateway does not serve unimplemented or mutating routes", async () => {
  const response = await fetch(`${origin}/api/commands`, { method: "POST" });
  assert.equal(response.status, 404);
  assert.equal((await response.json()).error.code, "NOT_FOUND");
});
