import os, sqlite3, tempfile, unittest
from app.store import migrate, read_items


def legacy(p, rows):
    c = sqlite3.connect(p)
    c.execute("CREATE TABLE items(id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
    c.executemany("INSERT INTO items VALUES(?,?)", rows)
    c.commit(); c.close()


class T(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory(); self.p = os.path.join(self.d.name, "db")
    def tearDown(self): self.d.cleanup()

    def test_legacy(self):
        legacy(self.p, [(5, " AbC "), (-2, "X")])
        migrate(self.p)
        self.assertEqual(read_items(self.p), [(-2, "x"), (5, "abc")])
        calls = []
        migrate(self.p, calls.append); self.assertEqual(calls, [])

    def test_faults(self):
        legacy(self.p, [(1, " A")])
        for pt in ("after_copy", "before_commit"):
            def f(n, pt=pt):
                if n == pt: raise RuntimeError(pt)
            with self.assertRaises(RuntimeError): migrate(self.p, f)
            c = sqlite3.connect(self.p)
            self.assertEqual(c.execute("PRAGMA user_version").fetchone()[0], 0)
            self.assertEqual([r[0] for r in c.execute("select name from sqlite_master")], ["items"])
            c.close()
        migrate(self.p)
        self.assertEqual(read_items(self.p), [(1, "a")])
        c = sqlite3.connect(self.p)
        self.assertEqual([r[0] for r in c.execute("select name from sqlite_master")], ["items"])

    def test_future(self):
        c = sqlite3.connect(self.p); c.execute("PRAGMA user_version=2"); c.close()
        with self.assertRaises(ValueError): migrate(self.p)
        c = sqlite3.connect(self.p)
        self.assertEqual(c.execute("select count(*) from sqlite_master").fetchone()[0], 0)

if __name__ == "__main__": unittest.main()
