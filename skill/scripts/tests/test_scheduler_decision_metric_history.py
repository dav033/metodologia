from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bt_scheduler_decision_adapter import metric_samples_for_route
from bt_scheduler_monitor import MetricSample


def sample(provider: str = "codex", *, key: str = "codex/profile-a/model-a/output_tokens",
           value: int | None = 12, quality: str = "reported", profile: str | None = "profile-a",
           model: str | None = "model-a", name: str = "output_tokens", unit: str = "tokens") -> MetricSample:
    return MetricSample("1.0.0", "sha256:" + "a" * 64, provider, name, value, unit,
                        "provider_reported", "2026-10-15T16:00:00Z", quality, 1 if value is not None else 0,
                        key, profile_id=profile, model=model)


class MetricHistoryTests(unittest.TestCase):
    def test_m1_m2_adapter_imports_when_optional_m4_modules_are_absent(self):
        scripts = Path(__file__).resolve().parents[1]
        code = """
import importlib.abc
import sys

class BlockMonitorImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if (fullname == "bt_scheduler_monitor_adapter" or fullname == "bt_scheduler_monitor"
                or fullname.startswith("bt_scheduler_monitor.") or fullname.startswith("bt_scheduler_m4")):
            raise ModuleNotFoundError(fullname, name=fullname)
        return None

sys.meta_path.insert(0, BlockMonitorImports())
import bt_scheduler_decision_adapter as m2
import bt_scheduler_adapter as m1

assert m1.decision_sources is m2
assert m2.metric_samples_for_route((), provider="codex", profile=None, model=None,
                                   name="output_tokens", unit="tokens", comparability_key="unknown") == ()
"""
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                                check=False, cwd=scripts,
                                env={**os.environ, "PYTHONPATH": str(scripts)})

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_route_history_keeps_provider_and_comparability_boundaries(self):
        codex = sample()
        claude = sample("claude", key="claude/profile-a/model-a/output_tokens")
        other_key = sample(key="codex/profile-b/model-a/output_tokens", profile="profile-b")
        alternate_key = sample(key="codex/profile-a/model-a/output_tokens-v2")
        unknown = sample(key="unknown", profile=None, model=None)

        found = metric_samples_for_route((codex, claude, other_key, alternate_key, unknown), provider="codex",
                                         profile="profile-a", model="model-a", name="output_tokens", unit="tokens",
                                         comparability_key="codex/profile-a/model-a/output_tokens")

        self.assertEqual(found, (codex,))
        self.assertEqual((found[0].source, found[0].unit, found[0].quality, found[0].sample_count,
                          found[0].observed_at, found[0].comparability_key),
                         ("provider_reported", "tokens", "reported", 1, "2026-10-15T16:00:00Z",
                          "codex/profile-a/model-a/output_tokens"))

    def test_unknown_profile_and_model_are_selected_only_for_exact_none_dimensions(self):
        unknown_dimensions = sample(key="unknown", profile=None, model=None)
        known_profile = sample(key="unknown", profile="profile-a", model=None)

        found = metric_samples_for_route((unknown_dimensions, known_profile), provider="codex", profile=None,
                                         model=None, name="output_tokens", unit="tokens",
                                         comparability_key="unknown")

        self.assertEqual(found, (unknown_dimensions,))

    def test_unknown_quota_is_preserved_as_unknown_not_zero_or_infinity(self):
        quota = MetricSample("1.0.0", "sha256:" + "b" * 64, "codex", "quota_remaining", None, "requests",
                             "provider_reported", "2026-10-15T16:00:00Z", "unknown", 0, "unknown",
                             profile_id="profile-a", model="model-a")

        found = metric_samples_for_route((quota,), provider="codex", profile="profile-a", model="model-a",
                                         name="quota_remaining", unit="requests", comparability_key="unknown")

        self.assertEqual(found, (quota,))
        self.assertIsNone(found[0].value)
        self.assertEqual((found[0].quality, found[0].sample_count), ("unknown", 0))

        zero = sample(key="codex/profile-a/model-a/quota_remaining", value=0, name="quota_remaining", unit="requests")
        known_zero = metric_samples_for_route((quota, zero), provider="codex", profile="profile-a", model="model-a",
                                              name="quota_remaining", unit="requests",
                                              comparability_key="codex/profile-a/model-a/quota_remaining")
        self.assertEqual(known_zero, (zero,))

    def test_unvalidated_metric_inputs_are_rejected(self):
        with self.assertRaisesRegex(TypeError, "validated MetricSample"):
            metric_samples_for_route(({"provider": "codex"},), provider="codex", profile="p", model="m",
                                     name="output_tokens", unit="tokens", comparability_key="unknown")


if __name__ == "__main__":
    unittest.main()
