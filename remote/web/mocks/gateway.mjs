import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const directory = dirname(fileURLToPath(import.meta.url));
const snapshotPath = join(directory, "fixtures", "snapshot.json");

export async function createMockGatewayServer() {
  const snapshot = await readFile(snapshotPath, "utf8");

  return createServer((request, response) => {
    const authenticated = (request.headers.cookie ?? "").split(";").some((cookie) => cookie.trim() === "flow_session=mock-session");
    const sendJson = (status, value) => {
      response.writeHead(status, { "cache-control": "no-store", "content-type": "application/json; charset=utf-8" });
      response.end(JSON.stringify(value));
    };

    if (request.method === "GET" && request.url === "/api/auth/session") {
      if (!authenticated) return sendJson(401, { error: "unauthorized" });
      return sendJson(200, { login: "dav033" });
    }

    if (request.method === "GET" && request.url === "/api/auth/github") {
      response.writeHead(302, {
        "cache-control": "no-store",
        location: "https://github.com/login/oauth/authorize?state=mock-oauth-state",
        "set-cookie": "flow_oauth_state=mock-oauth-state; Path=/api/auth/callback; HttpOnly; Secure; SameSite=Lax",
      });
      response.end();
      return;
    }

    if (request.method === "GET" && request.url === "/api/remote/v1/snapshot") {
      if (!authenticated) return sendJson(401, { error: "unauthorized" });
      response.writeHead(200, { "cache-control": "no-store", "content-type": "application/json; charset=utf-8" });
      response.end(snapshot);
      return;
    }

    response.writeHead(404, { "content-type": "application/json; charset=utf-8" });
    response.end(JSON.stringify({ ok: false, error: { code: "NOT_FOUND", message: "Ruta desconocida" } }));
  });
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const port = Number(process.env.MOCK_GATEWAY_PORT ?? 8790);
  const server = await createMockGatewayServer();
  server.listen(port, "127.0.0.1", () => {
    process.stdout.write(`Mock gateway listening at http://127.0.0.1:${port}\n`);
  });
}
