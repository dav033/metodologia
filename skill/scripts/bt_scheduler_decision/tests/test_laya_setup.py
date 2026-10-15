"""Security regressions for the isolated Laya checkpoint verifier."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "setup_bt_scheduler_laya.py"
SPEC = importlib.util.spec_from_file_location("setup_bt_scheduler_laya", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("could not load the Laya setup script")
SETUP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SETUP)


class LayaCheckpointPathTests(unittest.TestCase):
    def _write_manifest(self, checkpoints: Path) -> None:
        (checkpoints / "manifest.json").write_text(
            json.dumps({
                "schema_version": 1,
                "laya_source_commit": SETUP.UPSTREAM_COMMIT,
                "checkpoints": {
                    name: {
                        "revision": spec["revision"],
                        "model_sha256": spec["sha256"],
                        "model_bytes": spec["size"],
                    }
                    for name, spec in SETUP.CHECKPOINTS.items()
                },
            }),
            encoding="utf-8",
        )

    def test_rejects_symlinked_intermediate_encoder_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "install"
            checkpoints = root / "checkpoints"
            checkpoints.mkdir(parents=True)
            self._write_manifest(checkpoints)
            outside = Path(temporary) / "outside"
            outside.mkdir()
            (outside / "config.json").write_text("{}", encoding="utf-8")
            english = checkpoints / "english"
            english.mkdir()
            (english / "encoder").symlink_to(outside, target_is_directory=True)

            with self.assertRaisesRegex(RuntimeError, "checkpoint path missing or unsafe"):
                SETUP.verify_checkpoints(root)

    def test_rejects_symlinked_intermediate_tokenizer_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "install"
            checkpoints = root / "checkpoints"
            checkpoints.mkdir(parents=True)
            self._write_manifest(checkpoints)
            outside = Path(temporary) / "outside"
            outside.mkdir()
            (outside / "tokenizer.json").write_text("{}", encoding="utf-8")
            english = checkpoints / "english"
            english.mkdir()
            (english / "encoder").mkdir()
            (english / "tokenizer").symlink_to(outside, target_is_directory=True)

            with self.assertRaisesRegex(RuntimeError, "checkpoint path missing or unsafe"):
                SETUP.verify_checkpoints(root)

    def test_rejects_symlinked_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "install"
            checkpoints = root / "checkpoints"
            checkpoints.mkdir(parents=True)
            external_manifest = Path(temporary) / "manifest.json"
            external_manifest.write_text("{}", encoding="utf-8")
            (checkpoints / "manifest.json").symlink_to(external_manifest)

            with self.assertRaisesRegex(RuntimeError, "checkpoint path missing or unsafe"):
                SETUP.verify_checkpoints(root)


if __name__ == "__main__":
    unittest.main()
