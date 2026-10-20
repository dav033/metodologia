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

async function waitForNext(url, process) {
  for (let attempt = 0; attempt < 80; attempt += 1) {
    if (process.exitCode !== null) throw new Error("Next.js dev server exited before becoming ready");
    try {
      const response = await fetch(url);
      if (response.status < 500) return;
    } catch { await delay(250); }
  }
  throw new Error("Next.js dev server did not become ready");
}

async function waitForDebugger(origin, process) {
  for (let attempt = 0; attempt < 80; attempt += 1) {
    if (process.exitCode !== null) throw new Error("Chromium exited before DevTools became ready");
    try {
      const response = await fetch(`${origin}/json/version`);
      if (response.ok) return;
    } catch { await delay(100); }
  }
  throw new Error("Chromium DevTools did not become ready");
}

async function cdp(socket, method, params = {}) {
  const id = (cdp.nextId ?? 0) + 1;
  cdp.nextId = id;
  const response = new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error(`DevTools timed out: ${method}`)), 10_000);
    const receive = (event) => {
      const message = JSON.parse(event.data);
      if (message.id !== id) return;
      clearTimeout(timeout);
      socket.removeEventListener("message", receive);
      if (message.error) reject(new Error(message.error.message));
      else resolve(message.result);
    };
    socket.addEventListener("message", receive);
  });
  socket.send(JSON.stringify({ id, method, params }));
  return response;
}

test("real panel entrypoint renders API contract runs, failure reviews and controls at 360 px", { timeout: 60_000 }, async () => {
  let gateway;
  let next;
  let browser;
  let profile;
  let debugReservation;
  try {
    gateway = await createMockGatewayServer();
    const gatewayPort = await listen(gateway);
    const reservation = createServer();
    const frontendPort = await listen(reservation);
    await new Promise((resolve, reject) => reservation.close((error) => error ? reject(error) : resolve()));
    const frontendOrigin = `http://127.0.0.1:${frontendPort}`;
    next = spawn(process.execPath, [join(root, "node_modules/next/dist/bin/next"), "dev", "--hostname", "127.0.0.1", "--port", String(frontendPort)], {
      cwd: root, env: { ...process.env, FLOW_GATEWAY_ORIGIN: `http://127.0.0.1:${gatewayPort}` }, stdio: "ignore",
    });
    await waitForNext(frontendOrigin, next);

    profile = await mkdtemp(join(tmpdir(), "flow-panel-browser-"));
    debugReservation = createServer();
    const debugPort = await listen(debugReservation);
    await new Promise((resolve, reject) => debugReservation.close((error) => error ? reject(error) : resolve()));
    browser = spawn(chromiumPath, ["--headless=new", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", "--disable-background-networking", "--no-first-run", "--remote-allow-origins=*", `--remote-debugging-port=${debugPort}`, `--user-data-dir=${profile}`, "about:blank"], { stdio: "ignore" });
    const debugOrigin = `http://127.0.0.1:${debugPort}`;
    await waitForDebugger(debugOrigin, browser);
    const targetResponse = await fetch(`${debugOrigin}/json/new?${encodeURIComponent(frontendOrigin)}`, { method: "PUT" });
    assert.equal(targetResponse.status, 200);
    const target = await targetResponse.json();
    const socket = new WebSocket(target.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => { socket.addEventListener("open", resolve, { once: true }); socket.addEventListener("error", reject, { once: true }); });
    await cdp(socket, "Emulation.setDeviceMetricsOverride", { width: 360, height: 900, deviceScaleFactor: 1, mobile: true });
    await cdp(socket, "Page.enable");
    await cdp(socket, "Page.navigate", { url: frontendOrigin });
    let browserState;
    for (let attempt = 0; attempt < 80; attempt += 1) {
      const evaluated = await cdp(socket, "Runtime.evaluate", { expression: "({text: document.body.innerText, width: document.documentElement.scrollWidth, viewport: window.innerWidth})", returnByValue: true });
      browserState = evaluated.result?.value;
      if (browserState?.text?.includes("REQ-018") && browserState?.text?.includes("Eliminar plan") && browserState?.text?.includes("Intento att-0008") && browserState?.text?.includes("Origen · telegram")) break;
      await delay(250);
    }
    for (const expected of ["Ejecuciones", "REQ-027", "REQ-018", "running", "paused", "Última señal de vida", "M3", "Tarea T15a", "Intento att-0008", "Cancelar intento", "Reabrir", "Aprobar y ejecutar", "Enviar respuestas", "Cancelar plan", "Eliminar plan", "Historial de comandos", "Origen · telegram", "Resultado · accepted"]) {
      assert.ok(browserState?.text?.includes(expected), `real panel should render ${expected}`);
    }
    for (let attempt = 0; attempt < 40 && !browserState?.text?.includes("×2"); attempt += 1) {
      await delay(100);
      const evaluated = await cdp(socket, "Runtime.evaluate", { expression: "document.body.innerText", returnByValue: true });
      browserState.text = evaluated.result?.value;
    }
    assert.ok(browserState?.text?.includes("×2"), "paged API events should render through the /flow grouping logic");
    assert.equal(browserState.viewport, 360);
    assert.equal(browserState.width, 360, `page overflowed horizontally at 360 px: ${browserState.width}px`);
    await cdp(socket, "Runtime.evaluate", { expression: "[...document.querySelectorAll('.review-trigger')].find((button) => button.innerText.includes('att-failed-02'))?.click()", returnByValue: true });
    let reviewState;
    for (let attempt = 0; attempt < 40; attempt += 1) {
      const evaluated = await cdp(socket, "Runtime.evaluate", { expression: "({text: document.body.innerText, logs: [...document.querySelectorAll('.review-log')].map((node) => ({height: node.clientHeight, scrollHeight: node.scrollHeight, overflow: getComputedStyle(node).overflowY}))})", returnByValue: true });
      reviewState = evaluated.result?.value;
      if (reviewState?.text?.includes("verification_failed") && reviewState?.logs?.length === 2) break;
      await delay(100);
    }
    for (const heading of ["Causa", "Verificación", "Diff", "Registro del agente", "verification_failed", "npm test", "2 files changed", "src/feature.ts"]) {
      assert.ok(reviewState?.text?.includes(heading), `failure review should render ${heading}`);
    }
    assert.ok(reviewState?.logs.some((box) => box.scrollHeight > box.height && box.overflow === "auto"), "long review logs should scroll inside their own box");
    assert.ok(!reviewState?.text?.includes("fixture-key-value"), "gateway keys must not be displayed");
    assert.ok(!reviewState?.text?.includes("fixture-token-value"), "bot tokens must not be displayed");
    const fill = async (selector, value) => cdp(socket, "Runtime.evaluate", {
      expression: `(() => { const input = document.querySelector(${JSON.stringify(selector)}); if (!input) throw new Error('Missing input ${selector}'); const setter = Object.getOwnPropertyDescriptor(input.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype, 'value').set; setter.call(input, ${JSON.stringify(value)}); input.dispatchEvent(new Event('input', { bubbles: true })); input.dispatchEvent(new Event('change', { bubbles: true })); return true; })()`,
      returnByValue: true,
    });
    const click = async (selector) => cdp(socket, "Runtime.evaluate", {
      expression: `(() => { const button = document.querySelector(${JSON.stringify(selector)}); if (!button) throw new Error('Missing button ${selector}'); button.click(); return true; })()`,
      returnByValue: true,
    });
    await fill(".cancel-form input", "Stop the stalled attempt");
    await click(".cancel-form button");
    for (let attempt = 0; attempt < 40 && gateway.commands.length < 1; attempt += 1) await delay(100);
    assert.equal(gateway.commands[0]?.type, "cancel-attempt");
    assert.equal(gateway.commands[0]?.reason, "Stop the stalled attempt");
    assert.equal(gateway.commands[0]?.target.attemptId, "att-0008");
    assert.equal(gateway.commands[0]?.target.project, "lotm");
    for (let attempt = 0; attempt < 40; attempt += 1) {
      const ready = await cdp(socket, "Runtime.evaluate", { expression: "[...document.querySelectorAll('button')].some((button) => button.innerText === 'Reabrir' && !button.disabled)", returnByValue: true });
      if (ready.result?.value) break;
      await delay(100);
    }
    await cdp(socket, "Runtime.evaluate", { expression: "[...document.querySelectorAll('button')].find((button) => button.innerText === 'Reabrir')?.click()", returnByValue: true });
    for (let attempt = 0; attempt < 40 && gateway.commands.length < 2; attempt += 1) await delay(100);
    assert.equal(gateway.commands[1]?.type, "reopen");
    assert.equal(gateway.commands[1]?.target.taskId, "T2");
    let stale;
    for (let attempt = 0; attempt < 40; attempt += 1) {
      stale = await cdp(socket, "Runtime.evaluate", { expression: "document.body.innerText.includes('El estado cambió')", returnByValue: true });
      if (stale.result?.value) break;
      await delay(100);
    }
    assert.equal(stale?.result?.value, true, "stale preconditions should explain that the state changed");
    const buttonState = (label, scope = "document") => cdp(socket, "Runtime.evaluate", { expression: `(() => { const button = [...${scope}.querySelectorAll('button')].find((node) => node.innerText === ${JSON.stringify(label)}); return button ? button.disabled : null; })()`, returnByValue: true }).then((result) => result.result?.value);
    assert.equal(await buttonState("Aprobar y ejecutar"), true, "approve must stay disabled until the REQ id is typed");
    await fill('[aria-label="Escribe REQ-027 para confirmar"]', "REQ-02");
    assert.equal(await buttonState("Aprobar y ejecutar"), true, "a partial REQ id must not enable approve");
    await fill('[aria-label="Escribe REQ-027 para confirmar"]', "REQ-027");
    assert.equal(await buttonState("Aprobar y ejecutar"), false, "the typed REQ id enables approve");
    await cdp(socket, "Runtime.evaluate", { expression: "[...document.querySelectorAll('button')].find((button) => button.innerText === 'Cancelar plan')?.click()", returnByValue: true });
    for (let attempt = 0; attempt < 40 && gateway.commands.length < 3; attempt += 1) await delay(100);
    assert.equal(gateway.challenges[0]?.typedReq, "REQ-027", "destructive confirmation should issue a server challenge only after typing the REQ id");
    assert.equal(gateway.commands[2]?.confirmation?.challengeId, "challenge-token-0123456789");
    await cdp(socket, "Runtime.evaluate", { expression: "[...document.querySelectorAll('button')].find((button) => button.innerText === 'Aprobar y ejecutar')?.click()", returnByValue: true });
    for (let attempt = 0; attempt < 40 && gateway.commands.length < 4; attempt += 1) await delay(100);
    assert.deepEqual([gateway.commands[3]?.type, gateway.commands[3]?.target, gateway.commands[3]?.precondition], ["approve", { kind: "plan", project: "lotm", req: "REQ-027" }, { state: "review" }]);
    assert.equal(gateway.commands[3]?.confirmation?.typedReq, "REQ-027");
    assert.equal(gateway.challenges[1]?.typedReq, "REQ-027", "approve asks the gateway for a challenge with the typed REQ id");

    await click('[aria-label="Ronda 2"] input[type=radio]');
    assert.equal(await buttonState("Enviar respuestas"), true, "a round with an unanswered question cannot be sent");
    await fill('[aria-label="Ronda 2"] textarea', "Nada más");
    await click('[aria-label="Ronda 2"] button');
    for (let attempt = 0; attempt < 40 && gateway.commands.length < 5; attempt += 1) await delay(100);
    assert.deepEqual([gateway.commands[4]?.type, gateway.commands[4]?.target.roundId, gateway.commands[4]?.answer], ["answer-round", "round-02", { q1: { choice: "a" }, q2: { text: "Nada más" } }]);

    for (let attempt = 0; attempt < 40; attempt += 1) {
      if (await buttonState("Reintentar", `document.querySelector('[aria-label="Decisión T2:2"]')`) === false) break;
      await delay(100);
    }
    const decisionText = await cdp(socket, "Runtime.evaluate", { expression: "document.querySelector('[aria-label=\"Decisión T2:2\"]').innerText", returnByValue: true });
    for (const expected of ["Reintentar", "Gasta un intento", "Para el scheduler", "recomendada"]) assert.ok(decisionText.result?.value.includes(expected), `decision should show ${expected}`);
    await cdp(socket, "Runtime.evaluate", { expression: "[...document.querySelectorAll('[aria-label=\"Decisión T2:2\"] button')].find((button) => button.innerText === 'Reintentar')?.click()", returnByValue: true });
    for (let attempt = 0; attempt < 40 && gateway.commands.length < 6; attempt += 1) await delay(100);
    assert.deepEqual([gateway.commands[5]?.type, gateway.commands[5]?.requestId, gateway.commands[5]?.option, gateway.commands[5]?.precondition, gateway.commands[5]?.target.kind], ["answer-decision", "T2:2", "retry", { state: "paused" }, "run"]);
    socket.close();
  } catch (error) {
    if (error?.code === "ENOENT") assert.fail(`Chromium was not found at ${chromiumPath}; set CHROMIUM_PATH to a local Chromium binary`);
    throw error;
  } finally {
    if (browser && browser.exitCode === null) { browser.kill("SIGTERM"); await once(browser, "close"); }
    if (next && next.exitCode === null) { next.kill("SIGTERM"); await once(next, "close"); }
    if (gateway?.listening) { gateway.close(); await once(gateway, "close"); }
    if (debugReservation?.listening) { debugReservation.close(); await once(debugReservation, "close"); }
    if (profile) await rm(profile, { recursive: true, force: true });
  }
});
