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

test("mock gateway sends unauthenticated visitors to the GitHub OAuth start", async () => {
  const session = await fetch(`${origin}/api/auth/session`);
  assert.equal(session.status, 401);

  const response = await fetch(`${origin}/api/auth/github`, { redirect: "manual" });
  assert.equal(response.status, 302);
  assert.match(response.headers.get("location") ?? "", /^https:\/\/github\.com\/login\/oauth\/authorize\?/);
  assert.match(response.headers.get("set-cookie") ?? "", /flow_oauth_state=.*SameSite=Lax/);
});

test("mock gateway returns the v1 run snapshot only to an authenticated session", async () => {
  const unauthorized = await fetch(`${origin}/api/remote/v1/snapshot`);
  assert.equal(unauthorized.status, 401);

  const headers = { cookie: "flow_session=mock-session" };
  const sessionResponse = await fetch(`${origin}/api/auth/session`, { headers });
  assert.equal(sessionResponse.status, 200);
  assert.deepEqual(await sessionResponse.json(), { login: "dav033" });

  const response = await fetch(`${origin}/api/remote/v1/snapshot`, { headers });
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /application\/json/);

  const body = await response.json();
  assert.equal(body.schemaVersion, 1);
  assert.equal(body.runs[0].req_id, "REQ-027");
  assert.equal(body.runs[0].status, "running");
  assert.equal(body.runs[0].last_sign_of_life, "2026-10-19T11:59:45Z");
  assert.equal(body.laptop.online, true);
});

test("mock gateway does not serve unimplemented or mutating routes", async () => {
  const response = await fetch(`${origin}/api/remote/v1/commands`, { method: "POST" });
  assert.equal(response.status, 404);
  assert.equal((await response.json()).error.code, "NOT_FOUND");
});
