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

    def test_an_ordinary_path_is_unchanged_apart_from_duplicates(self):
        self.assertEqual(bt_autostart.stable_path("/usr/bin:/home/x/.local/bin:/usr/bin"), "/usr/bin:/home/x/.local/bin")


if __name__ == "__main__":
    unittest.main()
