import os, tempfile, unittest
from app.store import *

class T(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory(); self.p = os.path.join(self.d.name, 'db'); init(self.p); init(self.p)
    def tearDown(self): self.d.cleanup()
    def test_flow(self):
        p = self.p
        enqueue(p, 'b', 'B', 'a'); enqueue(p, 'a', 'A'); enqueue(p, 'a', 'X')
        self.assertEqual(claim(p, 0, 5), ('a', 'A', 1))
        self.assertIsNone(claim(p, 1, 5))
        self.assertEqual(claim(p, 5, 5), ('a', 'A', 2))
        self.assertFalse(complete(p, 'a', 1, 'r', 6))
        def bad(w):
            if w == 'before_commit': raise RuntimeError
        with self.assertRaises(RuntimeError): complete(p, 'a', 2, 'r', 6, bad)
        self.assertEqual(inspect(p, 'a')['state'], 'running')
        self.assertTrue(complete(p, 'a', 2, 'r', 6))
        self.assertEqual(claim(p, 6, 5)[0], 'b')
        got = []
        self.assertEqual(publish(p, lambda i, b: (got.append((i, b)), consume(p, i, b))), 1)
        self.assertEqual(got, [('a', 'r')]); self.assertEqual(publish(p, lambda i, b: 1/0), 0)
        self.assertFalse(consume(p, 'a', 'z'))
    def test_retry_ttl(self):
        p = self.p; enqueue(p, 'a', 'A')
        with self.assertRaises(ValueError): claim(p, 0, 0)
        t = claim(p, 0, 5)[2]
        self.assertTrue(retry(p, 'a', t, 1)); self.assertFalse(retry(p, 'a', t, 1))
        self.assertEqual(claim(p, 1, 5)[2], 2)
