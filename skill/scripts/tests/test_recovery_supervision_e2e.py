"""REQ-029 T11: the shipped entry points together. A real run is created by `scheduler-watch` (CLI -> owner -> executor stores), then
the real `serve` process and `scheduler-op` are driven over HTTP and the CLI: the recovery preview writes nothing, the plan page
shows the recovery and self-healing panels, and every control needs the token, is bound to the preview and the stop generation, and
leaves its effect on disk. (The run is not executed to the end here: the fake provider is not routable without the M2 stores the
live machine has; execution paths are covered by the in-process runtime tests.)"""
from __future__ import annotations

import hashlib
import json
import re
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
SCRIPTS = HERE.parent
from recovery_process_support import FixtureScenario, RecoveryProcessHarness

TASK = {"id": "T1", "milestone_id": "M1", "title": "make a file", "objective": "make a file", "repository": "app", "after": [],
        "complexity": "low", "scope": "isolated_fix", "estimated_minutes": 5, "risk": "low", "coupling": "low",
        "confidence": "high", "estimate_rationale": "tiny", "classification_evidence": {}, "expected_paths": ["made.txt"],
        "shared_resources": [], "acceptance_criteria": ["file exists"], "covers": [], "kind": "implement",
        "verification": [{"type": "command", "value": "test -s made.txt", "purpose": "file exists", "category": "functional"}]}


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class SupervisionE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        provider = HERE / "fake_providers" / "provider.py"
        cls.tools = tempfile.TemporaryDirectory(prefix="e2e-provider-")
        cls.wrapper = Path(cls.tools.name) / "codex.sh"
        cls.wrapper.write_text(f'#!/bin/sh\nexec {sys.executable} {provider} codex "$@"\n')
        cls.wrapper.chmod(0o755)
        cls.harness = RecoveryProcessHarness(FixtureScenario(project="e2e", requirement="REQ-001", tasks=(TASK,),
                                                             repositories={"app": "repos/app"}), {"codex": cls.wrapper})
        cls.rdir = cls.harness.rdir
        watch = cls.harness.start_watch()
        cls.harness.wait_for(lambda: cls._task_state() == "ready", timeout=90, interval=1.0, label="the run to exist (T1 ready)")
        watch.terminate()
        watch.wait(timeout=10)
        cls.harness.close_owners = True
        subprocess.run(["pkill", "-f", f"scheduler-run REQ-001"], check=False)
        time.sleep(1.0)

    @classmethod
    def tearDownClass(cls):
        cls.harness.close()
        cls.tools.cleanup()

    @classmethod
    def _task_state(cls):
        done = cls.harness.cli("scheduler-op", "REQ-001", "status", timeout=30)
        try:
            return json.loads(done.stdout).get("task_states", {}).get("T1")
        except ValueError:
            return None

    def files_digest(self) -> str:
        digest = hashlib.sha256()
        for path in sorted(p for p in self.rdir.rglob("*") if p.is_file()):
            if path.suffix in {".sqlite3-shm", ".db-shm", ".db-wal", ".lock", ".sqlite3-wal"} or path.name.startswith("RUN.projection"):
                continue
            digest.update(path.relative_to(self.rdir).as_posix().encode() + hashlib.sha256(path.read_bytes()).digest())
        return digest.hexdigest()

    def test_01_the_preview_writes_nothing_and_never_diagnoses_or_activates(self):
        before = self.files_digest()
        done = self.harness.cli("scheduler-op", "REQ-001", "recovery-preview", timeout=60)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        preview = json.loads(done.stdout)
        self.assertEqual(preview["schema_version"], "recovery-preview/1")
        self.assertIs(preview["diagnosis_invoked"], False)
        self.assertIs(preview["decision_answered"], False)
        self.assertIs(preview["activation_present"], False)
        self.assertEqual(self.files_digest(), before)                                    # a read: no file of the run changed
        self.assertFalse((self.rdir / "RUN.recovery-policy.json").exists())
        type(self).preview = preview

    def test_02_the_page_controls_need_the_token_and_leave_their_effects_on_disk(self):
        port = free_port()
        server = subprocess.Popen([sys.executable, str(SCRIPTS / "bitacora.py"), "--project", "e2e", "serve", "--port", str(port)],
                                  cwd=self.harness.temp, env=self.harness.env(), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        self.addCleanup(server.kill)
        base = f"http://127.0.0.1:{port}"
        self.harness.wait_for(lambda: self._up(base), timeout=30, interval=0.3, label="the web server")
        page = urllib.request.urlopen(f"{base}/plans/e2e/REQ-001", timeout=20).read().decode()
        self.assertIn("Recuperación diagnóstica", page)
        self.assertIn("solo vista previa", page)                                         # opening the view did not enable anything
        self.assertIn("Autocuración", page)
        self.assertFalse((self.rdir / "RUN.recovery-policy.json").exists())
        token = (self.harness.bitacora_root / ".state" / "server-token").read_text().strip()
        digest = re.search(r'name="preview" value="([0-9a-f]{64})"', page).group(1)
        generation = re.search(r'name="stop_generation" value="(\d+)"', page).group(1)
        url = f"{base}/plans/e2e/REQ-001"

        def post(path, **form):
            data = urllib.parse.urlencode(form).encode()
            request = urllib.request.Request(f"{url}/{path}", data=data, headers={"Origin": base})
            try:
                return urllib.request.build_opener(NoRedirect).open(request, timeout=20).status, ""
            except urllib.error.HTTPError as error:
                return error.code, error.headers.get("Location", "")

        self.assertEqual(post("heal", action="stop")[0], 403)                            # no token: refused
        self.assertFalse((self.rdir / "RUN.healing.off").exists())
        self.assertEqual(post("heal", token=token, action="stop")[0], 303)
        self.assertTrue((self.rdir / "RUN.healing.off").exists())                        # with the token: healing is off
        post("heal", token=token, action="start")
        self.assertFalse((self.rdir / "RUN.healing.off").exists())
        stale = post("recovery", token=token, action="enable", preview="0" * 64, stop_generation=generation)
        self.assertIn("msg=", stale[1])
        self.assertFalse((self.rdir / "RUN.recovery-policy.json").exists())              # a stale preview enables nothing
        moved = post("recovery", token=token, action="enable", preview=digest, stop_generation=str(int(generation) + 1))
        self.assertFalse((self.rdir / "RUN.recovery-policy.json").exists())              # nor does a moved stop generation
        post("recovery", token=token, action="enable", preview=digest, stop_generation=generation)
        policy = json.loads((self.rdir / "RUN.recovery-policy.json").read_text())
        self.assertEqual(policy["preview_digest"], digest)                               # bound to the preview the owner saw
        self.assertRegex(policy["authorization_ref"], r"^owner-control:[0-9a-f]{32}$")
        post("recovery", token=token, action="stop", stop_generation=generation)
        status = json.loads(self.harness.cli("scheduler-op", "REQ-001", "status", timeout=30).stdout)
        self.assertTrue(status["hold"])                                                  # the stop holds the run
        after = urllib.request.urlopen(url, timeout=20).read().decode()
        self.assertIn("activa", after)
        self.assertIn("msg=", moved[1])                                                  # the refusal is explained on the page

    @staticmethod
    def _up(base: str) -> bool:
        try:
            urllib.request.urlopen(f"{base}/", timeout=2)
            return True
        except urllib.error.HTTPError:
            return True
        except OSError:
            return False


if __name__ == "__main__":
    unittest.main()
