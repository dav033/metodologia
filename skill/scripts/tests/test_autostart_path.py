"""A boot-time script must not carry per-shell fnm directories: they vanish at the next boot and take `codex` with them."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_autostart  # noqa: E402


class StablePath(unittest.TestCase):
    def test_a_multishell_entry_becomes_the_real_node_directory_and_a_dead_one_is_dropped(self):
        with tempfile.TemporaryDirectory() as tmp:
            real = (Path(tmp) / "node-versions" / "v24" / "installation" / "bin").resolve()
            real.mkdir(parents=True)
            shell = Path(tmp) / "fnm_multishells" / "1_2"
            shell.mkdir(parents=True)
            (shell / "bin").symlink_to(real)
            gone = str(Path(tmp) / "fnm_multishells" / "9_9" / "bin")
            value = os.pathsep.join([str(shell / "bin"), "/usr/bin", gone, "/usr/bin", str(real)])
            self.assertEqual(bt_autostart.stable_path(value), os.pathsep.join([str(real), "/usr/bin"]))

    def test_a_multishell_on_the_default_alias_keeps_the_alias(self):
        """D-256: fnm's multishell links to `aliases/default`; resolving it fully baked one node version into the engine's
        PATH (v24.21.0), which `fnm default` and an uninstall leave behind. One hop keeps the alias."""
        with tempfile.TemporaryDirectory() as tmp:
            fnm = Path(tmp) / "fnm"
            for version in ("v24", "v26"):
                (fnm / "node-versions" / version / "installation" / "bin").mkdir(parents=True)
            (fnm / "aliases").mkdir()
            (fnm / "aliases" / "default").symlink_to(fnm / "node-versions" / "v24" / "installation")
            shell = Path(tmp) / "fnm_multishells" / "1094_1"
            shell.parent.mkdir()
            shell.symlink_to(fnm / "aliases" / "default")
            baked = bt_autostart.stable_path(os.pathsep.join([str(shell / "bin"), "/usr/bin"]))
            self.assertEqual(baked, os.pathsep.join([str(fnm / "aliases" / "default" / "bin"), "/usr/bin"]))
            (fnm / "aliases" / "default").unlink()                     # `fnm default 26`, then v24 is uninstalled
            (fnm / "aliases" / "default").symlink_to(fnm / "node-versions" / "v26" / "installation")
            self.assertTrue((Path(baked.split(os.pathsep)[0]) / ".").resolve().is_dir())
            self.assertIn("v26", str(Path(baked.split(os.pathsep)[0]).resolve()))

    def test_an_ordinary_path_is_unchanged_apart_from_duplicates(self):
        self.assertEqual(bt_autostart.stable_path("/usr/bin:/home/x/.local/bin:/usr/bin"), "/usr/bin:/home/x/.local/bin")


if __name__ == "__main__":
    unittest.main()
