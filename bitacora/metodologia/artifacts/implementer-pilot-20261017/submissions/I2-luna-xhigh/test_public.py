import unittest
from app.repository import Repository
from app.service import list_items
class Public(unittest.TestCase):
    def test_legacy(self):
        rows = [{'timestamp':2,'id':'b'},{'timestamp':1,'id':'a'}]
        self.assertEqual(Repository(rows).list_items(1), [rows[1]])
    def test_empty_page(self):
        self.assertEqual(list_items(Repository([])), {'items':[],'next_cursor':None})
