"""Cross-platform launch contracts, with real POSIX argument and process checks."""
import json
import os
import plistlib
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_autostart
import bt_platform as host
import bt_runsession
import bt_secrets
import bt_server
import bt_vcs
import bt_workspace


class PlatformTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="metodologia-platform-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "space ' dólar $ ñ"
        self.root.mkdir()

    @unittest.skipIf(os.name == "nt", "Windows paths are case insensitive")
    def test_workspace_index_preserves_distinct_posix_path_case(self):
        self.assertNotEqual(bt_workspace._key(self.root / "Repo"), bt_workspace._key(self.root / "repo"))

    def test_detached_process_flags_follow_the_host(self):
        for platform in ("linux", "macos", "windows"):
            with self.subTest(platform=platform), patch.object(host, "platform", return_value=platform):
                options = host.detached_options()
                if platform == "windows":
                    self.assertGreater(options["creationflags"], 0)
                else:
                    self.assertEqual(options, {"start_new_session": True})

    @unittest.skipIf(os.name == "nt", "requires bash")
    def test_posix_script_preserves_prompt_paths_and_environment_as_data(self):
        output = self.root / "output.json"
        program = self.root / "receiver.py"
        program.write_text("import json,os,pathlib,sys\n"
                           "pathlib.Path(sys.argv[1]).write_text(json.dumps([sys.argv[2],os.environ['BITACORA_ROOT'],os.getcwd()]))\n")
        prompt = self.root / "prompt.txt"
        value = 'line one\n$(touch SHOULD_NOT_EXIST) `echo nope` "quotes" ñ'
        prompt.write_text(value, encoding="utf-8")
        for platform in ("linux", "macos"):
            with self.subTest(platform=platform), patch.object(host, "platform", return_value=platform):
                script = host.write_script(self.root / "run", self.root,
                                           [sys.executable, str(program), str(output)],
                                           {"BITACORA_ROOT": str(self.root)}, prompt)
                subprocess.run(["/bin/bash", str(script)], check=True, timeout=10)
                self.assertEqual(json.loads(output.read_text()), [value, str(self.root), str(self.root.resolve())])
                self.assertFalse((self.root / "SHOULD_NOT_EXIST").exists())

    def test_windows_script_quotes_paths_and_keeps_utf8_prompt(self):
        with patch.object(host, "platform", return_value="windows"):
            script = host.write_script(self.root / "run", self.root, ["codex", "--yolo"],
                                       {"BITACORA_ROOT": str(self.root)}, self.root / "prompt.txt")
        content = script.read_text(encoding="utf-8")
        self.assertTrue(script.read_bytes().startswith(b'\xef\xbb\xbf'))
        self.assertEqual(script.suffix, ".ps1")
        self.assertIn("space '' dólar", content)
        self.assertIn("-Encoding UTF8", content)
        self.assertIn("& 'codex' '--yolo' $prompt", content)

    def test_linux_terminal_uses_kitty_without_windows_flags(self):
        graphical = {k: v for k, v in os.environ.items() if k != "BITACORA_TERMINAL"} | {"DISPLAY": ":0"}
        with patch.object(host, "platform", return_value="linux"), patch.dict(os.environ, graphical, clear=True), \
                patch.object(host.shutil, "which", side_effect=lambda exe: '/bin/kitty' if exe == 'kitty' else None), \
                patch.object(host.subprocess, "Popen") as spawn:
            host.open_terminal(self.root, self.root / "run.sh", "a title")
        self.assertEqual(spawn.call_args.args[0],
                         ["kitty", "--title", "a title", "--hold", "/bin/bash", "-l", str(self.root / "run.sh")])
        self.assertTrue(spawn.call_args.kwargs["start_new_session"])
        self.assertNotIn("creationflags", spawn.call_args.kwargs)

    def test_linux_missing_terminal_has_actionable_error(self):
        with patch.object(host, "platform", return_value="linux"), patch.object(host.shutil, "which", return_value=None), \
                self.assertRaisesRegex(RuntimeError, "Run manually"):
            host.open_terminal(self.root, self.root / "run.sh", "title")

    def test_mac_terminal_passes_shell_command_as_applescript_argument(self):
        with patch.object(host, "platform", return_value="macos"), patch.object(host.subprocess, "run") as run:
            host.open_terminal(self.root, self.root / "run.sh", "title")
        cmd = run.call_args.args[0]
        self.assertEqual(cmd[0], "osascript")
        self.assertIn('tell application "Terminal"', cmd[2])
        self.assertNotIn(str(self.root), cmd[2])
        self.assertIn("/bin/bash -l", cmd[3])
        self.assertTrue(run.call_args.kwargs["check"])

    def test_windows_terminal_retains_powershell_launcher(self):
        with patch.object(host, "platform", return_value="windows"), \
                patch.object(host.shutil, "which", side_effect=lambda exe: 'powershell' if exe == 'powershell' else None), \
                patch.object(host.subprocess, "Popen") as spawn:
            host.open_terminal(self.root, self.root / "run.ps1", "title")
        self.assertEqual(spawn.call_args.args[0][:4], ["cmd", "/c", "start", "title"])
        self.assertIn("creationflags", spawn.call_args.kwargs)

    def test_native_notifications_keep_user_text_out_of_script_source(self):
        for platform in ("linux", "macos"):
            with self.subTest(platform=platform), patch.object(host, "platform", return_value=platform), \
                    patch.object(host.subprocess, "run") as run:
                host.local_notification('title "quoted"', 'message $value')
                cmd = run.call_args.args[0]
                self.assertEqual(cmd[-2:], ['title "quoted"', 'message $value'])
                self.assertEqual(cmd[0], "osascript" if platform == "macos" else "notify-send")

    def test_linux_autostart_uses_xdg_directory_and_quoted_exec(self):
        config = self.root / "config"
        with patch.object(host, "platform", return_value="linux"), patch.dict(os.environ, {"XDG_CONFIG_HOME": str(config)}), \
                patch.object(bt_autostart.shutil, "which", return_value=None):
            path = bt_autostart.install("demo", "REQ-001", self.root, self.root / "bitacora.py")
        self.assertEqual(path.parent, config / "autostart")
        content = path.read_text()
        self.assertIn('Exec="/bin/bash" "-l" ', content)
        self.assertIn('Terminal=false', content)
        self.assertIn('\\\\$', content)
        self.assertEqual(bt_autostart.desktop_arg("100%"), '"100%%"')

    def test_linux_systemd_entry_is_enabled_for_next_login_without_starting_it(self):
        with patch.object(host, "platform", return_value="linux"), \
                patch.dict(os.environ, {"XDG_CONFIG_HOME": str(self.root / "config")}), \
                patch.object(bt_autostart.shutil, "which", return_value="systemctl"), \
                patch.object(bt_autostart.subprocess, "run") as run:
            path = bt_autostart.install("demo", "REQ-001", self.root, self.root / "bitacora.py")
            self.assertEqual(path.suffix, ".service")
            self.assertIn("WantedBy=default.target", path.read_text())
            self.assertIn("$$", path.read_text())
            self.assertEqual(run.call_args.args[0], ["systemctl", "--user", "enable", path.name])
            bt_autostart.remove("demo", "REQ-001")
            self.assertFalse(path.exists())
            self.assertFalse(any("start" in call.args[0] or "stop" in call.args[0] for call in run.call_args_list))

    def test_mac_autostart_is_a_user_launchagent_with_log_paths(self):
        with patch.object(host, "platform", return_value="macos"), patch.object(Path, "home", return_value=self.root):
            path = bt_autostart.install("demo", "REQ-001", self.root, self.root / "bitacora.py")
        data = plistlib.loads(path.read_bytes())
        self.assertEqual(path.parent, self.root / "Library/LaunchAgents")
        self.assertTrue(data["RunAtLoad"])
        self.assertEqual(data["ProgramArguments"][:2], ["/bin/bash", "-l"])
        script = Path(data["ProgramArguments"][2]).read_text()
        self.assertIn("--resume", script)
        self.assertIn("export PATH=", script)

    def test_git_background_push_uses_posix_session_and_reports_launch_errors(self):
        with patch.object(host, "platform", return_value="linux"), \
                patch.object(bt_vcs, "has_remote", return_value=True), patch.object(bt_vcs.subprocess, "Popen") as spawn:
            bt_vcs.push_async(self.root)
        self.assertTrue(spawn.call_args.kwargs["start_new_session"])
        with patch.object(bt_vcs, "has_remote", return_value=True), \
                patch.object(bt_vcs.subprocess, "Popen", side_effect=OSError("cannot spawn")), \
                patch.object(bt_vcs, "print", create=True) as output:
            bt_vcs.push_async(self.root)
        self.assertIn("could not start", output.call_args.args[0])

    def test_web_server_background_process_uses_a_posix_session(self):
        with patch.object(host, "platform", return_value="linux"), \
                patch.object(bt_server, "is_running", return_value=False), \
                patch.object(bt_server.subprocess, "Popen") as spawn:
            bt_server.ensure_server(18765)
        self.assertTrue(spawn.call_args.kwargs["start_new_session"])
        self.assertNotIn("creationflags", spawn.call_args.kwargs)

    def test_web_server_with_its_systemd_unit_is_restarted_there_not_spawned_loose(self):
        with patch.object(bt_server, "_unit_enabled", return_value=True), \
                patch.object(bt_server, "_server_stale", return_value=True), \
                patch.object(bt_server, "is_running", return_value=False), \
                patch.object(bt_server.subprocess, "run") as run, patch.object(bt_server.subprocess, "Popen") as spawn:
            bt_server.ensure_server(bt_server.DEFAULT_PORT)
        run.assert_called_once()
        self.assertEqual(run.call_args.args[0], ["systemctl", "--user", "restart", bt_server.WEB_UNIT])
        spawn.assert_not_called()
        with patch.object(bt_server, "_unit_enabled", return_value=True), \
                patch.object(bt_server, "is_running", return_value=True), patch.object(bt_server, "_server_stale", return_value=False), \
                patch.object(bt_server.subprocess, "run") as run:
            bt_server.ensure_server(bt_server.DEFAULT_PORT)
        run.assert_not_called()                                              # current code: leave the unit alone

    def test_socket_activation_unit_is_recognized_as_the_panel_owner(self):
        results = [
            subprocess.CompletedProcess([], 1, stdout="disabled\n", stderr=""),
            subprocess.CompletedProcess([], 0, stdout="enabled-runtime\n", stderr=""),
        ]
        with patch.object(bt_server, "platform", return_value="linux"), \
                patch.object(bt_server.shutil, "which", return_value="systemctl"), \
                patch.object(bt_server.subprocess, "run", side_effect=results) as run:
            self.assertTrue(bt_server._unit_enabled())
        self.assertEqual(run.call_args_list[0].args[0][-1], bt_server.WEB_UNIT)
        self.assertEqual(run.call_args_list[1].args[0][-1], bt_server.WEB_SOCKET_UNIT)

    def test_systemd_status_failure_never_falls_back_to_a_loose_server(self):
        with patch.object(bt_server, "platform", return_value="linux"), \
                patch.object(bt_server.shutil, "which", return_value="systemctl"), \
                patch.object(bt_server.subprocess, "run", side_effect=FileNotFoundError("systemctl unavailable")), \
                patch.object(bt_server, "is_running", return_value=False), \
                patch.object(bt_server.subprocess, "Popen") as spawn:
            with self.assertRaises(FileNotFoundError):
                bt_server.ensure_server(bt_server.DEFAULT_PORT)
        spawn.assert_not_called()

    def test_missing_systemctl_preserves_the_loose_startup_path(self):
        with patch.object(bt_server, "platform", return_value="linux"), \
                patch.object(bt_server.shutil, "which", return_value=None), \
                patch.object(bt_server, "is_running", return_value=False), \
                patch.object(bt_server.subprocess, "Popen") as spawn:
            bt_server.ensure_server(bt_server.DEFAULT_PORT)
        spawn.assert_called_once()

    def test_web_server_reload_uses_the_inherited_listener(self):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.addCleanup(listener.close)
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        address = listener.getsockname()
        with patch.object(bt_server, "systemd_listener", return_value=listener):
            httpd = bt_server.create_http_server(address[1])
        self.addCleanup(httpd.server_close)
        self.assertEqual(httpd.socket.getsockname(), address)
        self.assertEqual(httpd.socket.fileno(), listener.fileno())

    def test_systemd_listener_requires_its_activation_environment(self):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.addCleanup(listener.close)
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        with patch.object(host.sys, "platform", "linux"), \
                patch.object(host.os, "getpid", return_value=123), \
                patch.dict(os.environ, {"LISTEN_PID": "123", "LISTEN_FDS": "1"}), \
                patch.object(host.socket, "fromfd", return_value=listener):
            self.assertIs(host.systemd_listener(listener.getsockname()[1]), listener)
        with patch.object(host.sys, "platform", "linux"), \
                patch.dict(os.environ, {"LISTEN_PID": "999", "LISTEN_FDS": "1"}):
            self.assertIsNone(host.systemd_listener(listener.getsockname()[1]))

    def test_stale_web_server_can_be_stopped_on_posix_without_taskkill(self):
        state = self.root / "state"
        state.mkdir()
        (state / "server.json").write_text(json.dumps({"pid": 12345, "port": 18765, "version": "old", "root": "old"}))
        with patch.object(bt_server, "STATE", state), patch.object(bt_server, "platform", return_value="linux"), \
                patch.object(bt_server, "is_running", return_value=False), patch.object(bt_server.os, "kill") as kill:
            self.assertTrue(bt_server._stale(18765))
        kill.assert_called_once_with(12345, bt_server.signal.SIGTERM)

    def test_invalid_stale_server_pid_never_reaches_the_signal_api(self):
        state = self.root / "state"
        state.mkdir()
        for pid in (-1, 0, 1, True, "12345", os.getpid()):
            (state / "server.json").write_text(json.dumps({"pid": pid, "port": 18765, "version": "old"}))
            with self.subTest(pid=pid), patch.object(bt_server, "STATE", state), patch.object(bt_server.os, "kill") as kill:
                self.assertFalse(bt_server._stale(18765))
                kill.assert_not_called()

    def test_secret_scan_timeout_never_counts_as_clean(self):
        with patch.object(bt_secrets, "find_gitleaks", return_value="gitleaks"), \
                patch.object(bt_secrets.subprocess, "run", side_effect=subprocess.TimeoutExpired("gitleaks", 60)):
            clean, report = bt_secrets.scan_staged(self.root)
        self.assertFalse(clean)
        self.assertIn("TimeoutExpired", report)

    @unittest.skipUnless(bt_secrets.find_gitleaks(), "gitleaks not installed")
    def test_secret_scan_skips_generated_mockups_but_still_catches_real_leaks(self):
        def git(*args):
            subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)
        git("init", "-q")
        (self.root / "design").mkdir()
        fake = 'aws_access_key_id = "AKIA' + 'ABCDEFGHIJKLMNOP"\n'  # split so this file is not itself a finding
        (self.root / "design" / "mock.html").write_text(fake)
        git("add", "-A")
        self.assertEqual(bt_secrets.scan_staged(self.root), (True, ""))  # generated artifact: not scanned
        (self.root / "notes.md").write_text(fake)
        git("add", "-A")
        clean, report = bt_secrets.scan_staged(self.root)
        self.assertFalse(clean)
        self.assertIn("notes.md", report)
        self.assertNotIn("ABCDEFGHIJKLMNOP", report)  # reports stay redacted
        (self.root / ".gitleaksignore").write_text("notes.md:aws-access-token:1\n")
        git("add", "-A")
        self.assertTrue(bt_secrets.scan_staged(self.root)[0])

    @unittest.skipIf(os.name == "nt", "POSIX process groups")
    def test_cancel_kills_descendant_processes(self):
        marker = self.root / "child-survived"
        child = "import time,pathlib;time.sleep(1);pathlib.Path(" + repr(str(marker)) + ").touch()"
        parent = "import subprocess,sys,time;subprocess.Popen([sys.executable,'-c'," + repr(child) + "]);print('ready',flush=True);time.sleep(60)"
        proc = subprocess.Popen([sys.executable, "-c", parent], start_new_session=True,
                                stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual(proc.stdout.readline().strip(), "ready")
            bt_runsession.kill_tree(proc)
            time.sleep(1.3)
            self.assertFalse(marker.exists())
        finally:
            if proc.poll() is None:
                bt_runsession.kill_tree(proc)
            proc.stdout.close()


@unittest.skipIf(os.name == "nt", "POSIX process groups")
class PosixRuntimeTests(unittest.TestCase):
    def test_kill_tree_ends_a_group_that_ignores_sigterm_and_its_children(self):
        proc = subprocess.Popen(["/bin/sh", "-c", "trap '' TERM; sleep 60 & wait"], start_new_session=True,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.3)
        with patch.object(bt_runsession, "KILL_GRACE_SEC", 0.2):
            bt_runsession.kill_tree(proc)
        self.assertIsNotNone(proc.poll())
        with self.assertRaises(ProcessLookupError):
            os.killpg(proc.pid, 0)

    def test_pid_alive_treats_foreign_process_as_alive(self):
        import bt_runutil
        with patch("bt_runutil.os.kill", side_effect=PermissionError):
            self.assertTrue(bt_runutil.pid_alive(1))
        with patch("bt_runutil.os.kill", side_effect=ProcessLookupError):
            self.assertFalse(bt_runutil.pid_alive(999999))

    def test_headless_launch_prefers_tmux_then_systemd_run(self):
        script = Path("/tmp/run.sh")
        with patch("bt_platform.shutil.which", side_effect=lambda n: f"/usr/bin/{n}"):
            cmd = host._headless_command(Path("/tmp"), script, "pictures REQ-014 (claude)")
        self.assertEqual(cmd[:5], ["tmux", "new-session", "-d", "-s", "pictures-REQ-014-claude"])
        with patch("bt_platform.shutil.which", side_effect=lambda n: "/usr/bin/systemd-run" if n == "systemd-run" else None):
            cmd = host._headless_command(Path("/tmp"), script, "p r")
        self.assertEqual(cmd[:2], ["systemd-run", "--user"])
        with patch("bt_platform.shutil.which", return_value=None), self.assertRaises(RuntimeError):
            host._headless_command(Path("/tmp"), script, "p r")

    def test_headless_is_detected_without_a_display(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertTrue(host._headless())
        with patch.dict(os.environ, {"WAYLAND_DISPLAY": "wayland-1"}, clear=True):
            self.assertFalse(host._headless())
        with patch.dict(os.environ, {"WAYLAND_DISPLAY": "wayland-1", "BITACORA_TERMINAL": "tmux"}, clear=True):
            self.assertTrue(host._headless())


if __name__ == "__main__":
    unittest.main()
