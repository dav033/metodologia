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
      send(200, { login: "owner" });
      return;
    }
    if (request.method === "GET" && request.url === "/api/remote/v1/snapshot") {
      response.writeHead(200, { "cache-control": "no-store", "content-type": "application/json; charset=utf-8" });
      response.end(snapshot);
      return;
    }
    if (request.method === "GET" && request.url === "/api/remote/v1/commands?after=&limit=100") {
      send(200, { commands: [{ id: "cmd-previous", command: "pause", target: "lotm/REQ-027", submittedAt: "2026-10-19T11:58:00Z", origin: "telegram", result: "accepted" }], nextCursor: "1" });
      return;
    }
    if (request.method === "GET" && request.url?.startsWith("/api/remote/v1/events")) {
      response.writeHead(200, { "cache-control": "no-store", "content-type": "text/event-stream; charset=utf-8" });
      const events = [
        { id: "mock-event-1", cursor: "1", schemaVersion: 1, type: "attempt.failed", occurredAt: "2026-10-19T12:00:01Z", target: { kind: "run", project: "lotm", req: "REQ-027", taskId: "T15a" }, data: { summary: "La verificación terminó" }, dedupeKey: "mock-event-1" },
        { id: "mock-event-2", cursor: "2", schemaVersion: 1, type: "attempt.failed", occurredAt: "2026-10-19T12:00:02Z", target: { kind: "run", project: "lotm", req: "REQ-027", taskId: "T15a" }, data: { summary: "La verificación terminó" }, dedupeKey: "mock-event-2" },
      ];
      for (const event of events) response.write(`id: ${event.cursor}\nevent: flow\ndata: ${JSON.stringify(event)}\n\n`);
      response.end();
      return;
    }
    if (request.method === "POST" && request.url === "/api/remote/v1/challenges") {
      let body = "";
      request.on("data", (chunk) => { body += chunk; });
      request.on("end", () => {
        const challenge = JSON.parse(body);
        server.challenges.push(challenge);
        if (challenge.typedReq !== challenge.target?.req) { send(409, { code: "INVALID_CHALLENGE", message: "El REQ escrito no coincide." }); return; }
        send(201, { challengeId: "challenge-token-0123456789", target: "lotm/REQ-027", expiresIn: 120 });
      });
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
          if (typeof command.idempotencyKey !== "string" || typeof command.type !== "string" || !command.target || typeof command.target.project !== "string") {
            send(400, { code: "INVALID_COMMAND", message: "Comando inválido" });
            return;
          }
          const challenged = ["revise", "approve", "launch", "cancel-plan", "delete-plan"].includes(command.type);
          if (challenged && (typeof command.confirmation?.challengeId !== "string" || command.confirmation.typedReq !== command.target.req)) {
            send(409, { code: "CONFIRMATION_REQUIRED", message: "Falta la confirmación." });
            return;
          }
          server.commands.push(command);
          if (command.type === "reopen") { send(409, { code: "STALE_PRECONDITION", message: "El estado cambió." }); return; }
          send(202, { commandId: `cmd-${server.commands.length}`, status: "accepted", idempotencyKey: command.idempotencyKey });
        } catch {
          send(400, { code: "INVALID_COMMAND", message: "JSON inválido" });
        }
      });
      return;
    }
    send(404, { code: "NOT_FOUND", message: "Ruta desconocida" });
  });
  server.commands = [];
  server.challenges = [];
  return server;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const port = Number(process.env.MOCK_GATEWAY_PORT ?? 8790);
  const server = await createMockGatewayServer();
  server.listen(port, "127.0.0.1", () => {
    process.stdout.write(`Mock gateway listening at http://127.0.0.1:${port}\n`);
  });
}
