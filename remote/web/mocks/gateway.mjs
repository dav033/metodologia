import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const directory = dirname(fileURLToPath(import.meta.url));
const snapshotPath = join(directory, "fixtures", "snapshot.json");
const attemptReviewPath = join(directory, "fixtures", "attempt-review.json");

export async function createMockGatewayServer() {
  const snapshot = await readFile(snapshotPath, "utf8");
  const attemptReview = await readFile(attemptReviewPath, "utf8");
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
      response.writeHead(200, { "cache-control": "no-store", "content-type": "application/json; charset=utf-8" });
      response.end(server.snapshot);
      return;
    }
    if (request.method === "GET" && request.url === "/api/remote/v1/quotas") {
      send(200, { checkedAt: "2026-10-19T12:00:00Z", accounts: [
        { id: "claude-primary", checkedAt: "2026-10-19T12:00:00Z", windows: [
          { name: "5h", remaining: 34, limit: 100, resetsAt: "2026-10-19T17:00:00Z" },
          { name: "7d", remaining: 412, limit: 1000, resetsAt: "2026-10-25T12:00:00Z" },
        ] },
      ] });
      return;
    }
    if (request.method === "GET" && request.url === "/api/remote/v1/attempts/att-review-1/review") {
      response.writeHead(200, { "cache-control": "no-store", "content-type": "application/json; charset=utf-8" });
      response.end(attemptReview);
      return;
    }
    if (request.method === "GET" && request.url?.startsWith("/api/remote/v1/events?")) {
      send(200, { events: [], nextCursor: "mock-cursor-v1", hasMore: false });
      return;
    }
    if (request.method === "GET" && request.url === "/api/remote/v1/events") {
      response.writeHead(200, { "cache-control": "no-store, no-transform", "content-type": "text/event-stream; charset=utf-8", connection: "keep-alive", "x-accel-buffering": "no" });
      server.eventStreams.add(response);
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
      request.on("close", () => { clearInterval(timer); server.eventStreams.delete(response); });
      return;
    }
    if (request.method === "POST" && request.url === "/api/remote/v1/challenges") {
      server.challengeHeaders.push(request.headers["x-flow-request"] ?? null);
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
      server.commandHeaders.push(request.headers["x-flow-request"] ?? null);
      let body = "";
      request.on("data", (chunk) => { body += chunk; });
      request.on("end", () => {
        try {
          const command = JSON.parse(body);
          if (command.schemaVersion !== 1 || typeof command.idempotencyKey !== "string" || typeof command.type !== "string") {
            send(400, { code: "INVALID_COMMAND", message: "Comando inválido" });
            return;
          }
          server.commands.push(command);
          const nextResponse = server.commandResponses.shift();
          send(nextResponse?.status ?? 202, nextResponse?.body ?? { commandId: "mock-command-v1", status: "accepted", idempotencyKey: command.idempotencyKey });
        } catch {
          send(400, { code: "INVALID_COMMAND", message: "JSON inválido" });
        }
      });
      return;
    }
    send(404, { code: "NOT_FOUND", message: "Ruta desconocida" });
  });
  server.snapshot = snapshot;
  server.commands = [];
  server.challenges = [];
  server.challengeHeaders = [];
  server.commandResponses = [];
  server.commandHeaders = [];
  server.eventStreams = new Set();
  server.publishEvent = (event) => {
    for (const response of server.eventStreams) {
      if (!response.destroyed) response.write(`id: ${event.id}\ndata: ${JSON.stringify(event)}\n\n`);
    }
  };
  return server;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const port = Number(process.env.MOCK_GATEWAY_PORT ?? 8790);
  const server = await createMockGatewayServer();
  server.listen(port, "127.0.0.1", () => {
    process.stdout.write(`Mock gateway listening at http://127.0.0.1:${port}\n`);
  });
}
