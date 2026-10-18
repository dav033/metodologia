from textwrap import dedent as D

CASE = dict(id='I2', title='Stable cursor pagination through repository service CLI', difficulty=2,
 prompt='''Implement stable cursor pagination across app.repository, app.service and app.cli, using stdlib only. Only app/ may change; test_public.py is protected. You may add tests under app/.
Rows are dictionaries with unique nonempty string id and integer timestamp, plus arbitrary payload. Inputs have valid rows; duplicate IDs need no validation. Repository(rows) snapshots rows. Repository.page(limit=20,cursor=None) returns {"items": list_of_row_dicts, "next_cursor": str_or_None}, ordered ascending by (timestamp,id). Limit must be int (not bool), 1..100 inclusive, otherwise ValueError. A cursor means strictly AFTER its tuple, even if that row has been deleted. Return next_cursor only if more rows exist, encoding the last returned tuple. No empty trailing page is required. Neither construction nor reads may mutate supplied rows; modifying returned rows must not affect subsequent reads (payloads used are JSON values).
app.repository.encode_cursor(timestamp, id) returns unpadded URL-safe base64 of compact UTF-8 JSON [timestamp,id], separators=(',',':'), ensure_ascii=False. decode_cursor(cursor) returns (timestamp,id). Reject empty, malformed base64, malformed JSON, wrong tuple length/types (bool is not timestamp), and empty IDs with ValueError; cursor must be a string, with only URL-safe base64 alphabet and no '=' padding. None is accepted only by page, meaning first page. Tokens from encode_cursor must round-trip unicode IDs.
Preserve legacy Repository.list_items(limit=20) returning just the first page list; it uses identical validation/order. app.service.list_items(repo,limit=20,cursor=None) returns the page dict. app.cli.main(argv=None, *, repo=None) parses --limit (default 20) and --cursor, delegates through service, prints one JSON page to stdout and returns 0. Invalid integer syntax/limit/cursor/options must return 2, print a nonempty error to stderr, and print nothing to stdout; do not raise SystemExit. With no injected repo use Repository([]). Running python -m app.cli exits with main's return code. Keep pagination deterministic and avoid duplicates/missing rows during static traversal.''',
 starter={'app/__init__.py':'', 'app/repository.py':D('''\
 class Repository:
     def __init__(self, rows):
         self.rows = list(rows)
     def list_items(self, limit=20):
         return sorted(self.rows, key=lambda row: (row['timestamp'],row['id']))[:limit]
     def page(self, limit=20, cursor=None):
         return {'items': self.list_items(limit), 'next_cursor': None}
 def encode_cursor(timestamp, id):
     return str(timestamp) + ':' + id
 def decode_cursor(cursor):
     timestamp, id = cursor.split(':',1)
     return int(timestamp), id
 '''), 'app/service.py':D('''\
 def list_items(repo, limit=20, cursor=None):
     return repo.page(limit=limit)
 '''), 'app/cli.py':D('''\
 import json
 from app.repository import Repository
 from app.service import list_items
 def main(argv=None, *, repo=None):
     print(json.dumps(list_items(repo if repo is not None else Repository([]))))
     return 0
 if __name__ == '__main__':
     raise SystemExit(main())
 '''), 'test_public.py':D('''\
 import unittest
 from app.repository import Repository
 from app.service import list_items
 class Public(unittest.TestCase):
     def test_legacy(self):
         rows = [{'timestamp':2,'id':'b'},{'timestamp':1,'id':'a'}]
         self.assertEqual(Repository(rows).list_items(1), [rows[1]])
     def test_empty_page(self):
         self.assertEqual(list_items(Repository([])), {'items':[],'next_cursor':None})
 ''')},
 reference={'app/repository.py':D('''\
 import base64
 import copy
 import json
 import re
 def encode_cursor(timestamp, id):
     raw = json.dumps([timestamp,id], separators=(',',':'), ensure_ascii=False).encode('utf-8')
     return base64.urlsafe_b64encode(raw).decode('ascii').rstrip('=')
 def decode_cursor(cursor):
     try:
         if not isinstance(cursor,str) or not re.fullmatch(r'[A-Za-z0-9_-]+',cursor):
             raise ValueError('invalid cursor alphabet')
         value = json.loads(base64.b64decode(cursor + '=' * (-len(cursor)%4), altchars=b'-_', validate=True).decode('utf-8'))
         if not isinstance(value,list) or len(value)!=2 or type(value[0]) is not int or not isinstance(value[1],str) or not value[1]:
             raise ValueError('invalid cursor tuple')
         return tuple(value)
     except (ValueError,TypeError,UnicodeError) as exc:
         raise ValueError('invalid cursor') from exc
 class Repository:
     def __init__(self, rows):
         self.rows = sorted(copy.deepcopy(list(rows)), key=lambda r:(r['timestamp'],r['id']))
     def list_items(self, limit=20):
         return self.page(limit)['items']
     def page(self, limit=20, cursor=None):
         if type(limit) is not int or not 1 <= limit <= 100:
             raise ValueError('limit must be 1..100')
         after = None if cursor is None else decode_cursor(cursor)
         rows = [r for r in self.rows if after is None or (r['timestamp'],r['id']) > after]
         items = copy.deepcopy(rows[:limit])
         token = encode_cursor(items[-1]['timestamp'],items[-1]['id']) if len(rows)>limit else None
         return {'items':items,'next_cursor':token}
 '''), 'app/service.py':D('''\
 def list_items(repo, limit=20, cursor=None):
     return repo.page(limit=limit, cursor=cursor)
 '''), 'app/cli.py':D('''\
 import argparse
 import json
 import sys
 from app.repository import Repository
 from app.service import list_items
 class Parser(argparse.ArgumentParser):
     def error(self, message):
         raise ValueError(message)
 def main(argv=None, *, repo=None):
     parser = Parser(add_help=False)
     parser.add_argument('--limit',type=int,default=20)
     parser.add_argument('--cursor')
     try:
         args = parser.parse_args(argv)
         result = list_items(repo if repo is not None else Repository([]), args.limit, args.cursor)
     except ValueError as exc:
         print(str(exc),file=sys.stderr)
         return 2
     print(json.dumps(result))
     return 0
 if __name__ == '__main__':
     raise SystemExit(main())
 ''')},
 private_tests={'test_private.py':D('''\
 import base64
 import contextlib
 import io
 import json
 import subprocess
 import sys
 import unittest
 from app.repository import Repository, encode_cursor, decode_cursor
 from app.service import list_items
 from app.cli import main
 def row(t,i): return {'timestamp':t,'id':i,'payload':{'v':[1]}}
 class Private(unittest.TestCase):
     def setUp(self):
         self.rows=[row(2,'z'),row(1,'c'),row(1,'a'),row(1,'b'),row(3,'x')]
         self.repo=Repository(self.rows)
     def test_static_traversal(self):
         cursor=None; ids=[]
         for _ in range(10):
             page=self.repo.page(2,cursor); ids.extend(r['id'] for r in page['items'])
             cursor=page['next_cursor']
             if cursor is None: break
         self.assertEqual(ids,['a','b','c','z','x'])
         self.assertIsNone(cursor)
     def test_cursor_encoding(self):
         token=encode_cursor(-5,'ñ')
         expected=base64.urlsafe_b64encode('[-5,"ñ"]'.encode()).decode().rstrip('=')
         self.assertEqual(token,expected)
         self.assertEqual(decode_cursor(token),(-5,'ñ'))
     def test_deleted_cursor(self):
         self.assertEqual([r['id'] for r in self.repo.page(10,encode_cursor(1,'bb'))['items']],['c','z','x'])
     def test_terminal(self):
         self.assertIsNone(self.repo.page(5)['next_cursor'])
         self.assertEqual(self.repo.page(2,encode_cursor(9,'z')),{'items':[],'next_cursor':None})
     def test_limits(self):
         for bad in [0,-1,101,True,1.5,'2',None]:
             with self.subTest(bad=bad):
                 with self.assertRaises(ValueError): self.repo.page(bad)
                 with self.assertRaises(ValueError): self.repo.list_items(bad)
         self.assertEqual(len(self.repo.page(100)['items']),5)
     def test_malformed_cursor(self):
         invalid=['','!','a','abc=','%%%%',None,12]
         for value in ['{}','[true,"a"]','[1,""]','[1,2]','[1,"a",3]','[1.2,"a"]','null']:
             invalid.append(base64.urlsafe_b64encode(value.encode()).decode().rstrip('='))
         for token in invalid:
             with self.subTest(token=token):
                 with self.assertRaises(ValueError): decode_cursor(token)
     def test_snapshot_and_return_isolation(self):
         self.rows[0]['payload']['v'].append(2)
         page=self.repo.page(5); page['items'][0]['payload']['v'].append(3)
         self.assertTrue(all(r['payload']['v']==[1] for r in self.repo.page(5)['items']))
     def test_service_forwards_cursor(self):
         page=list_items(self.repo,1,encode_cursor(1,'a'))
         self.assertEqual([r['id'] for r in page['items']],['b'])
         self.assertEqual(decode_cursor(page['next_cursor']),(1,'b'))
     def test_cli_success(self):
         out=io.StringIO(); err=io.StringIO()
         with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
             status=main(['--limit','1','--cursor',encode_cursor(1,'b')],repo=self.repo)
         self.assertEqual(status,0); self.assertEqual(err.getvalue(),'')
         self.assertEqual([r['id'] for r in json.loads(out.getvalue())['items']],['c'])
     def test_cli_errors(self):
         for argv in [['--limit','0'],['--limit','abc'],['--cursor','!'],['--unknown'],['--cursor']]:
             out=io.StringIO(); err=io.StringIO()
             with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
                 status=main(argv,repo=self.repo)
             self.assertEqual(status,2); self.assertEqual(out.getvalue(),''); self.assertTrue(err.getvalue())
     def test_module_entrypoint(self):
         good=subprocess.run([sys.executable,'-m','app.cli','--limit','2'],capture_output=True,text=True,timeout=5)
         self.assertEqual(good.returncode,0); self.assertEqual(json.loads(good.stdout),{'items':[],'next_cursor':None})
         bad=subprocess.run([sys.executable,'-m','app.cli','--limit','0'],capture_output=True,text=True,timeout=5)
         self.assertEqual(bad.returncode,2); self.assertEqual(bad.stdout,''); self.assertTrue(bad.stderr)
     def test_legacy_default(self):
         repo=Repository([row(0,str(i).zfill(3)) for i in range(25)])
         self.assertEqual(len(repo.list_items()),20)
         self.assertEqual(repo.list_items(3),repo.page(3)['items'])
 ''')})
