"""The executor shim writes bounded M3 wire frames without importing the monitor adapter."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

SHIM = Path(__file__).resolve().parents[1] / "shim.py"
spec = importlib.util.spec_from_file_location("scheduler_shim", SHIM)
shim = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(shim)


class StreamWireTests(unittest.TestCase):
    def test_frame_codec_keeps_stream_sequence_offset_and_data(self):
        encoded = shim.encode_stream_frame("stderr", 9, 123, b"diagnostic")
        self.assertLessEqual(len(encoded), 4096)
        self.assertEqual(shim.decode_stream_frame(encoded), ("stderr", 9, 123, b"diagnostic"))

    def test_oversized_payload_is_rejected_before_wire_write(self):
        with self.assertRaises(ValueError):
            shim.encode_stream_frame("stdout", 0, 0, b"x" * 3841)

    def test_m3_coalesces_disjoint_ranges_with_explicit_true_bounds(self):
        state = {"dropped": 0, "ranges": [], "pending": None}
        for index in range(70):
            sequence = index * 2
            shim.StreamTap._drop(state, sequence, sequence * 10, 1)
        self.assertEqual(len(state["ranges"]), 64)
        gap = state["ranges"][-1]
        self.assertGreater(gap["last_sequence"] - gap["first_sequence"] + 1, gap["dropped_frames"])


if __name__ == "__main__":
    unittest.main()
