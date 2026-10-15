from __future__ import annotations

import dataclasses
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

import bt_scheduler_laya as local_laya
import bt_scheduler_laya_worker as laya_worker
from bt_scheduler_decision import ChooserFailure, LayaChoice
from bt_scheduler_decision.tests.support import candidate, request


def fake_command(source: str) -> tuple[str, ...]:
    return sys.executable, "-u", "-c", source


class LocalLayaWorkerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def test_auto_explicitly_prefers_cuda_and_uses_cpu_when_cuda_is_missing(self):
        self.assertEqual(laya_worker._select_device("auto", True), "cuda")
        self.assertEqual(laya_worker._select_device("auto", False), "cpu")
        self.assertEqual(laya_worker._select_device("cpu", True), "cpu")
        self.assertEqual(laya_worker._select_device("cuda", False), "cuda")

    def test_worker_refuses_to_load_torch_without_a_finite_no_swap_cgroup(self):
        root = self.root / "cgroup"
        scope = root / "worker"
        scope.mkdir(parents=True)
        (scope / "memory.max").write_text("67108864", encoding="ascii")
        (scope / "memory.swap.max").write_text("0", encoding="ascii")
        cgroup = self.root / "cgroup.txt"
        cgroup.write_text("0::/worker\n", encoding="ascii")

        self.assertEqual(laya_worker._verify_memory_boundary(128 * 1024**2, cgroup_file=cgroup,
                                                             cgroup_root=root), (67108864, 0))
        (scope / "memory.swap.max").write_text("max", encoding="ascii")
        with self.assertRaisesRegex(ValueError, "finite"):
            laya_worker._verify_memory_boundary(128 * 1024**2, cgroup_file=cgroup, cgroup_root=root)

    def test_user_systemd_scope_enforces_memory_limit_and_kills_only_oversized_worker(self):
        systemd_run = shutil.which("systemd-run")
        if systemd_run is None:
            self.skipTest("systemd-run is unavailable")
        prefix = [systemd_run, "--user", "--scope", "--quiet", "--property=MemoryMax=67108864",
                  "--property=MemorySwapMax=0", "--property=OOMPolicy=kill", "--"]
        probe = subprocess.run(prefix + [sys.executable, "-c", (
            "from pathlib import Path; p=Path('/proc/self/cgroup').read_text().split('::',1)[1].strip(); "
            "d=Path('/sys/fs/cgroup')/p.lstrip('/'); print((d/'memory.max').read_text().strip()+chr(58)+"
            "(d/'memory.swap.max').read_text().strip())")],
            capture_output=True, text=True, timeout=15, check=False)
        if probe.returncode != 0:
            self.skipTest("user systemd manager cannot create a bounded scope")
        self.assertEqual(probe.stdout.strip(), "67108864:0")
        oversized = subprocess.run(prefix + [sys.executable, "-c", (
            "x=bytearray(192*1024*1024); "
            "[x.__setitem__(i,1) for i in range(0,len(x),4096)]; print('unexpected success')")],
            capture_output=True, text=True, timeout=15, check=False)
        self.assertNotEqual(oversized.returncode, 0)
        self.assertNotIn("unexpected success", oversized.stdout)

    def test_real_worker_argv_is_scoped_by_finite_memory_and_no_swap_limits(self):
        python = self.root / "venv" / "bin" / "python"
        python.parent.mkdir(parents=True)
        python.touch()
        config = local_laya.LocalLayaConfig(self.root, "english", worker_memory_limit_bytes=5 * 1024**3)
        client = local_laya.LocalLayaClient(config)

        argv = client._argv()

        self.assertEqual(argv[0].rsplit("/", 1)[-1], "systemd-run")
        self.assertIn("--property=MemoryMax=5368709120", argv)
        self.assertIn("--property=MemorySwapMax=0", argv)
        self.assertEqual(argv[-1], str(config.worker_memory_limit_bytes))

    def test_worker_environment_preserves_only_the_systemd_user_bus_connection(self):
        config = local_laya.LocalLayaConfig(self.root, "english")
        client = local_laya.LocalLayaClient(config)
        with patch.dict(os.environ, {
                "XDG_RUNTIME_DIR": "/run/user/1000", "DBUS_SESSION_BUS_ADDRESS": "unix:path=/run/user/1000/bus",
                "SYSTEMD_BUS_ADDRESS": "unix:path=/run/user/1000/systemd/private", "CLAUDE_CONFIG_DIR": "/secret"}):
            environment = client._environment()
        self.assertEqual(environment["XDG_RUNTIME_DIR"], "/run/user/1000")
        self.assertEqual(environment["DBUS_SESSION_BUS_ADDRESS"], "unix:path=/run/user/1000/bus")
        self.assertEqual(environment["SYSTEMD_BUS_ADDRESS"], "unix:path=/run/user/1000/systemd/private")
        self.assertNotIn("CLAUDE_CONFIG_DIR", environment)

    def test_checkpoint_registry_matches_the_verified_installer_manifest(self):
        setup_path = Path(__file__).resolve().parents[1] / "setup_bt_scheduler_laya.py"
        spec = importlib.util.spec_from_file_location("setup_bt_scheduler_laya", setup_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        setup = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(setup)
        self.assertEqual(set(local_laya.CHECKPOINTS), set(setup.CHECKPOINTS))
        for name, entry in setup.CHECKPOINTS.items():
            self.assertEqual(local_laya.CHECKPOINTS[name][1], entry["revision"])
            self.assertEqual(local_laya.CHECKPOINTS[name][2], entry["sha256"])
            self.assertEqual(laya_worker.CHECKPOINTS[name], (entry["revision"], entry["sha256"]))

    def test_worker_is_lazy_persistent_and_offline(self):
        source = """
import json, os, sys
for line in sys.stdin:
    item = json.loads(line)
    print(json.dumps({"request_id": item["request_id"], "ok": True,
                      "result": {"answers": {}},
                      "metrics": {"offline": os.environ.get("HF_HUB_OFFLINE"),
                                  "cuda_visible": os.environ.get("CUDA_VISIBLE_DEVICES")}}), flush=True)
"""
        client = local_laya.LocalLayaClient(
            local_laya.LocalLayaConfig(self.root, "english"), command=fake_command(source))
        self.assertIsNone(client._process)

        first = client.predict({"task": "one"}, {}, "en")
        process_id = client._process.pid
        second = client.predict({"task": "two"}, {}, "es")

        self.assertEqual(first, {"answers": {}})
        self.assertEqual(second, {"answers": {}})
        self.assertEqual(client._process.pid, process_id)
        self.assertEqual(client.last_metrics["offline"], "1")
        self.assertNotIn("CLAUDE_CONFIG_DIR", client._environment())
        client.close()
        self.assertIsNone(client._process)

    def test_choice_maps_back_only_to_a_candidate_and_reports_metrics(self):
        source = """
import json, sys
for line in sys.stdin:
    item = json.loads(line)
    print(json.dumps({"request_id": item["request_id"], "ok": True,
                      "result": {"answers": {"route": {"type": "choice", "choice": "option-2",
                                                           "answer_confidence": 0.91}}},
                      "metrics": {"device": "cpu", "inference_ms": 12.5}}), flush=True)
"""
        client = local_laya.LocalLayaClient(
            local_laya.LocalLayaConfig(self.root, "english"), command=fake_command(source))
        choices = (candidate(profile="z-profile", rank=0),
                   candidate(provider="codex", model="sol", profile="a-profile", rank=1))
        request_value = request(candidates=choices)
        request_value = dataclasses.replace(request_value,
                                            checkpoint_revision=local_laya.CHECKPOINTS["english"][1])

        result = client.choose(request_value, choices)

        self.assertIsInstance(result, LayaChoice)
        self.assertEqual(result.route_id, sorted(choices, key=lambda item: item.route_id)[1].route_id)
        self.assertEqual(result.checkpoint_revision, local_laya.CHECKPOINTS["english"][1])
        self.assertEqual(client.last_metrics["device"], "cpu")
        client.close()

    def test_prompt_receives_only_sanitized_classification_evidence_kinds(self):
        choices = (candidate(profile="z-profile", rank=0),
                   candidate(provider="codex", model="sol", profile="a-profile", rank=1))
        original = request(candidates=choices)
        dimensions = ("complexity", "scope", "duration", "risk", "coupling", "confidence")
        safe_evidence = {name: {"valid": True, "reference_kinds": ("file", "spec"), "reference_count": 2}
                         for name in dimensions}
        task = dataclasses.replace(original.task, classification_evidence=safe_evidence)
        request_value = dataclasses.replace(original, task=task,
                                            checkpoint_revision=local_laya.CHECKPOINTS["english"][1])
        client = local_laya.LocalLayaClient(local_laya.LocalLayaConfig(self.root, "english"))

        payload, _ = client._decision_payload(request_value, choices)

        self.assertEqual(payload["state"]["classification_evidence"]["risk"],
                         {"validated": True, "reference_kinds": ["file", "spec"]})
        serialized = str(payload["state"]["classification_evidence"])
        self.assertNotIn("REQ-013", serialized)
        self.assertNotIn("/home/", serialized)
        client.close()

    def test_requests_serialize_and_have_independent_ids(self):
        source = """
import json, sys, time
for line in sys.stdin:
    item = json.loads(line)
    time.sleep(0.002)
    print(json.dumps({"request_id": item["request_id"], "ok": True, "result": {"id": item["request_id"]}}), flush=True)
"""
        client = local_laya.LocalLayaClient(
            local_laya.LocalLayaConfig(self.root, "english"), command=fake_command(source))
        with ThreadPoolExecutor(max_workers=8) as pool:
            responses = list(pool.map(lambda _: client.predict({}, {}, "en"), range(16)))
        self.assertEqual(sorted(item["id"] for item in responses), list(range(1, 17)))
        client.close()

    def test_timeout_opens_circuit_and_fails_closed(self):
        source = "import sys,time\nfor line in sys.stdin:\n time.sleep(1)\n"
        client = local_laya.LocalLayaClient(
            local_laya.LocalLayaConfig(self.root, "english", deadline_seconds=0.05,
                                       circuit_failures=1, circuit_open_seconds=10),
            command=fake_command(source))
        with self.assertRaisesRegex(ChooserFailure, "laya_timeout"):
            client.predict({}, {}, "en")
        with self.assertRaisesRegex(ChooserFailure, "laya_circuit_open"):
            client.predict({}, {}, "en")
        client.close()

    def test_worker_exit_maps_to_unavailable_without_shell(self):
        client = local_laya.LocalLayaClient(
            local_laya.LocalLayaConfig(self.root, "english"), command=fake_command("raise SystemExit(3)"))
        with self.assertRaises(ChooserFailure) as raised:
            client.predict({}, {}, "en")
        self.assertEqual(raised.exception.reason, "laya_unavailable")
        client.close()

    def test_repeated_unlisted_choices_open_circuit_and_fail_closed(self):
        source = '''
import json, sys
for line in sys.stdin:
    item = json.loads(line)
    print(json.dumps({"request_id": item["request_id"], "ok": True,
                      "result": {"answers": {"route": {"type": "choice", "choice": "unknown-option",
                                                           "answer_confidence": 0.99}}}}), flush=True)
'''
        client = local_laya.LocalLayaClient(
            local_laya.LocalLayaConfig(self.root, "english", circuit_failures=2, circuit_open_seconds=10),
            command=fake_command(source))
        choices = (candidate(profile="one", rank=0),
                   candidate(provider="codex", model="sol", profile="two", rank=1))
        request_value = dataclasses.replace(request(candidates=choices),
                                            checkpoint_revision=local_laya.CHECKPOINTS["english"][1])
        try:
            for _ in range(2):
                with self.assertRaises(ChooserFailure) as raised:
                    client.choose(request_value, choices)
                self.assertEqual(raised.exception.reason, "laya_runtime_error")
            with self.assertRaises(ChooserFailure) as opened:
                client.choose(request_value, choices)
            self.assertEqual(opened.exception.reason, "laya_circuit_open")
            self.assertIsNone(client._process)
        finally:
            client.close()


if __name__ == "__main__":
    unittest.main()
