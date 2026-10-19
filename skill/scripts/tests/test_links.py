import io
import unittest

import bt_links as links


class Tty(io.StringIO):
    def isatty(self):
        return True


class Linkify(unittest.TestCase):
    ENV = {"TERM": "xterm-kitty"}

    def test_ids_become_osc8_links_only_on_a_tty(self):
        out = links.linkify("see REQ-005 and P-013.", "metodologia", stream=Tty(), env=self.ENV)
        self.assertIn("\x1b]8;;http://127.0.0.1:8765/go/metodologia/REQ-005\x07REQ-005\x1b]8;;\x07", out)
        self.assertIn("/go/metodologia/P-013", out)
        plain = "see REQ-005"
        self.assertEqual(links.linkify(plain, "p", stream=io.StringIO(), env=self.ENV), plain)   # redirected: untouched
        self.assertEqual(links.linkify(plain, "p", stream=Tty(), env={"TERM": "dumb"}), plain)

    def test_flag_overrides_and_port_is_configurable(self):
        env = {"BITACORA_LINKS": "1", "TERM": "dumb", "BITACORA_PORT": "9000"}
        self.assertIn("127.0.0.1:9000/go/D-045", links.linkify("D-045", None, stream=io.StringIO(), env=env))
        self.assertEqual(links.linkify("D-045", None, stream=Tty(), env={"BITACORA_LINKS": "0", "TERM": "xterm"}), "D-045")

    def test_does_not_touch_longer_tokens_or_paths(self):
        for text in ("PREQ-005", "REQ-005x", "docs/REQ-005-x/PLAN.md", "#P-013", "REQ-12", "TASK-009"):
            self.assertEqual(links.linkify(text, "p", stream=Tty(), env=self.ENV), text)

    def test_already_linked_text_is_not_wrapped_twice_in_a_markdown_link(self):
        text = "[REQ-005](http://x/go/REQ-005)"
        out = links.linkify(text, "p", stream=Tty(), env=self.ENV)
        self.assertEqual(out.count("\x1b]8;;"), 2)       # one link (open+close) for the bare id inside the brackets


if __name__ == "__main__":
    unittest.main()
