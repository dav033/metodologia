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

test("real panel entrypoint renders every contract run and refreshes live snapshots at 360 px", { timeout: 90_000 }, async () => {
  let gateway;
  let sessionContractObserved = false;
  let next;
  let browser;
  let profile;
  let debugReservation;
  try {
    gateway = await createMockGatewayServer();
    const mockGatewayHandler = gateway.listeners("request")[0];
    gateway.removeAllListeners("request");
    gateway.on("request", (request, response) => {
      if (request.method === "GET" && request.url === "/api/auth/session") {
        sessionContractObserved = true;
        response.writeHead(200, { "content-type": "application/json; charset=utf-8" });
        response.end(JSON.stringify({ login: "dav033" }));
        return;
      }
      mockGatewayHandler(request, response);
    });
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
      if (browserState?.text?.includes("REQ-018") && browserState?.text?.includes("Eliminar plan") && browserState?.text?.includes("Intento att-0008")) break;
      await delay(250);
    }
    for (const expected of ["Ejecuciones", "REQ-027", "REQ-018", "running", "paused", "Última señal de vida", "M3", "Tarea T15a", "T15c · Failure review screen", "rejected", "Intento att-0008", "Cancelar intento", "Reabrir", "Criterios de aceptación", "Cancelar plan", "Eliminar plan"]) {
      assert.ok(browserState?.text?.includes(expected), `real panel should render ${expected}`);
    }
    const reviewLink = await cdp(socket, "Runtime.evaluate", { expression: "(() => { const link = document.querySelector('a[href*=" + JSON.stringify("taskId=T15c") + "]'); if (!link) throw new Error('Missing review link'); link.scrollIntoView(); const bounds = link.getBoundingClientRect(); return { x: bounds.x + bounds.width / 2, y: bounds.y + bounds.height / 2 }; })()", returnByValue: true });
    const reviewPoint = reviewLink.result?.value;
    assert.ok(reviewPoint, "review link should have a visible position");
    await cdp(socket, "Input.dispatchMouseEvent", { type: "mouseMoved", x: reviewPoint.x, y: reviewPoint.y });
    await cdp(socket, "Input.dispatchMouseEvent", { type: "mousePressed", x: reviewPoint.x, y: reviewPoint.y, button: "left", clickCount: 1 });
    await cdp(socket, "Input.dispatchMouseEvent", { type: "mouseReleased", x: reviewPoint.x, y: reviewPoint.y, button: "left", clickCount: 1 });
    let fixtureReview = "";
    for (let attempt = 0; attempt < 300; attempt += 1) {
      const evaluated = await cdp(socket, "Runtime.evaluate", { expression: "document.body.innerText", returnByValue: true });
      fixtureReview = evaluated.result?.value ?? "";
      if (fixtureReview.includes("Fallo de fixture en rejected")) break;
      await delay(100);
    }
    assert.ok(fixtureReview.includes("Fallo de fixture en rejected"), `fixture rejected task should load its reviewAttempt through the real review route within 30 seconds: ${fixtureReview}`);
    await cdp(socket, "Page.navigate", { url: frontendOrigin });
    for (let attempt = 0; attempt < 70; attempt += 1) {
      const evaluated = await cdp(socket, "Runtime.evaluate", { expression: "document.body.innerText", returnByValue: true });
      browserState.text = evaluated.result?.value ?? "";
      if (browserState.text.includes("Tarea T15a")) break;
      await delay(100);
    }
    assert.equal(sessionContractObserved, true, "panel should consume the gateway's { login } session response");
    for (let attempt = 0; attempt < 40 && !browserState?.text?.includes("×2"); attempt += 1) {
      await delay(100);
      const evaluated = await cdp(socket, "Runtime.evaluate", { expression: "document.body.innerText", returnByValue: true });
      browserState.text = evaluated.result?.value;
    }
    assert.ok(browserState?.text?.includes("×2"), "SSE messages should render through the /flow grouping logic");
    assert.equal(browserState.viewport, 360);
    assert.equal(browserState.width, 360, `page overflowed horizontally at 360 px: ${browserState.width}px`);
    const waitForText = async (expected) => {
      for (let attempt = 0; attempt < 70; attempt += 1) {
        const evaluated = await cdp(socket, "Runtime.evaluate", { expression: "document.body.innerText", returnByValue: true });
        if (evaluated.result?.value?.includes(expected)) return evaluated.result.value;
        await delay(100);
      }
      assert.fail(`open panel did not refresh its snapshot to show ${expected} within 7 seconds`);
    };
    const waitForTaskState = async (taskId, expected) => {
      for (let attempt = 0; attempt < 70; attempt += 1) {
        const expression = `([...document.querySelectorAll('.task-card')].find((card) => card.querySelector('.row-heading strong')?.textContent?.startsWith(${JSON.stringify(taskId)}))?.querySelector('.state')?.textContent ?? '')`;
        const evaluated = await cdp(socket, "Runtime.evaluate", { expression, returnByValue: true });
        if (evaluated.result?.value === expected) return;
        await delay(100);
      }
      assert.fail(`task ${taskId} did not refresh to ${expected}`);
    };
    await delay(1200);
    const readsBeforePoll = gateway.snapshotReads.length;
    for (let attempt = 0; attempt < 60 && gateway.snapshotReads.length === readsBeforePoll; attempt += 1) await delay(100);
    assert.ok(gateway.snapshotReads.length > readsBeforePoll, "open panel should poll the gateway snapshot every five seconds without an SSE event");
    const pollGap = gateway.snapshotReads.at(-1) - gateway.snapshotReads.at(-2);
    assert.ok(pollGap >= 2500 && pollGap <= 5500, `expected a five-second snapshot poll, observed ${pollGap} ms`);
    const updateSnapshot = (update) => {
      const nextSnapshot = JSON.parse(gateway.snapshot);
      update(nextSnapshot);
      nextSnapshot.generatedAt = new Date().toISOString();
      nextSnapshot.cursor = `mock-cursor-${Date.now()}`;
      gateway.snapshot = JSON.stringify(nextSnapshot);
    };
    const originalSnapshot = gateway.snapshot;
    updateSnapshot((nextSnapshot) => {
      nextSnapshot.runs[0].tasks[0].state = "verifying";
      nextSnapshot.runs[0].tasks[0].activeAttempt.state = "verifying";
    });
    assert.ok((await waitForText("verifying")).includes("M6"), "task progress should refresh the active module and state");
    updateSnapshot((nextSnapshot) => {
      nextSnapshot.runs[0].tasks[0].state = "failed";
      nextSnapshot.runs[0].tasks[0].activeAttempt.state = "failed";
    });
    await waitForText("failed");
    updateSnapshot((nextSnapshot) => {
      nextSnapshot.runs[0].state = "rejected";
      nextSnapshot.runs[0].tasks[0].state = "rejected";
      delete nextSnapshot.runs[0].tasks[0].activeAttempt;
      nextSnapshot.runs[0].tasks[0].reviewAttempt = { id: "att-rejected-1", live: false };
    });
    await waitForTaskState("T15a", "rejected");
    const rejectedState = await waitForText("Reabrir ejecución");
    assert.ok(rejectedState.includes("Reabrir") && rejectedState.includes("Reabrir ejecución"), "rejected tasks and runs should expose recovery controls");
    await cdp(socket, "Runtime.evaluate", { expression: "document.querySelector('a[href*=" + JSON.stringify("taskId=T15a") + "]').click()", returnByValue: true });
    const waitForReview = async () => {
      let lastText = "";
      for (let attempt = 0; attempt < 70; attempt += 1) {
        const evaluated = await cdp(socket, "Runtime.evaluate", { expression: "document.body.innerText", returnByValue: true });
        lastText = evaluated.result?.value ?? "";
        if (lastText.includes("Fallo de fixture en rejected")) return lastText;
        await delay(100);
      }
      assert.fail(`failure review route did not load the rejected task's reviewAttempt: ${lastText}`);
    };
    const rejectedReview = await waitForReview();
    for (const expected of ["CAUSA", "SALIDA DE VERIFICACIÓN", "ESTADÍSTICA DEL DIFF", "FINAL DEL LOG", "att-rejected-1", "Fin de log"]) {
      assert.ok(rejectedReview.includes(expected), `real failure review should render ${expected}`);
    }
    assert.doesNotMatch(rejectedReview, /ghp_abcdefghijklmnopqrstuvwxyz123456|abc\.def\.ghi/);
    await cdp(socket, "Page.navigate", { url: frontendOrigin });
    await waitForText("rejected");
    updateSnapshot((nextSnapshot) => {
      nextSnapshot.runs[0].state = "finished";
      nextSnapshot.runs[0].tasks[0].state = "completed";
      delete nextSnapshot.runs[0].tasks[0].activeAttempt;
      delete nextSnapshot.runs[0].tasks[0].reviewAttempt;
      delete nextSnapshot.runs[0].activeAttempt;
    });
    await waitForText("finished");
    await waitForText("completed");
    updateSnapshot((nextSnapshot) => { nextSnapshot.laptop.online = false; });
    await waitForText("LAPTOP SIN CONEXIÓN");
    gateway.snapshot = originalSnapshot;
    await waitForText("Intento att-0008");
    const fill = async (selector, value) => cdp(socket, "Runtime.evaluate", {
      expression: `(() => { const input = document.querySelector(${JSON.stringify(selector)}); if (!input) throw new Error('Missing input ${selector}'); const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set; setter.call(input, ${JSON.stringify(value)}); input.dispatchEvent(new Event('input', { bubbles: true })); input.dispatchEvent(new Event('change', { bubbles: true })); return true; })()`,
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
    for (let attempt = 0; attempt < 40; attempt += 1) {
      const ready = await cdp(socket, "Runtime.evaluate", { expression: "[...document.querySelectorAll('.task-card')].find((card) => card.querySelector('.row-heading strong')?.textContent?.startsWith('T2'))?.querySelector('button')?.disabled === false", returnByValue: true });
      if (ready.result?.value) break;
      await delay(100);
    }
    await cdp(socket, "Runtime.evaluate", { expression: "[...document.querySelectorAll('.task-card')].find((card) => card.querySelector('.row-heading strong')?.textContent?.startsWith('T2'))?.querySelector('button')?.click()", returnByValue: true });
    for (let attempt = 0; attempt < 40 && gateway.commands.length < 2; attempt += 1) await delay(100);
    assert.equal(gateway.commands[1]?.type, "reopen");
    assert.equal(gateway.commands[1]?.target.taskId, "T2");
    await waitForText("Historial de comandos");
    await waitForText("Origen · Web");
    await waitForText("Resultado · accepted");
    for (let attempt = 0; attempt < 40; attempt += 1) {
      const ready = await cdp(socket, "Runtime.evaluate", { expression: "[...document.querySelectorAll('.task-card')].find((card) => card.querySelector('.row-heading strong')?.textContent?.startsWith('T2'))?.querySelector('button')?.disabled === false", returnByValue: true });
      if (ready.result?.value) break;
      await delay(100);
    }
    await fill('[aria-label="Escribe REQ-027"]', "REQ-028");
    const destructiveDisabled = await cdp(socket, "Runtime.evaluate", { expression: "[...document.querySelectorAll('button')].find((button) => button.innerText === 'Eliminar plan')?.disabled", returnByValue: true });
    assert.equal(destructiveDisabled.result?.value, true, "destructive commands must stay disabled unless the exact REQ is typed");
    await fill('[aria-label="Escribe REQ-027"]', "REQ-027");
    await fill('[aria-label="Id del reto de confirmación"]', "challenge-1");
    const destructiveEnabled = await cdp(socket, "Runtime.evaluate", { expression: "[...document.querySelectorAll('button')].find((button) => button.innerText === 'Eliminar plan')?.disabled", returnByValue: true });
    assert.equal(destructiveEnabled.result?.value, false, "typing the exact REQ and challenge should enable destructive commands");
    gateway.nextCommandResponse = { status: 409, body: { code: "STALE_PRECONDITION", message: "stale" } };
    await click(".plans form button.danger");
    await waitForText("El estado cambió");
    await waitForText("Resultado · Rechazado: el estado cambió");
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
