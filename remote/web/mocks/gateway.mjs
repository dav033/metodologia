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
          server.commands.push(command);
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
  return server;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const port = Number(process.env.MOCK_GATEWAY_PORT ?? 8790);
  const server = await createMockGatewayServer();
  server.listen(port, "127.0.0.1", () => {
    process.stdout.write(`Mock gateway listening at http://127.0.0.1:${port}\n`);
  });
}
