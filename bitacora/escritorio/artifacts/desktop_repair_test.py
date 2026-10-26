"""Regression checks for local desktop repair; no real suspend or display changes."""

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HOME = Path.home()
spec = importlib.util.spec_from_file_location(
    "media", HOME / ".config/waybar/scripts/media.py"
)
media = importlib.util.module_from_spec(spec)
spec.loader.exec_module(media)


class MediaTests(unittest.TestCase):
    def test_no_player_hides_only_media(self):
        with patch.object(media, "query", return_value=""):
            self.assertEqual(media.payload(), {"text": "", "class": "stopped"})

    def test_paused_metadata_is_escaped(self):
        with patch.object(media, "query", side_effect=["Paused", "<title> & artist"]):
            result = media.payload()
        self.assertEqual(result["class"], "paused")
        self.assertIn("&lt;title&gt; &amp; artist", result["text"])

    def test_playing_keeps_controls_available(self):
        with patch.object(media, "query", side_effect=["Playing", "Title"]):
            self.assertEqual(media.payload()["class"], "playing")


class RestoreTests(unittest.TestCase):
    def run_restore(self, streaming):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stub = root / "hyprctl"
            stub.write_text('''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
with open(os.environ["TEST_CALLS"], "a") as output:
    output.write(json.dumps(args) + "\\n")
if args[:2] == ["monitors", "all"]:
    print(json.dumps([{"name":"eDP-1", "disabled":False}, {"name":"moonlight"}]))
elif args[:1] == ["workspaces"]:
    print(json.dumps([{"id":4, "monitor":"moonlight"}]))
else:
    print("ok")
''')
            stub.chmod(0o755)
            calls_file = root / "calls"
            if streaming:
                (root / "sunshine-streaming").touch()
            env = dict(os.environ, HOME=str(root), XDG_RUNTIME_DIR=str(root),
                       PATH=f"{root}:{os.environ['PATH']}", TEST_CALLS=str(calls_file))
            result = subprocess.run(
                ["bash", str(HOME / ".local/bin/remote-headless"), "on"],
                env=env, capture_output=True, text=True, timeout=10, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            return [json.loads(line) for line in calls_file.read_text().splitlines()]

    def test_local_restore_moves_before_removing_virtual_output(self):
        calls = self.run_restore(False)
        move = next(i for i, call in enumerate(calls)
                    if call[0] == "dispatch" and "workspace.move" in call[1])
        remove = calls.index(["output", "remove", "moonlight"])
        self.assertLess(move, remove)

    def test_active_stream_preserves_virtual_output(self):
        calls = self.run_restore(True)
        self.assertNotIn(["output", "remove", "moonlight"], calls)
        self.assertTrue(any(call[0] == "eval" and 'mirror = "moonlight"' in call[1]
                            for call in calls))


class LiveConfigurationTests(unittest.TestCase):
    def test_loaded_lid_policies_suspend(self):
        for name in ("HandleLidSwitch", "HandleLidSwitchExternalPower", "HandleLidSwitchDocked"):
            result = subprocess.run(
                ["busctl", "get-property", "org.freedesktop.login1",
                 "/org/freedesktop/login1", "org.freedesktop.login1.Manager", name],
                capture_output=True, text=True, check=True, timeout=3,
            )
            self.assertEqual(result.stdout.strip(), 's "suspend"')

    def test_all_five_workspaces_are_persistent_and_local(self):
        result = subprocess.run(["hyprctl", "-j", "workspaces"], capture_output=True,
                                text=True, check=True, timeout=3)
        workspaces = {item["id"]: item for item in json.loads(result.stdout)}
        for number in range(1, 6):
            self.assertTrue(workspaces[number]["ispersistent"])
            self.assertEqual(workspaces[number]["monitor"], "eDP-1")

    def test_bar_follows_compositor_fullscreen_visibility(self):
        result = subprocess.run(["hyprctl", "-j", "layers"], capture_output=True,
                                text=True, check=True, timeout=3)
        bars = [layer for monitor in json.loads(result.stdout).values()
                for level in monitor["levels"].values() for layer in level
                if layer["namespace"] == "waybar"]
        self.assertEqual(len(bars), 1)
        workspace = subprocess.run(["hyprctl", "-j", "activeworkspace"],
                                   capture_output=True, text=True, check=True, timeout=3)
        fullscreen = json.loads(workspace.stdout)["hasfullscreen"]
        self.assertEqual(bars[0]["alpha"], 0 if fullscreen else 1)
        self.assertGreater(bars[0]["h"], 0)


if __name__ == "__main__":
    unittest.main()
