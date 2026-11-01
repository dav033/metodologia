"""The integration repins the remote API's release copy itself (D-274).

Until D-274 every integration left `bitacora-remote-api.service` on an old pinned copy
(`~/.local/share/bitacora-remote/<sha>`, drop-in `exec.conf`) and the operator refreshed it by hand (2026-10-31:
aaf31a8d6 -> 7e8d4e638). Real git repositories and real folders in a temporary directory; systemctl (daemon-reload,
restart, smoke) is the recording fake of test_integrate.
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bt_integrate as integ
import bt_integrate_post as post
import bt_remote_pin as remote_pin
import test_integrate as base
from test_integrate import commit, sh

UNIT = remote_pin.UNIT


class Fake(base.Fake):
    def __init__(self, case, *, reload_fails: bool = False, **extra):
        super().__init__(case, **extra)
        self.reload_fails = reload_fails

    def daemon_reload(self):
        self.calls.append(("daemon_reload",))
        if self.reload_fails:
            raise remote_pin.PinError("systemctl daemon-reload failed: bus gone")


def dropin_text(releases: Path, sha: str) -> str:
    return ("# Local override: run the pinned release copy of the remote API (hand refresh).\n[Service]\nExecStart=\n"
            f"ExecStart=/usr/bin/python3 {releases}/{sha}/skill/scripts/bitacora.py serve-remote\n")


def fake_copy(releases: Path, sha: str, age: float = 0.0) -> Path:
    entry = releases / sha / remote_pin.ENTRY
    entry.parent.mkdir(parents=True, exist_ok=True)
    entry.write_text("# old release\n", encoding="utf-8")
    if age:
        stamp = time.time() - age
        os.utime(releases / sha, (stamp, stamp))
    return releases / sha


class RemotePin(unittest.TestCase):
    request, run_it, live_bitacora_intact = base.Integrate.request, base.Integrate.run_it, \
        base.Integrate.live_bitacora_intact

    def setUp(self):
        base.Integrate.setUp(self)
        commit(self.live, "skill/scripts/bitacora.py", "print('cli')\n", "the CLI the listener runs")
        commit(self.live, "skill/references/notes.md", "# notes\n", "docs")
        self.pinned = sh(self.live, "rev-parse", "HEAD")          # the listener runs main as it is now
        sh(self.wt, "merge", "-q", "--no-edit", "main")
        self.tip = sh(self.wt, "rev-parse", "HEAD")
        self.releases = self.base / "releases"
        fake_copy(self.releases, self.pinned)
        self.dropin = self.base / "unit.d" / "exec.conf"
        self.dropin.parent.mkdir(parents=True)
        self.original = dropin_text(self.releases, self.pinned)
        self.dropin.write_text(self.original, encoding="utf-8")
        self.pin = remote_pin.Pin(releases=self.releases, dropin=self.dropin, keep=3, home=self.base)

    def integrate(self, fake, **extra) -> integ.Outcome:
        return self.run_it(fake, remote=self.pin, **extra)

    def branch_changes(self, path: str, text: str = "changed\n") -> None:
        sh(self.wt, "reset", "-q", "--hard", "main")
        commit(self.wt, path, text, f"change {path}")

    # ---------------------------------------------------------------------------------------- which changes
    def test_the_paths_the_listener_runs(self):
        for path in ("skill/scripts/bt_remote_api.py", "skill/scripts/bt_durable/deploy/x.sh", "skill/assets/live.js",
                     "skill/templates/SPEC.md", "skill/vendor/archify/a.js", "skill/agents/solver.md"):
            self.assertTrue(remote_pin.relevant(path), path)
        for path in ("skill/scripts/tests/test_x.py", "skill/references/modules.md", "skill/SKILL.md",
                     "skill/githooks/pre-commit", "pyproject.toml", "uv.lock", "bitacora/x.md", "README.md"):
            self.assertFalse(remote_pin.relevant(path), path)

    def test_a_change_the_listener_runs_repins_it_in_the_restart_phase(self):
        fake = Fake(self)
        outcome = self.integrate(fake)
        self.assertEqual(outcome.code, 0, outcome.lines)
        merge = outcome.merge
        self.assertEqual([c[0] for c in fake.calls],
                         ["regress", "backup", "push", "daemon_reload", "drain", "restart", "restart", "restart", "smoke"])
        self.assertEqual([c[1] for c in fake.calls if c[0] == "restart"], [integ.ENGINE_UNIT, integ.WEB_UNIT, UNIT])
        self.assertIn(UNIT, fake.calls[-1][1])                                  # smoked with the others
        self.assertEqual(remote_pin.current(self.pin), merge)
        copy = self.releases / merge
        self.assertEqual((copy / "skill/scripts/bt_x.py").read_text(), "x = 2\n")
        self.assertFalse((copy / "bitacora").exists())                          # `git archive <sha> skill` only
        self.assertEqual(list(self.releases.glob(".tmp-*")), [])
        backup = self.dropin.with_name(f"exec.conf.bak-{self.pinned[:12]}")
        self.assertEqual(backup.read_text(), self.original)
        text = self.dropin.read_text()
        self.assertIn("[Service]\nExecStart=\nExecStart=/usr/bin/python3 ", text)
        self.assertIn("(D-274)", text.splitlines()[0])
        self.assertTrue((self.releases / self.pinned).is_dir())                 # the previous copy stays
        log = self.log.read_text()
        self.assertIn(f"remote API pin: {self.pinned[:12]} -> {merge[:12]}", log)
        self.assertIn("local restart of engine + web + remote API", log)
        self.assertTrue(any("repinned" in line for line in outcome.lines))
        self.live_bitacora_intact()

    def test_an_unrelated_change_leaves_the_listener_alone(self):
        for path, units in (("skill/references/modules.md", []), ("skill/scripts/tests/test_x.py", []),
                            ("pyproject.toml", [integ.ENGINE_UNIT, integ.WEB_UNIT])):
            with self.subTest(path=path):
                self.setUp()
                self.branch_changes(path, '[project]\nname = "x"\n' if path == "pyproject.toml" else "changed\n")
                fake = Fake(self)
                outcome = self.integrate(fake)
                self.assertEqual(outcome.code, 0, outcome.lines)
                self.assertNotIn("daemon_reload", [c[0] for c in fake.calls])
                self.assertEqual([c[1] for c in fake.calls if c[0] == "restart"], units)
                self.assertEqual(self.dropin.read_text(), self.original)
                self.assertEqual(sorted(p.name for p in self.releases.iterdir()), [self.pinned])

    def test_a_pin_already_behind_main_catches_up_on_the_next_integration(self):
        """The origin, not the symptom: the copy is compared with main, so an older pin (a refresh that failed, a hand
        pin) is repinned even when this branch changes only docs."""
        old = sh(self.live, "rev-parse", "HEAD~2")                              # before bitacora.py and the docs
        fake_copy(self.releases, old)
        self.dropin.write_text(dropin_text(self.releases, old), encoding="utf-8")
        self.branch_changes("skill/references/modules.md")
        fake = Fake(self)
        outcome = self.integrate(fake)
        self.assertEqual(outcome.code, 0, outcome.lines)
        self.assertIn(("restart", UNIT), fake.calls)
        self.assertEqual(remote_pin.current(self.pin), outcome.merge)

    def test_a_dry_run_says_it_and_changes_nothing(self):
        fake = Fake(self)
        outcome = self.integrate(fake, dry_run=True)
        self.assertEqual(outcome.code, 0, outcome.lines)
        self.assertTrue(any(f"pinned to {self.pinned[:12]}, repinned to the merge" in line for line in outcome.lines))
        self.assertTrue(any(UNIT in line for line in outcome.lines if line.startswith("preflight ok")))
        self.assertEqual(fake.calls, [])
        self.assertEqual(self.dropin.read_text(), self.original)
        self.assertEqual(sorted(p.name for p in self.releases.iterdir()), [self.pinned])

    def test_without_a_pin_owner_the_listener_is_never_touched(self):
        fake = Fake(self)
        self.assertEqual(self.run_it(fake).code, 0)                             # remote=None: tests, other callers
        self.assertNotIn("daemon_reload", [c[0] for c in fake.calls])
        self.assertNotIn(("restart", UNIT), fake.calls)
        self.assertEqual(self.dropin.read_text(), self.original)

    # ---------------------------------------------------------------------------------------- failures
    def test_a_failed_smoke_puts_the_previous_pin_back_and_reverts(self):
        fake = Fake(self, smoke=[["remote API answered 500"], []])
        outcome = self.integrate(fake)
        self.assertEqual(outcome.code, 3, outcome.lines)
        self.assertEqual(self.dropin.read_text(), self.original)                # the listener restarts on the old copy
        self.assertEqual(remote_pin.current(self.pin), self.pinned)
        kinds = [c[0] for c in fake.calls]
        self.assertEqual(kinds.count("daemon_reload"), 2)                       # repin, then rollback
        rollback = kinds.index("daemon_reload", kinds.index("smoke"))         # after the failed smoke ...
        self.assertLess(rollback, len(kinds) - 1 - kinds[::-1].index("restart"))   # ... before the revert's restart
        self.assertEqual([c for c in fake.calls if c == ("restart", UNIT)], [("restart", UNIT)] * 2)
        self.assertEqual(sh(self.live, "show", "HEAD:skill/scripts/bt_x.py"), "x = 1")
        self.assertTrue((self.releases / self.pinned / remote_pin.ENTRY).is_file())
        self.assertIn(f"remote API pin: back on {self.pinned[:12]}", self.log.read_text())

    def test_a_pin_that_cannot_be_made_keeps_the_old_one_and_the_integration_goes_on(self):
        fake = Fake(self, reload_fails=True)
        outcome = self.integrate(fake)
        self.assertEqual(outcome.code, 0, outcome.lines)
        self.assertEqual(self.dropin.read_text(), self.original)
        self.assertNotIn(("restart", UNIT), fake.calls)
        self.assertNotIn(UNIT, fake.calls[-1][1])
        self.assertTrue(any(line.startswith("WARNING remote API not repinned") for line in outcome.lines))
        self.assertIn("remote API pin: NOT refreshed", self.log.read_text())

    def test_a_proposed_revert_repins_to_the_revert(self):
        merged = self.integrate(Fake(self), keep_worktree=True)
        self.assertEqual(remote_pin.current(self.pin), merged.merge)
        fake = Fake(self)
        self.assertEqual(post.revert(self.request(remote=self.pin), merged.merge, fake, say=lambda text: None), 0)
        reverted = sh(self.live, "rev-parse", "HEAD")
        self.assertEqual(remote_pin.current(self.pin), reverted)
        self.assertEqual((self.releases / reverted / "skill/scripts/bt_x.py").read_text(), "x = 1\n")
        self.assertIn(("restart", UNIT), fake.calls)

    # ---------------------------------------------------------------------------------------- pruning
    def test_a_passing_smoke_prunes_old_copies_but_keeps_the_current_and_the_previous(self):
        shas = [sh(self.live, "rev-parse", f"HEAD~{n}") for n in (1, 2, 3)]    # older releases, oldest last
        for age, sha in enumerate(shas, start=1):
            fake_copy(self.releases, sha, age=3600.0 * age)
        os.utime(self.releases / self.pinned, (time.time() - 86400, time.time() - 86400))   # previous pin: the oldest
        outcome = self.integrate(Fake(self))
        self.assertEqual(outcome.code, 0, outcome.lines)
        left = sorted(p.name for p in self.releases.iterdir())
        self.assertEqual(left, sorted([outcome.merge, self.pinned, shas[0]]))   # keep=3: current, previous, newest
        self.assertTrue(any("remote API copies: removed" in line for line in outcome.lines))


class Prune(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix="bt-remote-pin-"))
        self.repo = self.base / "repo"
        self.repo.mkdir()
        sh(self.repo, "init", "-q", "-b", "main")
        sh(self.repo, "config", "user.name", "Test")
        sh(self.repo, "config", "user.email", "test@example.invalid")
        self.shas = [commit(self.repo, remote_pin.ENTRY, f"v = {n}\n", f"v{n}") for n in range(6)]
        self.releases = self.base / "releases"
        self.dropin = self.base / "unit.d" / "exec.conf"
        self.dropin.parent.mkdir(parents=True)
        self.pin = remote_pin.Pin(releases=self.releases, dropin=self.dropin, keep=3, home=self.base)

    def test_old_copies_go_regenerable_and_unused_only(self):
        for age, sha in enumerate(reversed(self.shas)):                       # shas[5] newest ... shas[0] oldest
            fake_copy(self.releases, sha, age=60.0 * (age + 1))
        unknown = "f" * 40
        fake_copy(self.releases, unknown, age=99999)                           # not in the repo: cannot be made again
        (self.releases / "operator-notes").mkdir()                             # not a release folder
        self.dropin.write_text(dropin_text(self.releases, self.shas[5]), encoding="utf-8")
        for sha in (self.shas[0], self.shas[1]):
            self.dropin.with_name(f"exec.conf.bak-{sha[:12]}").write_text("old\n")
        self.dropin.with_name(f"exec.conf.bak-{self.shas[1][:7]}").write_text("operator's\n")
        busy = self.releases / self.shas[2]
        removed, kept = remote_pin.prune(self.pin, self.repo, {self.shas[5], self.shas[0]},
                                         in_use=lambda folder: folder == busy)
        self.assertEqual(sorted(removed), sorted([self.shas[1], self.shas[3]]))
        left = {p.name for p in self.releases.iterdir()}
        self.assertEqual(left, {self.shas[5], self.shas[4], self.shas[0], self.shas[2], unknown, "operator-notes"})
        self.assertTrue(any("not in" in reason for reason in kept))
        self.assertTrue(any("a process runs from it" in reason for reason in kept))
        self.assertTrue(self.dropin.with_name(f"exec.conf.bak-{self.shas[0][:12]}").exists())    # its copy stays
        self.assertFalse(self.dropin.with_name(f"exec.conf.bak-{self.shas[1][:12]}").exists())   # its copy went
        self.assertTrue(self.dropin.with_name(f"exec.conf.bak-{self.shas[1][:7]}").exists())     # never ours

    def test_keep_never_drops_below_the_current_and_the_previous(self):
        for age, sha in enumerate(self.shas):
            fake_copy(self.releases, sha, age=60.0 * (age + 1))
        self.dropin.write_text(dropin_text(self.releases, self.shas[5]), encoding="utf-8")
        self.pin.keep = 1
        remote_pin.prune(self.pin, self.repo, {self.shas[5], self.shas[3]}, in_use=lambda folder: False)
        self.assertEqual({p.name for p in self.releases.iterdir()}, {self.shas[5], self.shas[3]})

    def test_a_copy_is_made_once_and_never_overwritten(self):
        made = remote_pin.materialize(self.pin, self.repo, self.shas[2])
        self.assertEqual((made / remote_pin.ENTRY).read_text(), "v = 2\n")
        (made / remote_pin.ENTRY).write_text("kept\n")
        self.assertEqual(remote_pin.materialize(self.pin, self.repo, self.shas[2]), made)
        self.assertEqual((made / remote_pin.ENTRY).read_text(), "kept\n")       # reused, not re-extracted
        broken = self.releases / self.shas[3]
        broken.mkdir()
        with self.assertRaises(remote_pin.PinError):
            remote_pin.materialize(self.pin, self.repo, self.shas[3])
        self.assertEqual(list(broken.iterdir()), [])
        with self.assertRaises(remote_pin.PinError):
            remote_pin.materialize(self.pin, self.repo, "e" * 40)              # git archive fails: nothing left
        self.assertEqual(list(self.releases.glob(".tmp-*")), [])
        self.assertFalse((self.releases / ("e" * 40)).exists())

    def test_a_drop_in_pinning_outside_the_releases_folder_is_refused(self):
        other = self.base / "elsewhere"
        self.dropin.write_text(dropin_text(other, self.shas[0]), encoding="utf-8")
        with self.assertRaises(remote_pin.PinError):
            remote_pin.refresh(self.pin, self.repo, self.shas[1], reload=lambda: None)
        self.assertEqual(remote_pin.current(self.pin), self.shas[0])

    def test_percent_h_is_the_home_folder(self):
        self.pin.releases = self.base / ".local" / "share" / "bitacora-remote"
        text = ("[Service]\nExecStart=\nExecStart=/usr/bin/python3 %h/.local/share/bitacora-remote/"
                f"{self.shas[0]}/skill/scripts/bitacora.py serve-remote\n")
        self.dropin.write_text(text, encoding="utf-8")
        swap = remote_pin.refresh(self.pin, self.repo, self.shas[1], reload=lambda: None)
        self.assertEqual(swap.previous, self.shas[0])
        self.assertIn(f"%h/.local/share/bitacora-remote/{self.shas[1]}/skill/scripts/bitacora.py serve-remote",
                      self.dropin.read_text())


class Cli(unittest.TestCase):
    def built(self, argv, unit_file: Path):
        with mock.patch.object(integ, "integrate") as integrate, mock.patch.object(remote_pin, "UNIT_FILE", unit_file):
            integrate.return_value = integ.Outcome(0, [])
            self.assertEqual(integ.main([*argv, "--attached"]), 0)
        return integrate.call_args.args[0]

    def test_only_an_integration_into_the_live_checkout_owns_the_pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            unit = Path(tmp) / UNIT
            unit.write_text("[Service]\n")
            argv = ["--branch", "x", "--title", "t", "--worktree", tmp]
            self.assertIsNotNone(self.built(argv, unit).remote)
            self.assertIsNone(self.built([*argv, "--live", tmp], unit).remote)
            self.assertIsNone(self.built(argv, Path(tmp) / "missing.service").remote)


if __name__ == "__main__":
    unittest.main()
