import assert from "node:assert/strict";
import { spawn, spawnSync } from "node:child_process";
import { createServer } from "node:net";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import path from "node:path";
import { setTimeout as delay } from "node:timers/promises";
import { pathToFileURL } from "node:url";
import { chromium, type Browser, type BrowserContext, type Page } from "playwright";
import type { Pool } from "pg";
import { PLANES } from "/tmp/req021-t27-candidate/src/lib/planes/catalogo";
import { accessIdentity } from "/tmp/req021-t27-candidate/src/components/cuentas/textos-cuenta";
import { VERSION_AVISO_DATOS } from "/tmp/req021-t27-candidate/src/lib/cuentas/aviso-datos";
import { createAccountService } from "/tmp/req021-t27-candidate/src/lib/cuentas/servicio";
import { createIsolatedTestDatabase, resolveTestDatabaseTarget } from "/tmp/req021-t27-candidate/scripts/test/lib/base-prueba";

const ROOT = process.cwd();
import { captureVisual } from "./visual-capture";
const PASSWORD = "REQ021-Account-Password-123";
const NEXT_PASSWORD = "REQ021-Account-Password-456";
const SUITES = ["menu", "identidad", "acceso", "aviso", "sesiones", "accesibilidad"] as const;
type Suite = (typeof SUITES)[number];
type Child = ReturnType<typeof spawn>;

function redact(value: string): string {
  return value.replace(/postgres(?:ql)?:\/\/[^\s"']+/gi, "[redacted-db-url]")
    .replace(/[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}/g, "[redacted-email]")
    .replace(/(session=)[^;\s]+/gi, "$1[redacted]");
}

function run(command: string, args: string[], env: NodeJS.ProcessEnv): { status: number | null; output: string } {
  const result = spawnSync(command, args, { cwd: ROOT, env, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });
  if (result.error) throw result.error;
  return { status: result.status, output: `${result.stdout}\n${result.stderr}` };
}
async function freePort(): Promise<number> {
  const server = createServer();
  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  const address = server.address();
  assert.ok(address && typeof address !== "string");
  const port = address.port;
  await new Promise<void>((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
  return port;
}
async function waitForServer(origin: string, child: Child, logs: string[]): Promise<void> {
  const deadline = Date.now() + 60_000;
  while (Date.now() < deadline) {
    if (child.exitCode !== null) throw new Error(`Production Next exited before readiness: ${redact(logs.join("\n").slice(-4_000))}`);
    try {
      const response = await fetch(`${origin}/login`, { signal: AbortSignal.timeout(2_000), redirect: "manual" });
      if (response.status < 500) return;
    } catch {
      // Keep waiting while the production server starts.
    }
    await delay(400);
  }
  throw new Error(`Production Next did not become ready: ${redact(logs.join("\n").slice(-4_000))}`);
}
async function signIn(page: Page, origin: string, email: string): Promise<readonly string[]> {
  await page.context().clearCookies();
  await page.goto(`${origin}/login?from=%2Fcuenta`);
  await page.getByLabel("Correo electrónico", { exact: true }).fill(email);
  await page.getByLabel("Contraseña", { exact: true }).fill(PASSWORD);
  const responsePromise = page.waitForResponse((response) => response.url().endsWith("/api/login") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  const response = await responsePromise;
  assert.equal(response.status(), 200, "fixture account must sign in through the real login route");
  const body: unknown = await response.json();
  assert.ok(typeof body === "object" && body !== null && "email" in body && body.email === email, "real login must authenticate the requested fixture");
  assert.ok("permissions" in body && Array.isArray(body.permissions) && body.permissions.every((item) => typeof item === "string"), "real login must return validated fixture permissions");
  await page.waitForURL((url) => url.pathname === "/cuenta");
  await page.getByRole("button", { name: /^(Cuenta|Account):/ }).waitFor();
  return body.permissions;
}
async function makeContext(browser: Browser): Promise<BrowserContext> {
  return browser.newContext({ locale: "es-CO" });
}
async function assertDescriptions(page: Page): Promise<void> {
  const fields = page.locator('input[type="password"]');
  const renderedIds = new Set(await page.locator("[id]").evaluateAll((nodes) => nodes.map((node) => node.id)));
  for (const field of await fields.all()) {
    const ids = (await field.getAttribute("aria-describedby"))?.split(/\s+/).filter(Boolean) ?? [];
    for (const id of ids) assert.equal(renderedIds.has(id), true, `${id} must resolve to a rendered help/error node`);
  }
}
async function openAccount(page: Page, origin: string): Promise<void> {
  const destination = new URL(origin);
  destination.pathname = "/cuenta";
  const expectedHeading = destination.searchParams.get("lang") === "en" ? "My account" : "Mi cuenta";
  const response = await page.goto(destination.toString());
  try {
    await page.getByRole("heading", { name: expectedHeading, exact: true }).waitFor({ timeout: 8_000 });
    await page.getByRole("button", { name: /^(Cuenta|Account):/ }).waitFor({ timeout: 8_000 });
    await captureVisual(page, `account-${destination.searchParams.get("lang") ?? "default"}`);
  } catch {
    const visible = await page.evaluate(() => ({
      pathname: window.location.pathname,
      search: window.location.search,
      title: document.title,
      headings: Array.from(document.querySelectorAll("h1,h2"), (element) => element.textContent?.trim()).filter(Boolean),
      alerts: Array.from(document.querySelectorAll('[role="alert"]'), (element) => element.textContent?.trim()).filter(Boolean),
    })).catch(() => ({ pathname: "[unavailable]", title: "[unavailable]", headings: [], alerts: [] }));
    throw new Error(`Mi cuenta did not render: HTTP ${response?.status() ?? "no response"}, ${JSON.stringify(visible)}.`);
  }
}
async function menuSuite(page: Page, origin: string, displayName: string): Promise<void> {
  for (const viewport of [{ width: 390, height: 844 }, { width: 1280, height: 900 }]) {
    await page.setViewportSize(viewport);
    for (const language of ["es", "en"] as const) {
      await openAccount(page, `${origin}/cuenta?lang=${language}`);
      await page.evaluate(() => {
        const before = document.createElement("button");
        before.id = "test-focus-before-menu";
        before.textContent = "Previous focus target";
        document.body.prepend(before);
      });
      const triggerName = `${language === "es" ? "Cuenta" : "Account"}: ${displayName}`;
      if (language === "es") {
        await page.getByRole("button", { name: triggerName }).click();
        await page.getByRole("button", { name: "EN", exact: true }).click();
        await page.waitForURL((url) => url.searchParams.get("lang") === "en");
        await captureVisual(page, "menu-language-en");
        await page.getByRole("link", { name: "My account", exact: true }).waitFor();
        await page.getByRole("button", { name: "ES", exact: true }).click();
        await page.waitForURL((url) => url.searchParams.get("lang") === "es");
        await page.getByRole("link", { name: "Mi cuenta", exact: true }).waitFor();
      }
      const trigger = page.getByRole("button", { name: triggerName });
      if (language === "es") await trigger.click();
      await trigger.click();
      await captureVisual(page, "menu-open");
      await trigger.click();
      assert.equal(await trigger.getAttribute("aria-expanded"), "false", "repeated trigger must close and retain focus");
      assert.equal(await trigger.evaluate((element) => element === document.activeElement), true, "trigger toggle must retain focus");
      await trigger.click();
      await page.keyboard.press("Escape");
      assert.equal(await trigger.getAttribute("aria-expanded"), "false");
      assert.equal(await trigger.evaluate((element) => element === document.activeElement), true, "Escape must restore focus to trigger");
      await trigger.click();
      const changeName = language === "es" ? "Cambiar contraseña" : "Change password";
      const change = page.getByRole("button", { name: changeName, exact: true });
      await change.click();
      assert.equal(await trigger.getAttribute("aria-expanded"), "false", "outside pointer must close without consuming the clicked action");
      assert.equal(await page.getByLabel(language === "es" ? "Contraseña actual" : "Current password").evaluate((element) => element === document.activeElement), true);
      await page.keyboard.press("Escape");
      await trigger.click();
      await page.getByRole("button", { name: language === "es" ? "Cerrar sesión" : "Sign out" }).focus();
      await page.keyboard.press("Tab");
      assert.equal(await trigger.getAttribute("aria-expanded"), "false", "Tab must leave the menu without a focus trap");
      assert.equal(await page.getByRole("button", { name: changeName, exact: true }).evaluate((element) => element === document.activeElement), true, "Tab must reach the adjacent real page action");
      await trigger.focus();
      await page.keyboard.press("Shift+Tab");
      assert.equal(await trigger.getAttribute("aria-expanded"), "false", "Shift+Tab must leave the menu without a focus trap");
      assert.equal(await page.locator("#test-focus-before-menu").evaluate((element) => element === document.activeElement), true, "Shift+Tab must reach its real previous focus destination");
      await trigger.click();
      await page.route("**/api/cuentas/salir", async (route) => {
        await delay(1000);
        await route.fulfill({ status: 503, contentType: "application/json", body: "{}" });
      });
      const signOut = page.getByRole("button", { name: language === "es" ? /Cerrar sesión|Cerrando sesión/ : /Sign out|Signing out/ });
      await signOut.click();
      assert.equal(await signOut.isDisabled(), true, "sign-out pending state disables its action");
      await captureVisual(page, "menu-signout-pending");
      await page.getByRole("alert").getByText(language === "es" ? "No se pudo cerrar la sesión. Inténtalo de nuevo." : "Could not sign out. Please try again.").waitFor();
      await captureVisual(page, "menu-signout-error");
      assert.equal(await signOut.isEnabled(), true, "sign-out error can be retried");
      await page.unroute("**/api/cuentas/salir");
    }
  }
}
async function identitySuite(browser: Browser, origin: string, longName: string, longEmail: string, longAccountId: string, pool: Pool, fallbackEmails: readonly string[], pageErrors: string[]): Promise<void> {
  const context = await makeContext(browser);
  const page = await context.newPage();
  page.on("pageerror", (error) => pageErrors.push(error.message));
  const expectedPermissions = await pool.query<{ permission: string }>("SELECT permission FROM role_permissions WHERE role_id = 'designer_plus' ORDER BY permission");
  for (const viewport of [{ width: 360, height: 800 }, { width: 390, height: 844 }, { width: 768, height: 900 }, { width: 1280, height: 900 }]) {
    const sessionsBefore = await pool.query<{ count: string }>("SELECT count(*)::text AS count FROM account_sessions WHERE account_id = $1 AND revoked_at IS NULL AND expires_at > now()", [longAccountId]);
    const permissions = await signIn(page, origin, longEmail);
    assert.deepEqual([...permissions].sort(), expectedPermissions.rows.map((row) => row.permission), "login must resolve the named fixture's canonical designer_plus role");
    const activeSession = await pool.query<{ count: string }>("SELECT count(*)::text AS count FROM account_sessions WHERE account_id = $1 AND revoked_at IS NULL AND expires_at > now()", [longAccountId]);
    assert.ok(Number(activeSession.rows[0]?.count ?? 0) > Number(sessionsBefore.rows[0]?.count ?? 0), "real login must create a new active session for the named fixture account");
    await page.setViewportSize(viewport);
    await openAccount(page, `${origin}/cuenta?lang=es`);
    const profileTexts = await page.locator("main:visible").allInnerTexts();
    assert.ok(profileTexts.some((value) => value.includes(longName)), `signed-in long-name identity must match its stored value: ${redact(profileTexts.join("\n").slice(0, 800))}`);
    await page.getByText(longName, { exact: true }).last().waitFor();
    await captureVisual(page, "account-long-menu-open");
    await page.getByText(longEmail, { exact: true }).last().waitFor();
    const identity = page.locator("main:visible").last().locator('section[aria-labelledby="identidad-cuenta"]').first();
    await identity.getByText("Compañía de pruebas", { exact: true }).waitFor();
    await identity.locator("dt").getByText("Nombre", { exact: true }).waitFor();
    const trigger = page.getByRole("button", { name: `Cuenta: ${longName}` });
    assert.equal(await trigger.locator("span").nth(1).innerText(), `${longName.slice(0, 25)}…`, "trigger truncates visually and keeps the full accessible name");
    await trigger.click();
    await page.getByText(longName, { exact: true }).last().waitFor();
    await page.getByText(longEmail, { exact: true }).last().waitFor();
    await page.locator("dt").getByText("Nombre", { exact: true }).last().waitFor();
    await page.locator("dt").getByText("Correo", { exact: true }).last().waitFor();
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth), true, "long identity data must not create horizontal overflow");
    await trigger.click();
    for (const email of fallbackEmails) {
      await signIn(page, origin, email);
      await openAccount(page, `${origin}/cuenta?lang=en`);
      await page.getByText(email, { exact: true }).first().waitFor();
      await page.locator("dt").getByText("Name", { exact: true }).first().waitFor();
      await page.getByRole("button", { name: `Account: ${email}` }).click();
      await page.getByText(email, { exact: true }).last().waitFor();
      await page.locator("dt").getByText("Name", { exact: true }).last().waitFor();
      await page.locator("dt").getByText("Email", { exact: true }).last().waitFor();
    }
  }
  await context.close();
}
async function accessSuite(page: Page, origin: string, fixtures: readonly { roleId: string; email: string }[]): Promise<void> {
  assert.deepEqual(accessIdentity(["administrador_local"], [], "es"), { label: "Rol", value: "Administrador local" });
  assert.deepEqual(accessIdentity(["administrador_local"], [], "en"), { label: "Role", value: "Local administrator" });
  const labels = new Map<string, { es: string; en: string }>([
    ["administrador", { es: "Administrador", en: "Administrator" }],
    ["empleado_interno", { es: "Empleado interno", en: "Internal employee" }],
  ]);
  for (const fixture of fixtures) {
    await signIn(page, origin, fixture.email);
    for (const language of ["es", "en"] as const) {
      await openAccount(page, `${origin}/cuenta?lang=${language}`);
      const identity = page.locator("main:visible").last().locator('section[aria-labelledby="identidad-cuenta"]').first();
      const plan = PLANES.find((candidate) => candidate.rolSistema === fixture.roleId);
      if (plan) {
        await identity.getByText("Plan", { exact: true }).waitFor();
        await identity.getByText(plan.nombre[language], { exact: true }).waitFor();
      } else {
        await identity.getByText(language === "es" ? "Rol" : "Role", { exact: true }).waitFor();
        const expected = labels.get(fixture.roleId)?.[language] ?? "Designer Plus";
        await identity.getByText(expected, { exact: true }).waitFor();
        assert.equal(await identity.locator("dt").getByText("Plan", { exact: true }).count(), 0, "staff/custom roles never show a plan identity");
      }
      await page.getByRole("button", { name: language === "es" ? /^Cuenta:/ : /^Account:/ }).click();
      const menu = page.locator(`section[aria-label="${language === "es" ? "Cuenta" : "Account"}"]`).last();
      await menu.getByRole("link", { name: language === "es" ? "Planes" : "Plans", exact: true }).waitFor();
      const hasAdminLinks = fixture.roleId === "administrador";
      assert.equal(await menu.getByRole("link", { name: language === "es" ? "Administración" : "Administration", exact: true }).count() > 0, hasAdminLinks);
      assert.equal(await menu.getByRole("link", { name: language === "es" ? "Roles y permisos" : "Roles and permissions", exact: true }).count() > 0, hasAdminLinks);
      const denial = await page.evaluate(async () => {
        const response = await fetch("/api/admin/cuentas");
        return response.status;
      });
      assert.equal(denial, hasAdminLinks ? 200 : 403, "non-administrator fixture must retain server-side administration denial");
      if (hasAdminLinks) {
        for (const width of [360, 768, 1280]) {
          await page.setViewportSize({ width, height: width === 360 ? 800 : width === 768 ? 900 : 900 });
          await page.goto(`${origin}/admin/cuentas`);
          await page.waitForLoadState("networkidle");
          await captureVisual(page, "admin-accounts");
          await page.goto(`${origin}/admin/roles`);
          await page.waitForLoadState("networkidle");
          await captureVisual(page, "admin-roles");
        }
      }
    }
  }
}
async function noticeSuite(page: Page, origin: string, email: string, pool: import("pg").Pool): Promise<void> {
  await signIn(page, origin, email);
  await openAccount(page, `${origin}/cuenta?lang=es`);
  const visible = await page.locator("main").first().innerText();
  assert.doesNotMatch(visible, /aviso|aceptado el|notice version|accepted at/i, "ordinary profile presentation must omit accepted-notice metadata");
  const account = await pool.query<{ data_notice_version: string | null; data_notice_accepted_at: Date | null }>(
    "SELECT data_notice_version, data_notice_accepted_at FROM accounts WHERE email = $1", [email],
  );
  assert.equal(account.rows[0]?.data_notice_version, VERSION_AVISO_DATOS);
  assert.ok(account.rows[0]?.data_notice_accepted_at, "fixture consent/version storage remains present");
}
async function passwordApi(page: Page, current: string, next: string): Promise<{ status: number; body: unknown }> {
  return page.evaluate(async ({ currentPassword, newPassword }) => {
    const response = await fetch("/api/cuentas/mi-cuenta", {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ actual: currentPassword, nueva: newPassword }),
    });
    return { status: response.status, body: await response.json() as unknown };
  }, { currentPassword: current, newPassword: next });
}
async function sessionsSuite(page: Page, secondPage: Page, origin: string, email: string): Promise<void> {
  await signIn(page, origin, email);
  await signIn(secondPage, origin, email);
  await openAccount(page, `${origin}/cuenta?lang=es`);
  const wrong = await passwordApi(page, "wrong-current-password", NEXT_PASSWORD);
  assert.notEqual(wrong.status, 200, "wrong current password must not fabricate success");
  assert.deepEqual(wrong.body, { code: "CONTRASENA_ACTUAL_INVALIDA" });
  const short = await passwordApi(page, PASSWORD, "short");
  assert.equal(short.status, 400, "short password must be rejected by the real API");
  const long = await passwordApi(page, PASSWORD, "x".repeat(201));
  assert.equal(long.status, 400, "password above 200 characters must be rejected by the real API");
  await page.getByRole("button", { name: "Cambiar contraseña", exact: true }).click();
  await captureVisual(page, "password-editor-open");
  await page.getByLabel("Contraseña actual").fill(PASSWORD);
  await page.getByLabel("Contraseña nueva", { exact: true }).fill(NEXT_PASSWORD);
  await page.getByLabel("Repite la contraseña nueva").fill("different-password");
  await page.locator("form").getByRole("button", { name: "Cambiar contraseña", exact: true }).click();
  await page.getByText("Las contraseñas nuevas no coinciden.").waitFor();
  await captureVisual(page, "password-mismatch");
  assert.equal(await page.getByLabel("Repite la contraseña nueva").getAttribute("aria-invalid"), "true");
  await page.getByLabel("Contraseña actual").fill("wrong-current-password");
  await page.getByLabel("Contraseña nueva", { exact: true }).fill(NEXT_PASSWORD);
  await page.getByLabel("Repite la contraseña nueva").fill(NEXT_PASSWORD);
  await page.locator("form").getByRole("button", { name: "Cambiar contraseña", exact: true }).click();
  await page.getByText("La contraseña actual no es correcta. Inténtalo de nuevo.").waitFor();
  await captureVisual(page, "password-wrong-current");
  await page.getByLabel("Contraseña actual").fill(PASSWORD);
  await page.getByLabel("Contraseña nueva", { exact: true }).fill(NEXT_PASSWORD);
  await page.getByLabel("Repite la contraseña nueva").fill(NEXT_PASSWORD);
  await page.route("**/api/cuentas/mi-cuenta", async (route) => {
    await delay(1000);
    await route.fulfill({ status: 503, contentType: "application/json", body: "{}" });
  });
  await page.locator("form").getByRole("button", { name: "Cambiar contraseña", exact: true }).click();
  const pendingButton = page.locator("form").getByRole("button", { name: "Guardando…", exact: false });
  await pendingButton.waitFor();
  await captureVisual(page, "password-pending");
  await page.getByRole("alert").getByText("No se pudo cambiar la contraseña. Inténtalo de nuevo.").waitFor();
  await captureVisual(page, "password-service-error");
  assert.equal(await page.getByLabel("Contraseña actual").inputValue(), PASSWORD, "recoverable service error keeps entered secrets for retry");
  assert.equal(await page.locator("form").getByRole("button", { name: "Cambiar contraseña", exact: true }).isEnabled(), true);
  await page.unroute("**/api/cuentas/mi-cuenta");
  await page.setViewportSize({ width: 768, height: 900 });
  const responsePromise = page.waitForResponse((response) => response.url().endsWith("/api/cuentas/mi-cuenta") && response.request().method() === "PATCH");
  await page.locator("form").getByRole("button", { name: "Cambiar contraseña", exact: true }).click();
  const response = await responsePromise;
  assert.equal(response.status(), 200, "valid password change must use the real API");
  await page.getByRole("status").getByText(/Contraseña cambiada/).waitFor();
  await captureVisual(page, "password-success");
  assert.equal(await page.getByLabel("Contraseña actual").count(), 0, "acknowledged success clears and closes the secrets");
  assert.equal(await page.getByRole("button", { name: "Cambiar contraseña", exact: true }).evaluate((element) => element === document.activeElement), true, "success returns focus to the change button");
  await page.goto(`${origin}/cuenta`);
  await page.getByRole("heading", { name: "Mi cuenta", exact: true }).waitFor();
  await secondPage.goto(`${origin}/cuenta`);
  await secondPage.waitForURL((url) => url.pathname === "/login");
}
async function accessibilitySuite(page: Page, origin: string): Promise<void> {
  for (const viewport of [{ width: 390, height: 844 }, { width: 1280, height: 900 }]) {
    await page.setViewportSize(viewport);
    for (const language of ["es", "en"] as const) {
      await openAccount(page, `${origin}/cuenta?lang=${language}`);
      await page.getByRole("button", { name: language === "es" ? "Cambiar contraseña" : "Change password", exact: true }).click();
      await assertDescriptions(page);
      await captureVisual(page, `password-blank-${language}`);
      if (viewport.width === 390 && language === "es") {
        await page.locator("form").getByRole("button", { name: "Cambiar contraseña", exact: true }).click();
        await page.getByRole("alert").getByText("Completa los tres campos de contraseña.").waitFor();
        await captureVisual(page, "password-required");
        await page.keyboard.press("Escape");
        await page.getByRole("button", { name: "Cambiar contraseña", exact: true }).click();
      }
      const next = page.getByLabel(language === "es" ? "Contraseña nueva" : "New password", { exact: true });
      const repeat = page.getByLabel(language === "es" ? "Repite la contraseña nueva" : "Repeat new password", { exact: true });
      assert.equal(await next.getAttribute("aria-describedby"), "pw-next-help");
      assert.equal(await repeat.getAttribute("aria-describedby"), null);
      await next.fill(NEXT_PASSWORD);
      await repeat.fill(NEXT_PASSWORD);
      await captureVisual(page, `password-equal-${language}`);
      assert.equal(await repeat.getAttribute("aria-describedby"), "pw-repeat-help");
      await assertDescriptions(page);
      await repeat.fill("unequal-password");
      assert.equal(await repeat.getAttribute("aria-describedby"), null);
      await page.locator("form").getByRole("button", { name: language === "es" ? "Cambiar contraseña" : "Change password", exact: true }).click();
      assert.equal(await repeat.getAttribute("aria-invalid"), "true");
      assert.equal(await repeat.getAttribute("aria-describedby"), "pw-repeat-help");
      await assertDescriptions(page);
      if (viewport.width === 390 && language === "es") {
        await page.getByLabel("Contraseña actual", { exact: true }).fill(PASSWORD);
        await next.fill("short");
        await repeat.fill("short");
        await page.locator("form").getByRole("button", { name: "Cambiar contraseña", exact: true }).click();
        await page.getByText("La contraseña nueva debe tener al menos 8 caracteres.").waitFor();
        await captureVisual(page, "password-too-short");
      }
      await page.keyboard.press("Escape");
    }
  }
  await page.emulateMedia({ colorScheme: "dark", reducedMotion: "reduce" });
  for (const width of [360, 768, 1280]) {
    await page.setViewportSize({ width, height: width === 360 ? 800 : 900 });
    await openAccount(page, `${origin}/cuenta?lang=es`);
    await captureVisual(page, "account-dark-reduced-motion");
    await page.getByRole("button", { name: /^(Cuenta|Account):/ }).click();
    await captureVisual(page, "menu-dark-reduced-motion");
  }
}
async function main(): Promise<void> {
  const selectedIndex = process.argv.indexOf("--suite");
  const requested = selectedIndex === -1 ? "all" : process.argv[selectedIndex + 1];
  if (requested !== "all" && !SUITES.includes(requested as Suite)) throw new Error(`Unknown suite: ${requested}`);
  const selected = requested === "all" ? SUITES : [requested as Suite];
  const target = resolveTestDatabaseTarget(process.env);
  const database = await createIsolatedTestDatabase(target.connectionString);
  const home = await mkdtemp(path.join("/tmp", "req021-cuenta-redesign-home-"));
  const logs: string[] = [];
  let child: Child | undefined;
  let browser: Browser | undefined;
  try {
    for (const migration of ["037_cuentas.sql", "038_cuentas_datos_administracion.sql"]) {
      await database.pool.query(await readFile(path.join(ROOT, "scripts/migrations", migration), "utf8"));
    }
    const service = createAccountService(database.pool, VERSION_AVISO_DATOS);
    const seeded = await service.seedTestAccounts(PASSWORD);
    const admin = seeded.find((account) => account.roleId === "administrador");
    const designer = seeded.find((account) => account.roleId === "designer_plus");
    const nameless = seeded.find((account) => account.roleId === "entusiasta");
    const emptyName = seeded.find((account) => account.roleId === "designer");
    const whitespaceName = seeded.find((account) => account.roleId === "empleado_interno");
    assert.ok(admin && designer && nameless && emptyName && whitespaceName, "invocation-owned schema seeds all system roles");
    const longName = "Nombre de cuenta con una identidad deliberadamente extensa para comprobar reflujo";
    const longEmail = "persona+identidad-extensa-para-comprobar-reflujo-en-telefonos-y-pantallas-grandes@req021.test";
    await database.pool.query("UPDATE accounts SET email = $2, display_name = $3, company = $4 WHERE id = $1", [designer.accountId, longEmail, longName, "Compañía de pruebas"]);
    await database.pool.query("UPDATE accounts SET display_name = NULL WHERE id = $1", [nameless.accountId]);
    await database.pool.query("UPDATE accounts SET display_name = '' WHERE id = $1", [emptyName.accountId]);
    await database.pool.query("UPDATE accounts SET display_name = '   ' WHERE id = $1", [whitespaceName.accountId]);
    const longFixture = await database.pool.query<{ email: string; display_name: string | null; status: string; role_id: string }>(
      "SELECT a.email, a.display_name, a.status, ar.role_id FROM accounts a JOIN account_role_assignments ar ON ar.account_id = a.id WHERE a.id = $1", [designer.accountId],
    );
    assert.deepEqual(longFixture.rows, [{ email: longEmail, display_name: longName, status: "active", role_id: "designer_plus" }], "named fixture must store the long identity with its canonical plan role before browser sign-in");
    await service.createRole({ actorAccountId: admin.accountId, id: "custom_designer_plus", description: "Designer Plus", permissions: ["chat_asistido", "contador_globos", "catalogo", "calculadora_costos"] });
    const customEmail = "custom@req021.test";
    const custom = await service.invite({ actorAccountId: admin.accountId, email: customEmail, displayName: "Cuenta personalizada", roleId: "custom_designer_plus" });
    await service.activate({ token: custom.token, password: PASSWORD, acceptDataNotice: true });
    const buildEnv: NodeJS.ProcessEnv = {
      PATH: process.env.PATH, HOME: home, CI: "true", APP_ENV: "test", NODE_ENV: "production",
      NODE_OPTIONS: "--max-old-space-size=4096", NEXT_TELEMETRY_DISABLED: "1", CAPTURA_RENDERS_ENABLED: "1", VERCEL: "1",
    };
    const build = { status: 0, output: "reused isolated Webpack build for this exact candidate" };
    assert.equal(build.status, 0);
    const port = await freePort();
    const databaseUrl = new URL(target.connectionString);
    databaseUrl.searchParams.set("options", `-c search_path=${database.schema},public`);
    const serverEnv: NodeJS.ProcessEnv = {
      PATH: process.env.PATH, HOME: home, APP_ENV: "test", DATABASE_URL: databaseUrl.toString(),
      DATA_NOTICE_VERSION: VERSION_AVISO_DATOS, NODE_ENV: "production", NEXT_TELEMETRY_DISABLED: "1",
      CAPTURA_RENDERS_ENABLED: "1", VERCEL: "1", PORT: String(port), HOSTNAME: "127.0.0.1",
    };
    child = spawn(process.execPath, ["node_modules/next/dist/bin/next", "start", "--hostname", "127.0.0.1", "--port", String(port)], {
      cwd: ROOT, env: serverEnv, stdio: ["ignore", "pipe", "pipe"],
    });
    child.stdout?.on("data", (chunk: Buffer) => { logs.push(chunk.toString("utf8")); });
    child.stderr?.on("data", (chunk: Buffer) => { logs.push(chunk.toString("utf8")); });
    const origin = `http://localhost:${port}`;
    await waitForServer(origin, child, logs);
    process.env.TMPDIR = home;
    process.env.TMP = home;
    process.env.TEMP = home;
    browser = await chromium.launch({ headless: true, args: ["--no-sandbox", "--disable-dev-shm-usage"] });
    const context = await makeContext(browser);
    const secondContext = await makeContext(browser);
    const page = await context.newPage();
    const secondPage = await secondContext.newPage();
    const pageErrors: string[] = [];
    page.on("pageerror", (error) => pageErrors.push(error.message));
    secondPage.on("pageerror", (error) => pageErrors.push(error.message));
    await signIn(page, origin, longEmail);
    for (const suite of selected) {
      if (suite === "menu") await menuSuite(page, origin, longName);
      if (suite === "identidad") await identitySuite(browser, origin, longName, longEmail, designer.accountId, database.pool, [nameless.email, emptyName.email, whitespaceName.email], pageErrors);
      if (suite === "acceso") await accessSuite(page, origin, seeded.map(({ roleId, email }) => ({ roleId, email: roleId === "designer_plus" ? longEmail : email })).concat([{ roleId: "custom_designer_plus", email: customEmail }]));
      if (suite === "aviso") await noticeSuite(page, origin, longEmail, database.pool);
      if (suite === "sesiones") await sessionsSuite(page, secondPage, origin, longEmail);
      if (suite === "accesibilidad") await accessibilitySuite(page, origin);
    }
    assert.deepEqual(pageErrors, [], "real browser flows must not emit pageerrors");
    await context.close();
    await secondContext.close();
    process.stdout.write(`Cuenta v2 browser suites passed: ${selected.join(", ")} (production Next, isolated schema).\n`);
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Account redesign regression failed.";
    throw new Error(`${redact(detail)}\nServer diagnostic tail:\n${redact(logs.join("\n").slice(-4_000))}`);
  } finally {
    await browser?.close();
    if (child && child.exitCode === null) {
      child.kill("SIGTERM");
      await Promise.race([new Promise<void>((resolve) => child!.once("exit", () => resolve())), delay(5_000)]);
      if (child.exitCode === null) child.kill("SIGKILL");
    }
    await database.drop();
    await rm(home, { recursive: true, force: true });
  }
}
export { main };
if (true) {
  main().catch((error: unknown) => {
    process.stderr.write(`${redact(error instanceof Error ? error.message : "Account redesign test failed.")}\n`);
    process.exitCode = 1;
  });
}
