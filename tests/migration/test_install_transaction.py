from __future__ import annotations

import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skill" / "scripts"))

import bt_install_tx as tx  # noqa: E402


def tree(root: Path) -> dict[str, tuple[str, int, bytes | str | None]]:
    result = {}
    if not root.exists():
        return result
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            result[relative] = ("symlink", 0, os.readlink(path))
        elif path.is_dir():
            result[relative] = ("directory", stat.S_IMODE(path.stat().st_mode), None)
        else:
            result[relative] = ("file", stat.S_IMODE(path.stat().st_mode), path.read_bytes())
    return result


class InstallTransactionTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="install tx ñ ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def test_dry_run_creates_no_files_or_directories(self) -> None:
        target = self.root / "a space" / "配置.json"
        before = tree(self.root)
        transaction = tx.plan([tx.write_file(target, "hello")])
        report = tx.dry_run(transaction)
        self.assertEqual(report["operations"][0]["action"], "create")
        self.assertEqual(tree(self.root), before)

    def test_apply_twice_is_idempotent_and_keeps_bytes_identical(self) -> None:
        target = self.root / "folder" / "résultat.txt"
        transaction = tx.plan([tx.write_file(target, b"first\x00", 0o640)])
        backup = self.root / "backup"
        first = tx.apply(transaction, backup)
        content = target.read_bytes()
        second = tx.apply(transaction, backup)
        self.assertTrue(first["changed"])
        self.assertFalse(second["changed"])
        self.assertEqual(second["operations"][0]["action"], "unchanged")
        self.assertEqual(target.read_bytes(), content)
        self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o640)

    def test_json_merge_preserves_unknown_keys_and_unrelated_hooks(self) -> None:
        target = self.root / "settings.json"
        original = {"unknown": {"keep": True}, "hooks": {"Stop": [
            {"hooks": [{"command": "user-hook"}]},
            {"hooks": [{"command": "old metodologia hook"}]},
        ]}}
        target.write_text(json.dumps(original), encoding="utf-8")

        def merge(current: dict) -> dict:
            current.setdefault("hooks", {}).setdefault("Stop", []).append(
                {"hooks": [{"command": "metodologia hook"}]})
            return current

        operation = tx.json_merge(target, merge)
        transaction = tx.plan([operation])
        tx.apply(transaction, self.root / "backup")
        tx.apply(transaction, self.root / "backup")
        data = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(data["unknown"], {"keep": True})
        entries = data["hooks"]["Stop"]
        self.assertEqual(sum("metodologia" in json.dumps(item) for item in entries), 1)
        self.assertTrue(any("user-hook" in json.dumps(item) for item in entries))

    def test_failure_after_each_operation_rolls_back_exact_preimage_tree(self) -> None:
        for fail_after in range(1, 5):
            with self.subTest(fail_after=fail_after):
                case = self.root / f"case-{fail_after}"
                case.mkdir()
                old = case / "old.txt"
                old.write_bytes(b"before")
                os.chmod(old, 0o604)
                link = case / "link"
                link.symlink_to("old.txt")
                before = tree(case)
                transaction = tx.plan([
                    tx.write_file(old, "after", 0o600),
                    tx.symlink(link, "new-target"),
                    tx.ensure_block(case / "nested" / "notes.md", "managed", "metodologia"),
                    tx.write_file(case / "new.txt", b"created", 0o640),
                ])
                backup = self.root / f"backup-{fail_after}"
                with self.assertRaises(tx.InjectedFailure):
                    tx.apply(transaction, backup, fail_after=fail_after)
                report = tx.rollback(backup / "journal.jsonl")
                self.assertEqual(report["conflicts"], [])
                self.assertEqual(tree(case), before)

    def test_rollback_preserves_post_apply_edits_and_reports_conflict(self) -> None:
        target = self.root / "owned.txt"
        target.write_text("before", encoding="utf-8")
        backup = self.root / "backup"
        tx.apply(tx.plan([tx.write_file(target, "managed")]), backup)
        target.write_text("someone else's edit", encoding="utf-8")
        report = tx.rollback(backup / "journal.jsonl")
        self.assertEqual(report["conflicts"], [str(target)])
        self.assertEqual(target.read_text(encoding="utf-8"), "someone else's edit")

    def test_rollback_removes_new_file_only_when_unchanged(self) -> None:
        target = self.root / "new.txt"
        backup = self.root / "backup"
        tx.apply(tx.plan([tx.write_file(target, "managed")]), backup)
        tx.rollback(backup / "journal.jsonl")
        self.assertFalse(target.exists())
        backup2 = self.root / "backup2"
        tx.apply(tx.plan([tx.write_file(target, "managed")]), backup2)
        target.write_text("edited", encoding="utf-8")
        report = tx.rollback(backup2 / "journal.jsonl")
        self.assertEqual(report["conflicts"], [str(target)])
        self.assertEqual(target.read_text(encoding="utf-8"), "edited")

    def test_backup_is_private_and_paths_support_spaces_and_unicode(self) -> None:
        original = self.root / "área compartida" / "configuración.json"
        original.parent.mkdir()
        original.write_text("original", encoding="utf-8")
        backup = self.root / "respaldo privado"
        tx.apply(tx.plan([tx.write_file(original, "updated")]), backup)
        self.assertEqual(stat.S_IMODE(backup.stat().st_mode), 0o700)
        copies = list(backup.glob("preimage-*"))
        self.assertEqual(len(copies), 1)
        self.assertEqual(stat.S_IMODE(copies[0].stat().st_mode), 0o600)
        self.assertEqual(copies[0].read_text(encoding="utf-8"), "original")

    def test_json_merge_preserves_foreign_hook_that_mentions_project_path(self) -> None:
        target = self.root / "settings.json"
        foreign = {"command": "run ~/dev/metodologia/some-other-tool"}
        owned = {"command": "run ~/.codex/skills/metodologia/hook"}
        target.write_text(json.dumps({"hooks": {"Stop": [foreign, owned]}}), encoding="utf-8")
        operation = tx.json_merge(target, lambda current: current)
        tx.apply(tx.plan([operation]), self.root / "backup")
        entries = json.loads(target.read_text(encoding="utf-8"))["hooks"]["Stop"]
        self.assertIn(foreign, entries)
        self.assertNotIn(owned, entries)

    def test_rollback_recovers_replace_without_done_record(self) -> None:
        target = self.root / "target"
        target.write_text("before", encoding="utf-8")
        backup = self.root / "backup"
        original = tx._append
        def fail_done(path: Path, row: dict) -> None:
            if row.get("event") == "done":
                raise RuntimeError("crash before done")
            original(path, row)
        with patch.object(tx, "_append", side_effect=fail_done):
            with self.assertRaisesRegex(RuntimeError, "crash"):
                tx.apply(tx.plan([tx.write_file(target, "after")], allowed_roots=(self.root,)), backup)
        report = tx.rollback(backup / "journal.jsonl")
        self.assertEqual(report["restored"], [str(target)])
        self.assertEqual(target.read_text(encoding="utf-8"), "before")

    def test_rollback_rejects_tampered_backup_and_ignores_torn_tail(self) -> None:
        target = self.root / "target"
        target.write_text("before", encoding="utf-8")
        backup = self.root / "backup"
        tx.apply(tx.plan([tx.write_file(target, "after")], allowed_roots=(self.root,)), backup)
        copy = next(backup.glob("preimage-*"))
        copy.write_text("tampered", encoding="utf-8")
        journal = backup / "journal.jsonl"
        journal.write_text(journal.read_text(encoding="utf-8") + '{"event":', encoding="utf-8")
        report = tx.rollback(journal)
        self.assertEqual(report["conflicts"], [str(target)])
        self.assertIn("torn_trailing_line", report["warnings"])

    def test_plan_refuses_parent_symlink_escape(self) -> None:
        allowed = self.root / "allowed"
        allowed.mkdir()
        outside = self.root / "outside"
        outside.mkdir()
        link = allowed / "linked"
        link.symlink_to(outside, target_is_directory=True)
        transaction = tx.plan([tx.write_file(link / "target", "x")], allowed_roots=(allowed,))
        with self.assertRaisesRegex(tx.TransactionError, "symlink"):
            tx.apply(transaction, self.root / "backup")


if __name__ == "__main__":
    unittest.main()
