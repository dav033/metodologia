import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const directory = dirname(fileURLToPath(import.meta.url));
const snapshotPath = join(directory, "fixtures", "snapshot.json");
const reviewPath = join(directory, "fixtures", "failure-review.json");

export async function createMockGatewayServer() {
  const snapshot = await readFile(snapshotPath, "utf8");
  const review = await readFile(reviewPath, "utf8");
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
      response.end(snapshot);
      return;
    }
    if (request.method === "GET" && request.url?.startsWith("/api/remote/v1/events?")) {
      const after = new URL(request.url, "http://gateway.local").searchParams.get("after") ?? "";
      const all = [
        { id: "mock-event-1", cursor: "mock-event-cursor-1", schemaVersion: 1, type: "attempt.failed", occurredAt: "2026-10-19T12:00:01Z", target: { run: "lotm/REQ-027", task: "T15a" }, data: { summary: "La verificación terminó" }, dedupeKey: "mock-event-1" },
        { id: "mock-event-2", cursor: "mock-event-cursor-2", schemaVersion: 1, type: "attempt.failed", occurredAt: "2026-10-19T12:00:02Z", target: { run: "lotm/REQ-027", task: "T15a" }, data: { summary: "La verificación terminó" }, dedupeKey: "mock-event-2" },
      ];
      const start = Math.max(0, all.findIndex((event) => event.cursor === after) + 1);
      const events = after === "mock-event-cursor-2" ? [] : all.slice(start);
      send(200, { events, nextCursor: events.at(-1)?.cursor ?? (after || "mock-cursor-v1"), hasMore: false });
      return;
    }
    const reviewMatch = request.method === "GET" && request.url?.match(/^\/api\/remote\/v1\/attempts\/([^/]+)\/review$/);
    if (reviewMatch) {
      if (reviewMatch[1] !== "att-failed-02") { send(404, { code: "ATTEMPT_NOT_FOUND", message: "No se encontró el intento." }); return; }
      response.writeHead(200, { "cache-control": "no-store", "content-type": "application/json; charset=utf-8" });
      response.end(review);
      return;
    }
    if (request.method === "POST" && request.url === "/api/remote/v1/commands") {
      let body = "";
      request.on("data", (chunk) => { body += chunk; });
      request.on("end", () => {
        try {
          const command = JSON.parse(body);
          if (typeof command.idempotency_key !== "string" || typeof command.command !== "string" || typeof command.target !== "string" || command.origin !== "web") {
            send(400, { code: "INVALID_COMMAND", message: "Comando inválido" });
            return;
          }
          server.commands.push(command);
          send(200, { status: "OK", code: null, replayed: false, idempotency_key: command.idempotency_key });
        } catch {
          send(400, { code: "INVALID_COMMAND", message: "JSON inválido" });
        }
      });
      return;
    }
    send(404, { code: "NOT_FOUND", message: "Ruta desconocida" });
  });
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
