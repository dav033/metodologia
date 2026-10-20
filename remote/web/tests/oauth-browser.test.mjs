import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { once } from "node:events";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createServer } from "node:http";
import { setTimeout as delay } from "node:timers/promises";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("..", import.meta.url));
const chromiumPath = process.env.CHROMIUM_PATH ?? "/usr/bin/chromium";

async function listen(server, host = "127.0.0.1") {
  server.listen(0, host);
  await once(server, "listening");
  const address = server.address();
  assert.ok(address && typeof address !== "string");
  return address.port;
}

async function waitForNext(url, process) {
  for (let attempt = 0; attempt < 60; attempt += 1) {
    if (process.exitCode !== null) throw new Error("Next.js dev server exited before becoming ready");
    try {
      const response = await fetch(url);
      if (response.status < 500) return;
    } catch {
      await delay(250);
    }
  }
  throw new Error("Next.js dev server did not become ready");
}

test("OAuth browser round-trip keeps state and session cookies on the frontend host", { timeout: 60_000 }, async () => {
  let frontendOrigin;
  let sawStateOnCallback = false;
  let sawSessionAfterCallback = false;
  let gateway;
  let provider;
  let next;
  let profile;

  try {
    provider = createServer((request, response) => {
      const authorize = new URL(request.url, "http://localhost");
      assert.equal(authorize.pathname, "/authorize");
      const callback = new URL(authorize.searchParams.get("redirect_uri"));
      callback.searchParams.set("code", "local-test-code");
      callback.searchParams.set("state", authorize.searchParams.get("state"));
      response.writeHead(302, { location: callback.toString() });
      response.end();
    });
    const providerPort = await listen(provider, "::1");

    gateway = createServer((request, response) => {
      const requestUrl = new URL(request.url, "http://gateway.local");
      if (requestUrl.pathname === "/api/auth/github") {
        const state = "browser-state-check";
        const authorize = new URL(`http://localhost:${providerPort}/authorize`);
        authorize.searchParams.set("state", state);
        authorize.searchParams.set("redirect_uri", `${frontendOrigin}/api/auth/callback`);
        response.writeHead(302, {
          "set-cookie": `flow_oauth_state=${state}; Path=/; HttpOnly; Secure; SameSite=Lax`,
          location: authorize.toString(),
        });
        response.end();
        return;
      }
      if (requestUrl.pathname === "/api/auth/callback") {
        const cookies = request.headers.cookie ?? "";
        sawStateOnCallback = cookies.includes("flow_oauth_state=browser-state-check");
        if (!sawStateOnCallback || requestUrl.searchParams.get("state") !== "browser-state-check") {
          response.writeHead(400);
          response.end("OAuth state cookie was not sent to the frontend callback");
          return;
        }
        response.writeHead(302, {
          "set-cookie": "flow_session=browser-session; Path=/; HttpOnly; Secure; SameSite=Strict",
          location: "/api/auth/session",
        });
        response.end();
        return;
      }
      if (requestUrl.pathname === "/api/auth/session") {
        sawSessionAfterCallback = (request.headers.cookie ?? "").includes("flow_session=browser-session");
        response.writeHead(200, { "content-type": "application/json; charset=utf-8" });
        response.end(JSON.stringify({ authenticated: sawSessionAfterCallback }));
        return;
      }
      response.writeHead(404);
      response.end();
    });
    const gatewayPort = await listen(gateway);

    const reservation = createServer();
    const frontendPort = await listen(reservation);
    await new Promise((resolve, reject) => reservation.close((error) => error ? reject(error) : resolve()));
    frontendOrigin = `http://127.0.0.1:${frontendPort}`;

    next = spawn(process.execPath, [
      join(root, "node_modules/next/dist/bin/next"), "dev", "--hostname", "127.0.0.1", "--port", String(frontendPort),
    ], {
      cwd: root,
      env: { ...process.env, FLOW_GATEWAY_ORIGIN: `http://127.0.0.1:${gatewayPort}` },
      stdio: "ignore",
    });
    await waitForNext(frontendOrigin, next);

    profile = await mkdtemp(join(tmpdir(), "flow-oauth-browser-"));
    const browser = spawn(chromiumPath, [
      "--headless=new", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
      "--disable-background-networking", "--no-first-run", `--user-data-dir=${profile}`,
      "--dump-dom", `${frontendOrigin}/api/auth/github`,
    ], { stdio: ["ignore", "pipe", "pipe"] });
    let stdout = "";
    let stderr = "";
    browser.stdout.setEncoding("utf8").on("data", (chunk) => { stdout += chunk; });
    browser.stderr.setEncoding("utf8").on("data", (chunk) => { stderr += chunk; });
    const browserExit = await Promise.race([
      once(browser, "close"),
      once(browser, "error").then(([error]) => { throw error; }),
    ]);
    assert.equal(browserExit[0], 0, `Chromium failed: ${stderr}`);
    assert.match(stdout, /authenticated.*true|true.*authenticated/i);
    assert.equal(sawStateOnCallback, true, "frontend callback must receive the Lax state cookie");
    assert.equal(sawSessionAfterCallback, true, "same-origin API session request must receive the Strict session cookie");
  } catch (error) {
    if (error?.code === "ENOENT") {
      assert.fail(`Chromium was not found at ${chromiumPath}; set CHROMIUM_PATH to a local Chromium binary`);
    }
    throw error;
  } finally {
    if (next && next.exitCode === null) {
      next.kill("SIGTERM");
      await once(next, "close");
    }
    for (const server of [gateway, provider]) {
      if (server?.listening) {
        server.close();
        await once(server, "close");
      }
    }
    if (profile) await rm(profile, { recursive: true, force: true });
  }
});
