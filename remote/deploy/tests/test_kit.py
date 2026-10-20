from pathlib import Path
import re
import shutil
import subprocess
import unittest


DEPLOY = Path(__file__).parents[1]
ROOT = DEPLOY.parents[1]


class DeploymentKitTests(unittest.TestCase):
    def test_systemd_unit_validates_offline(self):
        unit = DEPLOY / "bitacora-gateway.service"
        if shutil.which("systemd-analyze"):
            result = subprocess.run(["systemd-analyze", "verify", str(unit)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            content = unit.read_text()
            self.assertIn("[Service]", content)
            self.assertIn("ExecStart=", content)
        self.assertIn("Environment=GATEWAY_BIND=172.20.0.1", unit.read_text())
        self.assertIn("Environment=GATEWAY_PORT=8790", unit.read_text())

    def test_caddy_block_and_deploy_entrypoint_use_host_gateway_offline(self):
        caddyfile = DEPLOY / "Caddyfile"
        config = caddyfile.read_text()
        self.assertRegex(config, r"(?m)^flow\.example\.com\s*\{")
        self.assertRegex(config, r"(?m)^\s*reverse_proxy\s+172\.20\.0\.1:8790\s*$")
        self.assertEqual(config.count("{"), config.count("}"))
        caddy = shutil.which("caddy")
        if caddy:
            result = subprocess.run([caddy, "validate", "--config", str(caddyfile)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run([str(DEPLOY / "deploy.sh"), "--check"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("172.20.0.1:8790", result.stdout)
        self.assertIn("Environment=GATEWAY_BIND=172.20.0.1", (DEPLOY / "bitacora-gateway.service").read_text())
        env_example = (DEPLOY / "gateway.env.example").read_text()
        self.assertIn("GATEWAY_BIND=", env_example)
        self.assertIn("set GATEWAY_BIND to 172.20.0.1", env_example)
        result = subprocess.run([str(DEPLOY / "rollback.sh"), "--check"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_env_example_has_all_keys_without_values(self):
        expected = {
            "LAPTOP_ORIGIN", "FLOW_GATEWAY_KEY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID",
            "GATEWAY_DATABASE", "GATEWAY_BIND", "GATEWAY_PORT", "UPSTREAM_TIMEOUT", "PROBE_INTERVAL",
            "GITHUB_CLIENT_ID", "GITHUB_CLIENT_SECRET", "SESSION_SECRET", "FLOW_FRONTEND_ORIGIN",
            "GITHUB_AUTHORIZE_URL", "GITHUB_TOKEN_URL", "GITHUB_USER_URL",
        }
        lines = (DEPLOY / "gateway.env.example").read_text().splitlines()
        found = {line.split("=", 1)[0] for line in lines if line and not line.startswith("#")}
        self.assertEqual(found, expected)
        self.assertTrue(all(re.fullmatch(r"[A-Z][A-Z0-9_]*=", line) for line in lines if line and not line.startswith("#")))

    def test_runbook_gives_rollback_for_each_step(self):
        text = (ROOT / "remote/docs/runbook.md").read_text()
        self.assertRegex(text, r"(?ms)^\d+\. .+?Rollback: .+(?=^\d+\. |\Z)")


if __name__ == "__main__":
    unittest.main()
