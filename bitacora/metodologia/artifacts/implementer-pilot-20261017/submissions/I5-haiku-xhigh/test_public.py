import os,tempfile,unittest
from app.store import init,enqueue,claim
class PublicTests(unittest.TestCase):
    def test_basic(self):
        with tempfile.TemporaryDirectory() as d:
            p=os.path.join(d,'db');init(p);enqueue(p,'a','work');self.assertEqual(claim(p,0,10),('a','work',1))
