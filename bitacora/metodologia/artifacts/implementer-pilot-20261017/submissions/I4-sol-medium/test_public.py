import tempfile,os,unittest
from app.store import migrate,read_items
class PublicTests(unittest.TestCase):
    def test_new_db(self):
        with tempfile.TemporaryDirectory() as d:
            p=os.path.join(d,'db');migrate(p);self.assertEqual(read_items(p),[])
