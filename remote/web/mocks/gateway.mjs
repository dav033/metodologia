// A loopback stand-in for the real gateway (remote/gateway/server.py), serving the same paths and payload shapes.
// Every payload comes from remote/contract/fixtures, which test_remote_contracts validates against the Pydantic
// contract, and the stream speaks the gateway's SSE dialect: named `event`/`resync` frames with epoch:sequence ids.
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { CHALLENGED_COMMANDS, COMMAND_TYPES, IDEMPOTENCY_KEY, STREAM } from "../src/contract.generated.ts";

const fixtures = new URL("../../contract/fixtures/", import.meta.url);
const fixture = async (name) => JSON.parse(await readFile(new URL(`${name}.json`, fixtures), "utf8"));
const EPOCH = "mock";
const TASK_COMMANDS = new Set(["reopen", "retry", "edit-brief"]);

/** The gateway's GET /snapshot answer: the laptop snapshot flattened with liveness (StreamHub.read_snapshot_response). */
export function gatewaySnapshot(snapshot, online = true) {
  return { ...snapshot, laptop: { online }, online, cachedAt: Date.now() / 1000, lastEventId: `${EPOCH}:0` };
}

/** The checks the real gateway applies before relaying (app.py `relay_command` and `_ledger_command`). */
function commandProblem(command) {
  const target = command?.target;
  if (command?.schemaVersion !== 1 || !COMMAND_TYPES.includes(command.type)) return "Comando inválido";
  if (typeof command.idempotencyKey !== "string" || command.idempotencyKey.length < IDEMPOTENCY_KEY.min
    || command.idempotencyKey.length > IDEMPOTENCY_KEY.max || !new RegExp(IDEMPOTENCY_KEY.pattern).test(command.idempotencyKey)) return "Clave inválida";
  if (typeof target?.project !== "string" || typeof target?.req !== "string" || typeof command.precondition?.state !== "string") return "Destino inválido";
  if (TASK_COMMANDS.has(command.type) && typeof target.taskId !== "string") return "Falta la tarea";
  if (command.type === "cancel-attempt" && typeof target.attemptId !== "string") return "Falta el intento";
  if (CHALLENGED_COMMANDS.includes(command.type) && (!command.confirmation?.challengeId || command.confirmation.typedReq !== target.req)) return "Falta la confirmación";
  return null;
}

export async function createMockGatewayServer() {
  const [snapshot, events, quotas, routes, review] = await Promise.all(["snapshot", "events", "quotas", "routes", "review"].map(fixture));
  const server = createServer((request, response) => {
    const send = (status, body) => {
      response.writeHead(status, { "cache-control": "no-store", "content-type": "application/json; charset=utf-8" });
      response.end(JSON.stringify(body));
    };
    const url = new URL(request.url ?? "/", "http://localhost");
    const path = url.pathname;
    const historyRow = (command, result) => ({ id: command.idempotencyKey, command: command.type, target: `${command.target?.project}/${command.target?.req}`,
      origin: "web", submittedAt: new Date().toISOString(), finishedAt: new Date().toISOString(), result });
    if (request.method === "GET" && path === "/api/auth/session") return send(200, { authenticated: true });
    if (request.method === "GET" && path === "/api/remote/v1/snapshot") {
      server.snapshotReads.push(Date.now());
      response.writeHead(200, { "cache-control": "no-store", "content-type": "application/json; charset=utf-8" });
      response.end(server.snapshot);
      return;
    }
    if (request.method === "GET" && path === "/api/remote/v1/commands") {
      return send(200, { commands: server.history.slice(-100), nextCursor: `cmd_${server.history.length}` });
    }
    if (request.method === "GET" && path === "/api/remote/v1/routes") return send(200, routes);
    if (request.method === "GET" && path === "/api/remote/v1/quotas") return send(200, quotas);
    const reviewMatch = request.method === "GET" && path.match(/^\/api\/remote\/v1\/attempts\/([^/]+)\/review$/);
    if (reviewMatch) {
      if (!/^[A-Za-z0-9_-]+\/REQ-[0-9]+$/.test(url.searchParams.get("target") ?? "")) return send(400, { code: "INVALID_TARGET", message: "Se requiere un target válido." });
      return send(200, { ...review, attemptId: decodeURIComponent(reviewMatch[1]) });
    }
    if (request.method === "GET" && path === "/api/remote/v1/events") {
      return send(200, { events: [], nextCursor: url.searchParams.get("after") ?? "", hasMore: false });
    }
    if (request.method === "GET" && path === STREAM.path) {
      response.writeHead(200, { "cache-control": "no-store, no-transform", "content-type": "text/event-stream; charset=utf-8", "x-accel-buffering": "no", connection: "close" });
      const last = request.headers["last-event-id"];
      const frames = [];
      if (typeof last === "string" && !last.startsWith(`${EPOCH}:`)) frames.push(`event: ${STREAM.resync}\ndata: ${JSON.stringify(JSON.parse(server.snapshot))}\n\n`);
      events.forEach((event, index) => frames.push(`id: ${EPOCH}:${index + 1}\nevent: ${STREAM.event}\ndata: ${JSON.stringify(event)}\n\n`));
      let index = 0;
      const timer = setInterval(() => {
        if (response.destroyed) { clearInterval(timer); return; }
        if (index < frames.length) response.write(frames[index]);
        else { response.write(": keepalive\n\n"); clearInterval(timer); }
        index += 1;
      }, 200);
      request.on("close", () => clearInterval(timer));
      return;
    }
    if (request.method === "POST" && (path === "/api/remote/v1/challenges" || path === "/api/remote/v1/commands")) {
      let body = "";
      request.on("data", (chunk) => { body += chunk; });
      request.on("end", () => {
        let payload;
        try { payload = JSON.parse(body); } catch { return send(400, { code: path.endsWith("challenges") ? "INVALID_CHALLENGE" : "INVALID_COMMAND", message: "JSON inválido" }); }
        if (path.endsWith("/challenges")) {
          if (typeof payload.target !== "string" || payload.typedReq !== payload.target.split("/").at(-1)) {
            return send(400, { code: "INVALID_CHALLENGE", message: "El id del requerimiento no coincide" });
          }
          server.challenges.push({ ...payload, requestMarker: request.headers["x-flow-request"] });
          return send(201, { challengeId: "mock-server-challenge-0001", target: payload.target, expiresIn: 120 });
        }
        const problem = commandProblem(payload);
        if (problem) return send(400, { code: "INVALID_COMMAND", message: problem });
        server.receivedCommands.push(payload);
        server.commandMarkers.push(request.headers["x-flow-request"]);
        const nextResponse = server.commandResponses.shift() ?? server.nextCommandResponse;
        if (nextResponse) {
          server.nextCommandResponse = null;
          server.history.push(historyRow(payload, nextResponse.body?.code ?? "REJECTED"));
          return send(nextResponse.status, nextResponse.body);
        }
        server.commands.push(payload);
        server.history.push(historyRow(payload, "OK"));
        return send(200, { status: "OK", code: null, replayed: false, idempotencyKey: payload.idempotencyKey });
      });
      return;
    }
    send(404, { code: "NOT_FOUND", message: "Ruta desconocida" });
  });
  server.snapshot = JSON.stringify(gatewaySnapshot(snapshot));
  server.snapshotReads = [];
  server.commands = [];
  server.receivedCommands = [];
  server.commandMarkers = [];
  server.history = [];
  server.challenges = [];
  server.commandResponses = [];
  server.nextCommandResponse = null;
  return server;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const port = Number(process.env.MOCK_GATEWAY_PORT ?? 8790);
  const server = await createMockGatewayServer();
  server.listen(port, "127.0.0.1", () => {
    process.stdout.write(`Mock gateway listening at http://127.0.0.1:${port}\n`);
  });
}
