import unittest

import bt_mockup_bridge as bridge


class Inject(unittest.TestCase):
    def test_the_bridge_goes_before_the_closing_body_once_and_the_rest_is_untouched(self):
        html = "<!doctype html><html><body><select id=view></select><p>x</p></body></html>"
        out = bridge.inject(html)
        self.assertIn("__ppBridge", out)
        self.assertLess(out.index("<script>"), out.index("</body>"))
        self.assertTrue(out.startswith("<!doctype html><html><body><select id=view></select><p>x</p><script>"))
        self.assertEqual(bridge.inject(out), out)                                  # idempotent

    def test_a_mockup_without_a_body_tag_gets_it_at_the_end(self):
        self.assertTrue(bridge.inject("<div>hi</div>").endswith("</script>"))

    def test_the_script_speaks_the_protocol_the_page_expects(self):
        src = bridge.BRIDGE.read_text(encoding="utf-8")
        for expected in ("pp: 'mockup'", "d.pp !== 'set'", "ev.source !== parent", "'view'", "'state'", "'scene'", "'theme'"):
            self.assertIn(expected, src)
        nav = (bridge.BRIDGE.parent / "mockup-nav.js").read_text(encoding="utf-8")
        for expected in ("d.pp !== 'mockup'", "pp: 'set'", "contentWindow === win", "hideOwn: true", "thumb=1", "pp-vcard", "pp-mdrop", "preview=1", "requestFullscreen", "pp-fullpill"):
            self.assertIn(expected, nav)
        for expected in ("d.hideOwn", "thumb=1", "preview=1"):
            self.assertIn(expected, src)


if __name__ == "__main__":
    unittest.main()
