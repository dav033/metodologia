import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const directory = dirname(fileURLToPath(import.meta.url));
const snapshotPath = join(directory, "fixtures", "snapshot.json");

export async function createMockGatewayServer() {
  const snapshot = await readFile(snapshotPath, "utf8");
  const server = createServer((request, response) => {
    const send = (status, body) => {
      response.writeHead(status, { "cache-control": "no-store", "content-type": "application/json; charset=utf-8" });
      response.end(JSON.stringify(body));
    };
    if (request.method === "GET" && request.url === "/api/auth/session") {
      send(200, { authenticated: true });
      return;
    }
    if (request.method === "GET" && request.url === "/api/remote/v1/snapshot") {
      server.snapshotReads.push(Date.now());
      response.writeHead(200, { "cache-control": "no-store", "content-type": "application/json; charset=utf-8" });
      response.end(server.snapshot);
      return;
    }
    if (request.method === "GET" && request.url?.startsWith("/api/remote/v1/commands?")) {
      send(200, { commands: server.history.slice(-100).reverse() });
      return;
    }
    if (request.method === "GET" && request.url?.startsWith("/api/remote/v1/routes?")) {
      send(200, { routes: [
        { route_id: "route-unavailable", provider: "claude", model: "sonnet", profile: "work", available: false },
        { route_id: "route-codex-work", provider: "codex", model: "gpt-6.1-sol", profile: "codex-work", available: true, quota_status: "available" },
      ] });
      return;
    }
    if (request.method === "GET" && request.url === "/api/remote/v1/quotas") {
      send(200, { checkedAt: "2026-10-19T12:00:00Z", accounts: [
        { profile: "codex-work", provider: "codex", status: "ok", observed_at: 1792411200,
          windows: { five_hour: { used_percent: 27, resets_at: 1792414800, window_minutes: 300 }, seven_day: { used_percent: 64, resets_at: 1792936800, window_minutes: 10080 } } },
      ] });
      return;
    }
    const reviewMatch = request.method === "GET" && request.url?.match(/^\/api\/remote\/v1\/attempts\/([^/]+)\/review$/);
    if (reviewMatch) {
      const attemptId = decodeURIComponent(reviewMatch[1]);
      send(200, { attemptId, cause: "La verificación falló; GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz123456",
        verification: { command: "npm run verify", output: "Fallo de fixture en rejected" },
        diff: { stat: "2 files changed, 3 insertions(+)" },
        logTail: "Authorization: Bearer abc.def.ghi\nFin de log" });
      return;
    }
    if (request.method === "GET" && request.url?.startsWith("/api/remote/v1/events?")) {
      send(200, { events: [], nextCursor: "mock-cursor-v1", hasMore: false });
      return;
    }
    if (request.method === "GET" && request.url?.startsWith("/api/remote/v1/events/stream?")) {
      response.writeHead(200, { "cache-control": "no-store, no-transform", "content-type": "text/event-stream; charset=utf-8", connection: "keep-alive", "x-accel-buffering": "no" });
      const events = [
        { id: "mock-event-1", cursor: "mock-event-cursor-1", schemaVersion: 1, type: "attempt.failed", occurredAt: "2026-10-19T12:00:01Z", target: { kind: "attempt", project: "lotm", req: "REQ-027", taskId: "T15a", attemptId: "att-0008" }, data: { summary: "La verificación terminó" } },
        { id: "mock-event-2", cursor: "mock-event-cursor-2", schemaVersion: 1, type: "attempt.failed", occurredAt: "2026-10-19T12:00:02Z", target: { kind: "attempt", project: "lotm", req: "REQ-027", taskId: "T15a", attemptId: "att-0008" }, data: { summary: "La verificación terminó" } },
      ];
      let index = 0;
      const timer = setInterval(() => {
        if (response.destroyed) { clearInterval(timer); return; }
        if (index < events.length) response.write(`id: ${events[index].cursor}\ndata: ${JSON.stringify(events[index])}\n\n`);
        else { response.write(": keep-alive\n\n"); clearInterval(timer); }
        index += 1;
      }, 200);
      request.on("close", () => clearInterval(timer));
      return;
    }
    if (request.method === "POST" && request.url === "/api/remote/v1/challenges") {
      let body = "";
      request.on("data", (chunk) => { body += chunk; });
      request.on("end", () => {
        try {
          const challengeRequest = JSON.parse(body);
          if (challengeRequest.typedReq !== challengeRequest.target.split("/").at(-1)) {
            send(400, { code: "INVALID_CHALLENGE", message: "El id del requerimiento no coincide" });
            return;
          }
          server.challenges.push(challengeRequest);
          send(201, { challengeId: "mock-server-challenge-0001", target: challengeRequest.target, expiresIn: 120 });
        } catch { send(400, { code: "INVALID_CHALLENGE", message: "JSON inválido" }); }
      });
      return;
    }
    if (request.method === "POST" && request.url === "/api/remote/v1/commands") {
      let body = "";
      request.on("data", (chunk) => { body += chunk; });
      request.on("end", () => {
        try {
          const command = JSON.parse(body);
          if (command.schemaVersion !== 1 || typeof command.idempotencyKey !== "string" || typeof command.type !== "string") {
            send(400, { code: "INVALID_COMMAND", message: "Comando inválido" });
            return;
          }
          server.receivedCommands.push(command);
          const queuedResponse = server.commandResponses.shift();
          const nextResponse = queuedResponse ?? server.nextCommandResponse;
          if (nextResponse) {
            server.nextCommandResponse = null;
            server.history.push({ id: command.idempotencyKey, command: command.type, target: `${command.target?.project}/${command.target?.req}`, submittedAt: new Date().toISOString(), origin: "Web", result: "Rechazado" });
            send(nextResponse.status, nextResponse.body);
            return;
          }
          server.commands.push({ ...command, requestMarker: request.headers["x-flow-request"] });
          server.history.push({ id: command.idempotencyKey, command: command.type, target: `${command.target?.project}/${command.target?.req}`, submittedAt: new Date().toISOString(), origin: "Web", result: "accepted" });
          send(202, { commandId: "mock-command-v1", status: "accepted", idempotencyKey: command.idempotencyKey });
        } catch {
          send(400, { code: "INVALID_COMMAND", message: "JSON inválido" });
        }
      });
      return;
    }
    send(404, { code: "NOT_FOUND", message: "Ruta desconocida" });
  });
  server.snapshot = snapshot;
  server.snapshotReads = [];
  server.commands = [];
  server.receivedCommands = [];
  server.challenges = [];
  server.history = [];
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
