"""Offline checks of the go-live kit (unit, Caddy block, env example, scripts, runbook, OAuth cookie contract)."""

from __future__ import annotations

import http.client
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

DEPLOY = Path(__file__).resolve().parents[1]
REMOTE = DEPLOY.parent
RUNBOOK = REMOTE / "docs" / "runbook.md"
GATEWAY = REMOTE / "gateway"


def env_keys(text: str) -> tuple[set[str], set[str]]:
    required, optional = set(), set()
    for line in text.splitlines():
        m = re.fullmatch(r"(#\s*)?([A-Z][A-Z0-9_]*)=(.*)", line.strip())
        if m:
            assert m.group(3) == "", f"{m.group(2)} must have no value"
            (optional if m.group(1) else required).add(m.group(2))
    return required, optional


class UnitTest(unittest.TestCase):
    def test_unit_structure(self):
        text = (DEPLOY / "bitacora-gateway.service").read_text()
        sections = re.findall(r"^\[(\w+)\]$", text, re.M)
        self.assertEqual(sections, ["Unit", "Service", "Install"])
        for key in ("ExecStart=", "EnvironmentFile=", "Restart=always", "NoNewPrivileges=true", "WantedBy="):
            self.assertIn(key, text)
        self.assertIn("/opt/bitacora-gateway/current/gateway/main.py", text)

    @unittest.skipUnless(shutil.which("systemd-analyze"), "systemd-analyze unavailable")
    def test_systemd_analyze_offline(self):
        for unit in ("bitacora-gateway.service", "advin-bitacora-tunnel.service", "bitacora-remote.service"):
            r = subprocess.run(["systemd-analyze", "verify", "--man=no", str(DEPLOY / unit)],
                               capture_output=True, text=True)
            bad = [l for l in r.stderr.splitlines() if "Failed to parse" in l or "Unknown" in l or "Invalid" in l]
            self.assertEqual(bad, [], r.stderr)


    def test_gateway_unit_keeps_state_private_and_is_hardened(self):
        text = (DEPLOY / "bitacora-gateway.service").read_text()
        for key in ("UMask=0077", "StateDirectoryMode=0700", "ProtectSystem=strict", "PrivateDevices=true",
                    "RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX", "CapabilityBoundingSet="):
            self.assertIn(key, text)

    def test_laptop_listener_unit_reads_key_from_a_private_env_file_without_values(self):
        text = (DEPLOY / "bitacora-remote.service").read_text()
        self.assertIn("EnvironmentFile=%h/.config/bitacora-remote/remote.env", text)
        self.assertIn("serve-remote", text)
        self.assertNotRegex(text, r"FLOW_GATEWAY_KEY=\S")
        required, optional = env_keys((DEPLOY / "remote.env.example").read_text())
        self.assertEqual((required, optional), ({"FLOW_GATEWAY_KEY"}, set()))


class CaddyTest(unittest.TestCase):
    def test_block_syntax(self):
        text = (DEPLOY / "Caddyfile").read_text()
        code = "\n".join(l.split("#")[0] for l in text.splitlines())
        depth = 0
        for ch in re.sub(r"\{\$\w+\}", "", code):
            depth += ch == "{"
            depth -= ch == "}"
            self.assertGreaterEqual(depth, 0)
        self.assertEqual(depth, 0)
        self.assertRegex(code, r"(?m)^flow\.example\.com\s*\{")
        self.assertIn("reverse_proxy 172.20.0.1:8790", code)
        self.assertIn("flush_interval -1", code)
        self.assertRegex(code, r"request_body\s*\{\s*max_size \d+KB")

    @unittest.skipUnless(shutil.which("caddy"), "caddy unavailable")
    def test_caddy_validate(self):
        r = subprocess.run(["caddy", "validate", "--config", str(DEPLOY / "Caddyfile"), "--adapter", "caddyfile"],
                           capture_output=True, text=True, env={"GATEWAY_API_HOST": "api.example.test", "PATH": "/usr/bin:/bin"})
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_callback_not_registered_on_api_host(self):
        code = (DEPLOY / "Caddyfile").read_text()
        self.assertIn("FRONTEND origin", code)
        self.assertNotRegex(code, r"(?m)^[^#\n]*/api/auth/callback")


class EnvExampleTest(unittest.TestCase):
    def test_lists_every_key_without_values(self):
        required, optional = env_keys((DEPLOY / "gateway.env.example").read_text())
        source = "".join((GATEWAY / n).read_text() for n in ("config.py", "auth.py"))
        used = set(re.findall(r'(?:values|env)(?:\.get)?\[?\(?"([A-Z][A-Z0-9_]+)"', source))
        used |= set(re.findall(r'"([A-Z][A-Z0-9_]{3,})"', source.split("names = (", 1)[1].split(")", 1)[0]))
        used |= set(re.findall(r'"([A-Z][A-Z0-9_]{3,})"', source.split('names = ("GITHUB', 1)[1].split(")", 1)[0])) if 'names = ("GITHUB' in source else set()
        self.assertTrue(used >= {"LAPTOP_ORIGIN", "SESSION_SECRET", "GATEWAY_PORT", "GITHUB_USER_URL"}, used)
        self.assertEqual(used, required | optional)
        self.assertFalse(required & optional)
        self.assertNotIn("GITHUB_CALLBACK_URL", required | optional)

    def test_host_gateway_override_is_documented_without_a_value(self):
        text = (DEPLOY / "gateway.env.example").read_text()
        self.assertIn("set GATEWAY_BIND to 172.20.0.1", text)
        self.assertRegex(text, r"(?m)^GATEWAY_BIND=$")


class ScriptTest(unittest.TestCase):
    def test_syntax_and_dry_run(self):
        for name in ("deploy.sh", "rollback.sh"):
            self.assertEqual(subprocess.run(["bash", "-n", str(DEPLOY / name)]).returncode, 0)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "releases" / "old").mkdir(parents=True)
            (root / "current").symlink_to(root / "releases" / "old")
            env = {"GATEWAY_ROOT": str(root), "PATH": "/usr/bin:/bin"}
            r = subprocess.run([str(DEPLOY / "deploy.sh"), str(GATEWAY), "--dry-run"], capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("systemctl restart bitacora-gateway", r.stdout)
            self.assertEqual((root / "current").resolve(), (root / "releases" / "old").resolve())
            (root / "previous").symlink_to(root / "releases" / "old")
            r = subprocess.run([str(DEPLOY / "rollback.sh"), "--dry-run"], capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, 0, r.stderr)
            r = subprocess.run([str(DEPLOY / "rollback.sh"), "--dry-run"], capture_output=True, text=True,
                               env={**env, "GATEWAY_ROOT": str(root / "none")})
            self.assertEqual(r.returncode, 2)

    def test_legacy_offline_check_entrypoints(self):
        r = subprocess.run([str(DEPLOY / "deploy.sh"), "--check"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("172.20.0.1:8790", r.stdout)
        r = subprocess.run([str(DEPLOY / "rollback.sh"), "--check"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)


class RunbookTest(unittest.TestCase):
    def test_every_step_has_rollback(self):
        text = RUNBOOK.read_text()
        parts = re.split(r"(?m)^## (Step \d+:.*)$", text)
        steps = parts[1::2]
        bodies = parts[2::2]
        self.assertGreaterEqual(len(steps), 6)
        for title, body in zip(steps, bodies):
            self.assertRegex(body, r"(?m)^Rollback:", title)

    def test_each_step_is_explicitly_numbered_and_has_rollback(self):
        text = RUNBOOK.read_text()
        steps = re.findall(r"(?ms)^## Step (\d+):.*?^Rollback: .+?(?=^## Step |\Z)", text)
        self.assertEqual(len(steps), 7)

    def test_env_files_are_installed_private_and_listener_has_a_step(self):
        text = RUNBOOK.read_text()
        self.assertIn("install -m 0600 -o root -g root remote/deploy/gateway.env.example", text)
        self.assertIn("bitacora-remote.service", text)
        self.assertIn("install -m 0600 remote/deploy/remote.env.example", text)

    def test_callback_on_frontend_origin(self):
        text = RUNBOOK.read_text()
        self.assertIn("<FLOW_FRONTEND_ORIGIN>/api/auth/callback", text)
        self.assertRegex(text, r"Do \*\*not\*\* register the API host")
        self.assertNotIn("GITHUB_CALLBACK_URL", text)


class OAuthCookieContractTest(unittest.TestCase):
    """Real gateway HTTP entry point: cookie attributes that make a frontend-host callback work."""

    def setUp(self):
        sys.path.insert(0, str(GATEWAY))
        self.addCleanup(sys.path.remove, str(GATEWAY))
        from auth import OAuthConfig
        from server import create_server

        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config = OAuthConfig(
            client_id="id", client_secret="s" * 8, session_secret="x" * 32,
            frontend_origin="https://flow.vercel.app", database_path=str(Path(self.tmp.name) / "g.db"),
        )
        self.server = create_server(self.config, ("127.0.0.1", 0))
        self.addCleanup(self.server.server_close)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.shutdown)

    def get(self, path, cookie=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_address[1], timeout=5)
        conn.request("GET", path, headers={"Cookie": cookie} if cookie else {})
        r = conn.getresponse()
        r.read()
        return r

    def test_login_sets_lax_state_and_frontend_callback(self):
        r = self.get("/api/auth/login")
        self.assertEqual(r.status, 302)
        redirect = parse_qs(urlsplit(r.getheader("Location")).query)["redirect_uri"][0]
        self.assertEqual(redirect, "https://flow.vercel.app/api/auth/callback")
        cookie = r.getheader("Set-Cookie")
        for attr in ("HttpOnly", "Secure", "SameSite=Lax", "Path=/api/auth/callback"):
            self.assertIn(attr, cookie)
        self.assertNotIn("Domain=", cookie)

    def test_callback_without_state_cookie_is_rejected(self):
        # What an API-host callback looks like: the browser holds the cookie for the frontend host only.
        r = self.get("/api/auth/login")
        state = parse_qs(urlsplit(r.getheader("Location")).query)["state"][0]
        denied = self.get(f"/api/auth/callback?code=c&state={state}")
        self.assertEqual(denied.status, 400)


class BrowserCookieTest(unittest.TestCase):
    WEB = REMOTE / "web"

    @unittest.skipUnless((WEB / "node_modules").is_dir() and shutil.which("node") and Path("/usr/bin/chromium").exists(),
                         "web dependencies or Chromium unavailable")
    def test_chromium_keeps_lax_state_and_strict_session_on_frontend_host(self):
        r = subprocess.run(["node", "--test", "tests/oauth-browser.test.mjs"], cwd=self.WEB, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
