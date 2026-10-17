from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from bt_scheduler_monitor.bench import _sampled_peak_rss_kib


class BenchmarkResourceTests(unittest.TestCase):
    def test_peak_rss_reads_linux_vm_hwm_in_kib(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            status = Path(directory) / "status"
            status.write_text("Name:\tpython\nVmRSS:\t9000 kB\nVmHWM:\t12345 kB\n", encoding="ascii")
            self.assertEqual(_sampled_peak_rss_kib(status), 12_345)


if __name__ == "__main__":
    unittest.main()
