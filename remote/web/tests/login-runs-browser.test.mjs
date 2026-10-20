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
import { createMockGatewayServer } from "../mocks/gateway.mjs";

const root = fileURLToPath(new URL("..", import.meta.url));
const chromiumPath = process.env.CHROMIUM_PATH ?? "/usr/bin/chromium";

async function listen(server) {
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  const address = server.address();
  assert.ok(address && typeof address !== "string");
  return address.port;
}

async function reservePort() {
  const server = createServer();
  const port = await listen(server);
  await new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
  return port;
}

async function waitFor(url, child) {
  for (let attempt = 0; attempt < 100; attempt += 1) {
    if (child.exitCode !== null) throw new Error("Next.js exited before becoming ready");
    try {
      const response = await fetch(url);
      if (response.status < 500) return;
    } catch { await delay(200); }
  }
  throw new Error("Next.js did not become ready");
}

async function debuggerReady(origin, child) {
  for (let attempt = 0; attempt < 100; attempt += 1) {
    if (child.exitCode !== null) throw new Error("Chromium exited before DevTools became ready");
    try {
      const response = await fetch(`${origin}/json/version`);
      if (response.ok) return;
    } catch { await delay(100); }
  }
  throw new Error("Chromium DevTools did not become ready");
}

function cdp(socket, method, params = {}) {
  const id = (cdp.nextId ?? 0) + 1;
  cdp.nextId = id;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error(`DevTools timed out: ${method}`)), 10_000);
    const receive = (event) => {
      const message = JSON.parse(event.data);
      if (message.id !== id) return;
      clearTimeout(timer);
      socket.removeEventListener("message", receive);
      if (message.error) reject(new Error(message.error.message));
      else resolve(message.result);
    };
    socket.addEventListener("message", receive);
    socket.send(JSON.stringify({ id, method, params }));
  });
}

test("OAuth redirect and authenticated runs list render without overflow at 360 px", { timeout: 90_000 }, async () => {
  let gateway;
  let next;
  let browser;
  let socket;
  let profile;
  let frontendOrigin;

  try {
    gateway = await createMockGatewayServer();
    const gatewayPort = await listen(gateway);
    const frontendPort = await reservePort();
    frontendOrigin = `http://127.0.0.1:${frontendPort}`;
    next = spawn(process.execPath, [join(root, "node_modules/next/dist/bin/next"), "dev", "--hostname", "127.0.0.1", "--port", String(frontendPort)], {
      cwd: root,
      env: { ...process.env, FLOW_GATEWAY_ORIGIN: `http://127.0.0.1:${gatewayPort}` },
      stdio: "ignore",
    });
    await waitFor(frontendOrigin, next);

    const oauthResponse = await fetch(`${frontendOrigin}/api/auth/github`, { redirect: "manual" });
    assert.equal(oauthResponse.status, 302, "the login path must reach the gateway OAuth start");
    assert.match(oauthResponse.headers.get("location") ?? "", /^https:\/\/github\.com\/login\/oauth\/authorize\?/);

    profile = await mkdtemp(join(tmpdir(), "flow-login-runs-browser-"));
    const debugPort = await reservePort();
    browser = spawn(chromiumPath, [
      "--headless=new", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
      "--disable-background-networking", "--no-first-run", "--remote-allow-origins=*",
      `--remote-debugging-port=${debugPort}`, `--user-data-dir=${profile}`, "about:blank",
    ], { stdio: "ignore" });
    const debugOrigin = `http://127.0.0.1:${debugPort}`;
    await debuggerReady(debugOrigin, browser);
    const targetResponse = await fetch(`${debugOrigin}/json/new?about:blank`, { method: "PUT" });
    assert.equal(targetResponse.status, 200);
    const target = await targetResponse.json();
    socket = new WebSocket(target.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => {
      socket.addEventListener("open", resolve, { once: true });
      socket.addEventListener("error", reject, { once: true });
    });
    await cdp(socket, "Emulation.setDeviceMetricsOverride", { width: 360, height: 900, deviceScaleFactor: 1, mobile: true });
    await cdp(socket, "Page.enable");
    await cdp(socket, "Runtime.enable");
    await cdp(socket, "Page.navigate", { url: frontendOrigin });

    let pageState;
    for (let attempt = 0; attempt < 80; attempt += 1) {
      const result = await cdp(socket, "Runtime.evaluate", {
        expression: "({text: document.body.innerText, width: document.documentElement.scrollWidth, viewport: window.innerWidth, login: document.querySelector('.sign-in')?.getAttribute('href')})",
        returnByValue: true,
      });
      pageState = result.result?.value;
      if (pageState?.login) break;
      await delay(150);
    }
    assert.equal(pageState?.login, "/api/auth/github", "the login button must point at the gateway start route");

    await cdp(socket, "Network.enable");
    await cdp(socket, "Network.setCookie", { name: "flow_session", value: "mock-session", url: frontendOrigin, path: "/", sameSite: "Lax" });
    await cdp(socket, "Page.navigate", { url: frontendOrigin });
    for (let attempt = 0; attempt < 80; attempt += 1) {
      const result = await cdp(socket, "Runtime.evaluate", {
        expression: "({text: document.body.innerText, width: document.documentElement.scrollWidth, viewport: window.innerWidth})",
        returnByValue: true,
      });
      pageState = result.result?.value;
      if (pageState?.text?.includes("REQ-027") && pageState.text.includes("Última señal de vida")) break;
      await delay(150);
    }

    assert.ok(pageState?.text?.includes("REQ-027"), "authenticated page should render the run id");
    assert.ok(pageState.text.includes("En curso"), "authenticated page should render the run state");
    assert.match(pageState.text, /Última señal de vida/i, "authenticated page should label last sign of life");
    assert.match(pageState.text, /2026/, "authenticated page should render the gateway's last-seen timestamp");
    assert.equal(pageState.viewport, 360);
    assert.equal(pageState.width, 360, `page overflowed horizontally at 360 px: ${pageState.width}px`);
  } catch (error) {
    if (error?.code === "ENOENT") assert.fail(`Chromium was not found at ${chromiumPath}`);
    throw error;
  } finally {
    socket?.close();
    for (const child of [next, browser]) {
      if (child && child.exitCode === null) {
        child.kill("SIGTERM");
        await once(child, "close");
      }
    }
    if (gateway?.listening) {
      gateway.close();
      await once(gateway, "close");
    }
    if (profile) await rm(profile, { recursive: true, force: true });
  }
});
