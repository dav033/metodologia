"""The supervisor records what the provider driver contract would call each session, without acting on it (D-015)."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bt_runsession  # noqa: E402
import bt_runsettle  # noqa: E402


def claude_result(is_error: bool = False) -> str:
    return "\n".join([json.dumps({"type": "system"}), json.dumps(
        {"type": "result", "is_error": is_error, "subtype": "error" if is_error else "success", "result": "done"})])


class ContractShadowTests(unittest.TestCase):
    def test_clean_turn_is_completed_with_terminal_event(self) -> None:
        shadow = bt_runsession._contract_shadow("claude", claude_result(), 0, False, False)
        self.assertEqual(shadow, {"v": 1, "status": "completed", "terminal": True})

    def test_cut_stream_nonzero_exit_and_timeout_are_not_completed(self) -> None:
        cut = bt_runsession._contract_shadow("claude", '{"type": "system"}\n{"type": "res', 0, False, False)
        self.assertEqual(cut["status"], "partial")
        self.assertEqual(bt_runsession._contract_shadow("claude", claude_result(), 3, False, False)["status"], "failed")
        self.assertEqual(bt_runsession._contract_shadow("claude", "x", None, True, False)["status"], "timeout")
        self.assertEqual(bt_runsession._contract_shadow("claude", "x", None, False, True)["status"], "cancelled")

    def test_unknown_agent_never_raises_and_session_fields_carry_the_record(self) -> None:
        self.assertIsNone(bt_runsession._contract_shadow("no-such-agent", "x", 0, False, False))
        info = {"rc": 0, "text": claude_result(), "model": "sonnet", "effort": "medium", "agent": "claude",
                "contract": {"v": 1, "status": "completed", "terminal": True}}
        self.assertEqual(bt_runsettle._session_fields(info)["contract"]["status"], "completed")

    def test_settle_diagnosis_names_a_not_clean_contract_and_stays_silent_otherwise(self) -> None:
        note = bt_runsettle._contract_note
        self.assertEqual(note({"contract": {"v": 1, "status": "partial", "terminal": False}}),
                         ", provider contract: partial, no end-of-turn event")
        self.assertEqual(note({"contract": {"v": 1, "status": "failed", "terminal": True}}),
                         ", provider contract: failed")
        self.assertEqual(note({"contract": {"v": 1, "status": "completed", "terminal": True}}), "")
        self.assertEqual(note({"contract": None}), "")
        self.assertEqual(note({}), "")


if __name__ == "__main__":
    unittest.main()
