import assert from "node:assert/strict";
import { once } from "node:events";
import { readFile } from "node:fs/promises";
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

const contractFixture = async (name) => JSON.parse(await readFile(new URL(`../../contract/fixtures/${name}.json`, import.meta.url), "utf8"));

test("mock gateway returns the gateway snapshot contract and the session consumed by the panel", async () => {
  const session = await fetch(`${origin}/api/auth/session`);
  assert.deepEqual(await session.json(), { authenticated: true });

  const response = await fetch(`${origin}/api/remote/v1/snapshot`);
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /application\/json/);

  const body = await response.json();
  const laptop = await contractFixture("snapshot");
  const { laptop: liveness, online, cachedAt, lastEventId, ...cached } = body;
  assert.deepEqual(cached, laptop, "the mock serves the validated laptop snapshot, flattened like StreamHub");
  assert.deepEqual([liveness, online, typeof cachedAt, lastEventId], [{ online: true }, true, "number", "mock:0"]);
  const events = await fetch(`${origin}/api/remote/v1/events?after=${encodeURIComponent(body.cursor)}&limit=100`);
  assert.deepEqual(await events.json(), { events: [], nextCursor: body.cursor, hasMore: false });
});

test("mock gateway accepts every contract command and refuses what the gateway refuses", async () => {
  const post = (body) => fetch(`${origin}/api/remote/v1/commands`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
  for (const command of await contractFixture("commands")) {
    const response = await post(command);
    assert.equal(response.status, 200, command.type);
    assert.deepEqual(await response.json(), { status: "OK", code: null, replayed: false, idempotencyKey: command.idempotencyKey });
  }
  const [, , , reopen] = await contractFixture("commands");
  for (const bad of [{ ...reopen, target: { kind: "run", project: "pictures", req: "REQ-018" } }, { ...reopen, idempotencyKey: "short" }]) {
    assert.equal((await post(bad)).status, 400);
  }
});

async function readFrames(response, count) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let text = "";
  while (text.split("\n\n").filter((frame) => /^event: /m.test(frame)).length < count) {
    const { value, done } = await reader.read();
    if (done) break;
    text += decoder.decode(value, { stream: true });
  }
  await reader.cancel();
  return text.split("\n\n").filter((frame) => /^event: /m.test(frame)).map((frame) => Object.fromEntries(
    frame.split("\n").filter((line) => line && !line.startsWith(":")).map((line) => [line.slice(0, line.indexOf(":")), line.slice(line.indexOf(":") + 2)])));
}

test("F4: the mock serves the real gateway stream contract, including resync", async () => {
  const { STREAM, EVENT_TYPES } = await import("../src/contract.generated.ts");
  const response = await fetch(`${origin}${STREAM.path}`);
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /text\/event-stream/);
  const frames = await readFrames(response, 2);
  assert.deepEqual(frames.map((frame) => frame.event), [STREAM.event, STREAM.event]);
  for (const frame of frames) {
    assert.match(frame.id, /^[A-Za-z0-9]+:[0-9]+$/, "ids are the gateway's epoch:sequence");
    const event = JSON.parse(frame.data);
    assert.equal(event.schemaVersion, 1);
    assert.ok(EVENT_TYPES.includes(event.type));
  }
  const resumed = await fetch(`${origin}${STREAM.path}`, { headers: { "Last-Event-ID": "other-epoch:9" } });
  const [resync] = await readFrames(resumed, 1);
  assert.equal(resync.event, STREAM.resync);
  assert.equal(JSON.parse(resync.data).schemaVersion, 1);
  assert.equal((await fetch(`${origin}/api/remote/v1/events/stream?after=x`)).status, 404, "the old phone-only path is gone");
});

test("mock read models are the contract fixtures", async () => {
  for (const [path, name] of [["/api/remote/v1/quotas", "quotas"], ["/api/remote/v1/routes?target=lotm%2FREQ-027&task=T15c", "routes"],
    ["/api/remote/v1/attempts/att-rejected-fixture/review?target=lotm%2FREQ-027", "review"]]) {
    const expected = JSON.parse(await readFile(new URL(`../../contract/fixtures/${name}.json`, import.meta.url), "utf8"));
    assert.deepEqual(await (await fetch(`${origin}${path}`)).json(), expected, name);
  }
});
