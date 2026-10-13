"""Harder tasks to separate effort levels and find limits. Imported by bench.py (adds to TASKS) ."""
import ast, json, os, random, re, subprocess, sys, textwrap
from pathlib import Path


def _sh(cmd, cwd, timeout=60, env=None):
    try:
        r = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, timeout=timeout,
                           env={"PATH": os.environ["PATH"], "HOME": os.environ["HOME"], "PYTHONDONTWRITEBYTECODE": "1",
                                **(env or {})})
        return r.returncode, r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        return 124, "timeout"


def _py(code, cwd, timeout=90, env=None):
    p = Path(cwd) / "_verify.py"
    p.write_text(code)
    return _sh(f"{sys.executable} _verify.py", cwd, timeout, env)


def _frac(out):
    m = re.findall(r"RESULT (\d+) (\d+)", out)
    return (int(m[-1][0]) / int(m[-1][1])) if m else 0.0


# ------------------------------------------------------------------ H1 expression evaluator (oracle: Python itself)

def h_expr():
    prompt = ("Create calc.py with `evaluate(s)` that evaluates an arithmetic expression string and returns the number. "
              "Do NOT use eval, exec, ast.literal_eval, compile or the ast module. Supported: integer and decimal "
              "literals, binary + - * / // % **, parentheses, unary + and -, arbitrary whitespace. Semantics must be "
              "exactly Python's: precedence, `**` is right associative, `-2**2` is -4, `2**-1` is 0.5, `/` is true "
              "division, `//` and `%` follow Python for negative operands. Raise ValueError for malformed input "
              "(empty, unbalanced parentheses, dangling operator, two numbers in a row, unknown characters). Division "
              "or modulo by zero must raise ZeroDivisionError.")

    def verify(d):
        code = r'''
import importlib.util, random, sys
spec = importlib.util.spec_from_file_location("calc", "calc.py"); m = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(m)
except Exception as e:
    print("import error", e); print("RESULT 0 1"); sys.exit()
src = open("calc.py").read()
import re as _re
if any(w in src for w in ("eval(", "exec(", "literal_eval", "import ast", "from ast")) or _re.search(r"(?<![\w.])compile\(", src):
    print("forbidden construct"); print("RESULT 0 1"); sys.exit()
rnd = random.Random(7)
def num():
    return rnd.choice([str(rnd.randint(0, 12)), "%d.%d" % (rnd.randint(0, 9), rnd.randint(0, 9))])
def gen(depth=0):
    r = rnd.random()
    if depth > 3 or r < 0.25: return num()
    if r < 0.4: return "(" + gen(depth + 1) + ")"
    if r < 0.5: return rnd.choice(["-", "+"]) + gen(depth + 1)
    op = rnd.choice(["+", "-", "*", "/", "//", "%", "**", "+", "-", "*"])
    a, b = gen(depth + 1), gen(depth + 1)
    if op == "**": b = str(rnd.randint(0, 3)) if rnd.random() < .7 else "-" + str(rnd.randint(1, 2))
    return a + rnd.choice(["", " ", "  "]) + op + rnd.choice(["", " "]) + b
ok = total = 0
for _ in range(150):
    e = gen()
    try: want = ("v", eval(e))
    except ZeroDivisionError: want = ("z",)
    except Exception: continue
    if want[0] == "v" and isinstance(want[1], complex): continue
    total += 1
    try:
        got = ("v", m.evaluate(e))
    except ZeroDivisionError: got = ("z",)
    except Exception: got = ("x",)
    if want[0] == "v" and got[0] == "v" and abs(want[1] - got[1]) <= 1e-9 * max(1, abs(want[1])): ok += 1
    elif want[0] == "z" and got[0] == "z": ok += 1
bad = ["", "  ", "(1+2", "1+2)", "1+", "*3", "1 2", "1..2", "2 $ 3", "()", "1+*2", "--", "3 3 +"]
for e in bad:
    total += 1
    try: m.evaluate(e)
    except ValueError: ok += 1
    except Exception: pass
fixed = [("-2**2", -4), ("2**3**2", 512), ("2**-1", 0.5), ("-7//2", -4), ("-7%3", 2), ("7%-3", -2), ("1-(-(-1))", 0),
         ("--3", 3), ("+-+3", -3), (" ( 1 + 2 ) * 3 ", 9), ("10/4", 2.5), ("2*-3", -6), ("0.1+0.2", 0.30000000000000004)]
for e, w in fixed:
    total += 1
    try: ok += abs(m.evaluate(e) - w) < 1e-9
    except Exception: pass
print("RESULT", ok, total)
'''
        rc, out = _py(code, d)
        return _frac(out), out.strip().splitlines()[-1][:120] if out.strip() else ""
    return (lambda d: None), prompt, verify


# ------------------------------------------------------------------ H2 bugs described only in prose

CACHE_BUGGY = '''"""TTL + LRU cache. Spec: at most `max_size` live entries; an entry is live for exactly `ttl` seconds after it was
last written (at now == written + ttl it is already expired); reading an entry marks it most recently used; when full,
the least recently used live entry is evicted; len() counts live entries only."""
from collections import OrderedDict


class TTLCache:
    def __init__(self, max_size, ttl, clock):
        self.max_size, self.ttl, self.clock = max_size, ttl, clock
        self._d = OrderedDict()  # key -> (value, written_at)

    def _live(self, written):
        return self.clock() - written <= self.ttl

    def get(self, key, default=None):
        item = self._d.get(key)
        if item is None:
            return default
        value, written = item
        if not self._live(written):
            del self._d[key]
            return default
        return value

    def set(self, key, value):
        if key in self._d:
            self._d[key] = (value, self._d[key][1])
            return
        if len(self._d) >= self.max_size:
            self._d.popitem(last=False)
        self._d[key] = (value, self.clock())

    def delete(self, key):
        return self._d.pop(key, None) is not None

    def __len__(self):
        return len(self._d)
'''


def h_cache():
    prompt = ("cache.py implements a TTL + LRU cache; its contract is in the module docstring. Users filed this bug "
              "report: (1) 'keys we read all the time still disappear while keys nobody touches survive'; (2) 'an entry "
              "is still served at exactly ttl seconds after it was written'; (3) 'len(cache) reports more items than "
              "can actually be read'; (4) 'overwriting a key does not extend how long it lives'; (5) 'when the cache "
              "is full and an expired entry exists, a live entry is evicted instead of the expired one being dropped'. "
              "Find and fix the causes in cache.py. Keep the public API unchanged. There are no tests: you must decide "
              "from the contract what is correct.")

    def setup(d):
        (Path(d) / "cache.py").write_text(CACHE_BUGGY)

    def verify(d):
        code = r'''
import importlib.util
spec = importlib.util.spec_from_file_location("cache", "cache.py"); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
class Clk:
    def __init__(s): s.t = 0.0
    def __call__(s): return s.t
ok = total = 0
def check(name, fn):
    global ok, total
    total += 1
    try: ok += bool(fn())
    except Exception as e: pass
def mk(n=3, ttl=10):
    c = Clk(); return c, m.TTLCache(n, ttl, c)
def t1():
    c, k = mk(); k.set("a", 1); k.set("b", 2); k.set("c", 3); k.get("a"); k.set("d", 4)
    return k.get("b") is None and k.get("a") == 1
def t2():
    c, k = mk(ttl=10); k.set("a", 1); c.t = 10; return k.get("a") is None
def t3():
    c, k = mk(ttl=10); k.set("a", 1); c.t = 9.99; return k.get("a") == 1
def t4():
    c, k = mk(); k.set("a", 1); k.set("b", 2); c.t = 11; return len(k) == 0
def t5():
    c, k = mk(); k.set("a", 1); c.t = 6; k.set("a", 2); c.t = 12; return k.get("a") == 2
def t6():
    c, k = mk(n=2); k.set("a", 1); c.t = 1; k.set("b", 2); c.t = 10.5; k.set("c", 3)  # a expired at 10, b live until 11
    return k.get("b") == 2 and k.get("c") == 3 and len(k) == 2
def t7():
    c, k = mk(n=2); k.set("a", 1); k.set("b", 2); k.set("a", 9); k.set("c", 3)
    return k.get("b") is None and k.get("a") == 9
def t8():
    c, k = mk(); k.set("a", 1); return k.delete("a") is True and k.delete("a") is False and len(k) == 0
def t9():
    c, k = mk(n=1); k.set("a", 1); k.set("b", 2); return k.get("a") is None and k.get("b") == 2 and len(k) == 1
def t10():
    c, k = mk(ttl=5); k.set("a", 1); c.t = 3; k.get("a"); c.t = 6; return k.get("a") is None  # a read does not extend life
def t11():
    c, k = mk(n=3, ttl=10); k.set("a", 1); c.t = 5; k.set("b", 2); c.t = 10; return len(k) == 1 and k.get("b") == 2
def t12():
    c, k = mk(); return k.get("zz", "dflt") == "dflt" and len(k) == 0
for i, f in enumerate([t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12]): check(i, f)
print("RESULT", ok, total)
'''
        rc, out = _py(code, d)
        return _frac(out), out.strip().splitlines()[-1][:100] if out.strip() else ""
    return setup, prompt, verify


# ------------------------------------------------------------------ H4 multi-file feature

SHOP = {
    "clock.py": '''import time


class Clock:
    def now(self):
        return time.time()

    def sleep(self, seconds):
        time.sleep(seconds)
''',
    "transport.py": '''class TransportError(Exception):
    pass


class Transport:
    """Real implementation talks to the network; tests replace it."""

    def send(self, method, path, payload=None):
        raise TransportError("network disabled")
''',
    "config.py": '''# Settings shared by the whole shop client.
BASE_URL = "https://shop.example"
TIMEOUT = 5.0
''',
    "client.py": '''from clock import Clock
from transport import Transport

import config


class ShopClient:
    def __init__(self, transport=None, clock=None):
        self.transport = transport or Transport()
        self.clock = clock or Clock()

    def get_product(self, product_id):
        if not isinstance(product_id, int):
            raise ValueError("product_id must be an int")
        return self.transport.send("GET", f"/products/{product_id}")

    def get_price(self, product_id):
        return self.transport.send("GET", f"/products/{product_id}/price")

    def place_order(self, product_id, qty):
        if qty < 1:
            raise ValueError("qty must be >= 1")
        return self.transport.send("POST", "/orders", {"product": product_id, "qty": qty})
''',
    "orders.py": '''def checkout(client, product_id, qty):
    price = client.get_price(product_id)
    order = client.place_order(product_id, qty)
    return {"price": price, "order": order}
''',
    "test_client.py": '''import unittest
from client import ShopClient


class Fake:
    def __init__(self):
        self.calls = []

    def send(self, method, path, payload=None):
        self.calls.append((method, path))
        return {"ok": path}


class T(unittest.TestCase):
    def test_get_product(self):
        c = ShopClient(Fake())
        self.assertEqual(c.get_product(3), {"ok": "/products/3"})

    def test_bad_id(self):
        with self.assertRaises(ValueError):
            ShopClient(Fake()).get_product("x")


if __name__ == "__main__":
    unittest.main()
''',
}


def h_retry():
    prompt = ("This is a small shop client project. Add retry with exponential backoff to every network call made "
              "through `ShopClient` (get_product, get_price, place_order). Requirements: a call is attempted at most "
              "3 times in total; only `transport.TransportError` is retried, any other exception (ValueError etc.) "
              "propagates immediately without retry; between attempts wait using `self.clock.sleep(delay)` where the "
              "delays are 0.1 then 0.2 seconds (base 0.1, factor 2); after the last failed attempt the original "
              "TransportError is raised; the retry settings live in config.py as `RETRY = {'attempts': 3, 'base': "
              "0.1, 'factor': 2.0}` and the client must read them at call time (so tests can change config.RETRY); "
              "input validation errors must be raised before any attempt. Do not change the signatures of the public "
              "methods or of orders.checkout. Keep the existing tests passing and add tests for the retry behaviour "
              "to test_client.py.")

    def setup(d):
        for n, c in SHOP.items():
            (Path(d) / n).write_text(c)

    def verify(d):
        code = r'''
import sys, importlib
sys.path.insert(0, ".")
ok = total = 0
def check(fn):
    global ok, total
    total += 1
    try: ok += bool(fn())
    except Exception as e: print("ERR", type(e).__name__, e)
try:
    import config, client, orders, transport
except Exception as e:
    print("import error", e); print("RESULT 0 1"); sys.exit()
class Clk:
    def __init__(s): s.slept = []
    def now(s): return 0
    def sleep(s, x): s.slept.append(x)
class Flaky:
    def __init__(s, fails, exc=None): s.fails, s.n, s.exc = fails, 0, exc or transport.TransportError("boom")
    def send(s, method, path, payload=None):
        s.n += 1
        if s.n <= s.fails: raise s.exc
        return {"ok": path}
def c1():
    t, k = Flaky(2), Clk(); r = client.ShopClient(t, k).get_product(1)
    return r == {"ok": "/products/1"} and t.n == 3 and k.slept == [0.1, 0.2]
def c2():
    t, k = Flaky(5), Clk()
    try: client.ShopClient(t, k).get_price(1)
    except transport.TransportError: return t.n == 3 and k.slept == [0.1, 0.2]
    return False
def c3():
    t, k = Flaky(5, ValueError("bad")), Clk()
    try: client.ShopClient(t, k).place_order(1, 2)
    except ValueError: return t.n == 1 and k.slept == []
    return False
def c4():
    t, k = Flaky(0), Clk()
    try: client.ShopClient(t, k).get_product("x")
    except ValueError: return t.n == 0
    return False
def c5():
    t, k = Flaky(0), Clk()
    try: client.ShopClient(t, k).place_order(1, 0)
    except ValueError: return t.n == 0
    return False
def c6():
    old = dict(config.RETRY)
    try:
        config.RETRY.update(attempts=5, base=1.0, factor=3.0)
        t, k = Flaky(4), Clk(); client.ShopClient(t, k).get_product(2)
        return t.n == 5 and k.slept == [1.0, 3.0, 9.0, 27.0]
    finally:
        config.RETRY.clear(); config.RETRY.update(old)
def c7():
    t, k = Flaky(1), Clk(); r = orders.checkout(client.ShopClient(t, k), 4, 2)
    return r["price"] == {"ok": "/products/4/price"} and k.slept == [0.1]
def c8():
    import inspect
    return list(inspect.signature(client.ShopClient.get_product).parameters) == ["self", "product_id"] and \
        list(inspect.signature(orders.checkout).parameters) == ["client", "product_id", "qty"] and \
        config.RETRY == {"attempts": 3, "base": 0.1, "factor": 2.0}
for f in (c1, c2, c3, c4, c5, c6, c7, c8): check(f)
print("RESULT", ok, total)
'''
        rc, out = _py(code, d)
        base = _frac(out)
        rc2, o2 = _sh(f"{sys.executable} -m unittest -q test_client 2>&1 | tail -3", d)
        tests = "OK" in o2
        n_tests = len(re.findall(r"def test_", (Path(d) / "test_client.py").read_text())) if (Path(d) / "test_client.py").exists() else 0
        return 0.8 * base + 0.1 * tests + 0.1 * (n_tests >= 5), f"hidden={base:.2f} own_tests_ok={tests} n_tests={n_tests}"
    return setup, prompt, verify


# ------------------------------------------------------------------ H5 long-context trace (oracle: run the code)

def _gen_repo(d):
    d = Path(d)
    mods = {}
    mods["settings.py"] = '''import os
BASE_TIMEOUT = 10
PROFILES = {"dev": 0.5, "staging": 1.5, "prod": 3}
RETRY_BASE = 2
'''
    mods["envlayer.py"] = '''import os
from settings import BASE_TIMEOUT, PROFILES

def profile_factor():
    return PROFILES.get(os.environ.get("PROFILE", "dev"), 1)

def region_adjust(v):
    r = os.environ.get("REGION", "us")
    return {"us": v, "eu": v + 4, "ap": v * 1.25}.get(r, v)

def base():
    return BASE_TIMEOUT
'''
    mods["limits.py"] = '''import os
from envlayer import base, profile_factor, region_adjust

def raw_timeout():
    return region_adjust(base() * profile_factor())

def burst_multiplier():
    return 2 if os.environ.get("BURST") == "1" else 1

def cap():
    return float(os.environ.get("TIMEOUT_CAP", "60"))
'''
    mods["policy.py"] = '''from limits import raw_timeout, burst_multiplier, cap

def effective_timeout():
    v = raw_timeout() * burst_multiplier()
    return min(v, cap())

def legacy_timeout():
    # old name kept for the metrics exporter, NOT used by the client
    return raw_timeout() + 100
'''
    mods["retrypolicy.py"] = '''from settings import RETRY_BASE
from policy import effective_timeout

def attempt_timeout(attempt):
    return effective_timeout() * (RETRY_BASE ** (attempt - 1)) if attempt <= 2 else effective_timeout()
'''
    mods["client.py"] = '''from retrypolicy import attempt_timeout

def send(attempt=1):
    return attempt_timeout(attempt)
'''
    # distractor modules
    for i in range(24):
        mods[f"util{i}.py"] = f'''"""helper {i}"""
import os

def helper_{i}(x):
    y = x * {i + 2} + {i}
    if os.environ.get("HELPER_{i}"):
        y += 1
    return y

def unused_timeout_{i}():
    return helper_{i}(3)
'''
    for n, c in mods.items():
        (d / n).write_text(c)
    qs = [("PROFILE=staging REGION=eu", 1), ("PROFILE=prod REGION=ap BURST=1", 2), ("PROFILE=prod REGION=us BURST=1 TIMEOUT_CAP=40", 3)]
    return qs


def h_trace():
    prompt = ("This directory is a small Python project (about 30 modules). Answer the three questions below about the "
              "value returned by `client.send(attempt)` and write ANSWER.json as {\"q1\": number, \"q2\": number, "
              "\"q3\": number}. Environment variables not mentioned are unset.\n"
              "q1: PROFILE=staging REGION=eu, attempt=1.\n"
              "q2: PROFILE=prod REGION=ap BURST=1, attempt=2.\n"
              "q3: PROFILE=prod REGION=us BURST=1 TIMEOUT_CAP=40, attempt=3.")

    def setup(d):
        _gen_repo(d)

    def verify(d):
        truth = {}
        for key, env, att in (("q1", {"PROFILE": "staging", "REGION": "eu"}, 1),
                              ("q2", {"PROFILE": "prod", "REGION": "ap", "BURST": "1"}, 2),
                              ("q3", {"PROFILE": "prod", "REGION": "us", "BURST": "1", "TIMEOUT_CAP": "40"}, 3)):
            rc, out = _sh(f"{sys.executable} -c \"import client; print(client.send({att}))\"", d, env=env)
            truth[key] = float(out.strip().splitlines()[-1])
        try:
            got = json.loads((Path(d) / "ANSWER.json").read_text())
        except Exception as e:
            return 0.0, f"no answer ({e}) truth={truth}"
        ok = sum(abs(float(got.get(k, -1)) - v) < 1e-6 for k, v in truth.items())
        return ok / 3, f"got={got} truth={truth}"
    return setup, prompt, verify


# ------------------------------------------------------------------ H6 simultaneous constraints

def h_constraints():
    prompt = ("Create rle.py with two functions `encode(s: str) -> str` and `decode(s: str) -> str`. Format: a run of "
              "length 1 is the character alone, a longer run is the character followed by the count ('aaabcc' -> "
              "'a3bc2'). Input to encode contains only letters. HARD CONSTRAINTS for BOTH functions: (1) no `for` or "
              "`while` statements (comprehensions, recursion and itertools are fine); (2) the body, docstring "
              "included, is at most 12 lines; (3) every parameter and the return value has a type annotation; (4) a "
              "docstring that contains at least two doctest examples (>>>) that pass; (5) no `import` inside the "
              "function bodies. decode(encode(x)) == x must hold for any letters-only string, including the empty "
              "string.")

    def verify(d):
        code = r'''
import ast, doctest, importlib.util, random, sys
src = open("rle.py").read()
ok = total = 0
def chk(v):
    global ok, total
    total += 1; ok += bool(v)
try:
    tree = ast.parse(src)
    spec = importlib.util.spec_from_file_location("rle", "rle.py"); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
except Exception as e:
    print("error", e); print("RESULT 0 1"); sys.exit()
funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
for name in ("encode", "decode"):
    f = funcs.get(name)
    chk(f is not None)
    if f is None:
        for _ in range(5): chk(False)
        continue
    chk(not any(isinstance(n, (ast.For, ast.While, ast.AsyncFor)) for n in ast.walk(f)))
    chk((f.end_lineno - f.lineno + 1) <= 12 + 1)
    chk(f.returns is not None and all(a.annotation is not None for a in f.args.args))
    doc = ast.get_docstring(f) or ""
    chk(doc.count(">>>") >= 2)
    chk(not any(isinstance(n, (ast.Import, ast.ImportFrom)) for n in ast.walk(f)))
res = doctest.testmod(m, verbose=False)
chk(res.attempted >= 4 and res.failed == 0)
rnd = random.Random(3)
cases = [""] + ["".join(rnd.choice("abAB") * rnd.randint(1, 5) for _ in range(rnd.randint(0, 8))) for _ in range(40)]
good = 0
for s in cases:
    try: good += m.decode(m.encode(s)) == s
    except Exception: pass
chk(good == len(cases))
chk(m.encode("aaabcc") == "a3bc2" and m.encode("") == "" and m.encode("zzzzzzzzzzzz") == "z12")
print("RESULT", ok, total)
'''
        rc, out = _py(code, d)
        return _frac(out), out.strip().splitlines()[-1][:100] if out.strip() else ""
    return (lambda d: None), prompt, verify


# ------------------------------------------------------------------ H9 security review with decoys

SEC_FILE = '''"""Admin and file service (change under review)."""
import hashlib, os, pickle, sqlite3, yaml
from flask import Flask, abort, redirect, request, session, send_file

app = Flask(__name__)
app.secret_key = "dev-secret-123"            # session signing key
UPLOAD_DIR = "/srv/uploads"
ALLOWED_TABLES = {"orders": "orders", "invoices": "invoices"}
DB_PASSWORD = os.environ["DB_PASSWORD"]


def db():
    return sqlite3.connect("/srv/app.db")


def find_user(name):
    return db().execute(f"SELECT id, role FROM users WHERE name = '{name}'").fetchone()


def count_rows(table_key):
    table = ALLOWED_TABLES[table_key]
    return db().execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def get_order(order_id):
    return db().execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()


def download(filename):
    return send_file(os.path.join(UPLOAD_DIR, filename))


def download_safe(filename):
    full = os.path.abspath(os.path.join(UPLOAD_DIR, filename))
    if not full.startswith(UPLOAD_DIR + os.sep):
        abort(400)
    return send_file(full)


def load_prefs(blob):
    return pickle.loads(blob)


def load_config(text):
    return yaml.safe_load(text)


def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


def delete_user(user_id):
    db().execute("DELETE FROM users WHERE id = ?", (user_id,))


def delete_user_checked(user_id):
    if session.get("role") != "admin":
        abort(403)
    db().execute("DELETE FROM users WHERE id = ?", (user_id,))


def after_login():
    return redirect(request.args.get("next"))


def after_logout():
    target = request.args.get("next", "/")
    if not target.startswith("/") or target.startswith("//"):
        target = "/"
    return redirect(target)


def render_comment(text):
    return "<div>" + text + "</div>"


def render_comment_escaped(text):
    import html
    return "<div>" + html.escape(text) + "</div>"
'''
SEC_REAL = {"find_user": r"inject|interpol|f-string|parameter", "download": r"travers|\.\./|escape|directory|path",
            "load_prefs": r"pickle|deserial|arbitrary code|untrusted", "delete_user": r"auth|admin|permission|access control|check",
            "after_login": r"open redirect|redirect|validat|untrusted|next", "render_comment": r"xss|escape|html|script|inject"}
SEC_DECOY = ["count_rows", "get_order", "download_safe", "load_config", "hash_token", "delete_user_checked",
             "after_logout", "render_comment_escaped"]


def h_security():
    prompt = ("Security review of change_under_review.py. Write REVIEW.json: a JSON array of objects "
              "{\"function\": <function name>, \"issue\": <one-sentence description of the vulnerability>} listing "
              "ONLY real exploitable vulnerabilities. A pattern that looks risky but is actually safe in context is "
              "not a vulnerability: do not list it. Note module-level problems with function name `<module>`. Do "
              "not modify the file.")

    def setup(d):
        (Path(d) / "change_under_review.py").write_text(SEC_FILE)

    def verify(d):
        try:
            arr = json.loads((Path(d) / "REVIEW.json").read_text())
            names = [str(x.get("function", "")) for x in arr]
        except Exception as e:
            return 0.0, f"bad json ({e})"
        real = {"find_user", "download", "load_prefs", "delete_user", "after_login", "render_comment"}
        tp = len(real & set(names))
        fp = len([n for n in names if n in SEC_DECOY])
        secret = any(n == "<module>" for n in names)  # the hardcoded secret_key is a 7th real finding
        score = (tp + secret) / 7 - 0.15 * fp
        return max(0.0, score), f"tp={tp}/6 module_secret={secret} decoys_flagged={[n for n in names if n in SEC_DECOY]}"
    return setup, prompt, verify


# ------------------------------------------------------------------ H10 weighted interval scheduling (oracle: brute force)

def h_sched():
    prompt = ("Create sched.py with `best_schedule(jobs)` where jobs is a list of (start, end, profit) tuples with "
              "start < end; jobs may not overlap, but a job may start exactly when another ends. Return the list of "
              "chosen job INDICES (into the input list) that maximizes total profit. Ties: prefer the selection with "
              "the fewest jobs, and if still tied the lexicographically smallest sorted index list. Return indices "
              "sorted ascending. It must handle 20000 jobs in under 3 seconds.")

    def verify(d):
        code = r'''
import importlib.util, itertools, random, sys, time
spec = importlib.util.spec_from_file_location("sched", "sched.py"); m = importlib.util.module_from_spec(spec)
try: spec.loader.exec_module(m)
except Exception as e:
    print("import error", e); print("RESULT 0 1"); sys.exit()
def brute(jobs):
    n = len(jobs); best = (-1, 0, ())
    for mask in range(1 << n):
        idx = [i for i in range(n) if mask >> i & 1]
        iv = sorted(idx, key=lambda i: jobs[i][0])
        if any(jobs[iv[k]][1] > jobs[iv[k + 1]][0] for k in range(len(iv) - 1)): continue
        p = sum(jobs[i][2] for i in idx)
        key = (-p, len(idx), tuple(idx))
        if best[0] == -1 or key < (-best[0], best[1], best[2]): best = (p, len(idx), tuple(idx))
    return list(best[2])
rnd = random.Random(11)
ok = total = 0
for _ in range(60):
    n = rnd.randint(0, 9)
    jobs = []
    for _ in range(n):
        s = rnd.randint(0, 12); jobs.append((s, s + rnd.randint(1, 6), rnd.randint(1, 5)))
    total += 1
    try: ok += list(m.best_schedule(list(jobs))) == brute(jobs)
    except Exception: pass
big = []
for _ in range(20000):
    s = rnd.randint(0, 10**6); big.append((s, s + rnd.randint(1, 3000), rnd.randint(1, 100)))
total += 1
t = time.time()
try:
    r = m.best_schedule(big)
    el = time.time() - t
    iv = sorted(r, key=lambda i: big[i][0])
    valid = all(big[iv[k]][1] <= big[iv[k + 1]][0] for k in range(len(iv) - 1))
    ok += valid and el < 3 and len(set(r)) == len(r)
except Exception: pass
print("RESULT", ok, total)
'''
        rc, out = _py(code, d, timeout=180)
        return _frac(out), out.strip().splitlines()[-1][:100] if out.strip() else ""
    return (lambda d: None), prompt, verify


# ------------------------------------------------------------------ H11 interacting bugs behind a visible suite

LEDGER_OK = '''"""Account ledger. Rules: transfers move money between accounts; a fee of 1% (minimum 0.50) is charged to the
sender on every transfer above 100 (none at or below 100); the sender may never go below zero including the fee;
a single account may send at most 1000 per calendar day (fees do not count toward the limit); every successful
transfer is appended to the history; amounts are rounded half-up to cents."""
from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")


def money(x):
    return Decimal(str(x)).quantize(CENT, rounding=ROUND_HALF_UP)


class InsufficientFunds(Exception):
    pass


class LimitExceeded(Exception):
    pass


class Ledger:
    def __init__(self):
        self.balances = {}
        self.sent_today = {}
        self.history = []

    def open(self, name, amount=0):
        self.balances[name] = money(amount)

    def fee(self, amount):
        amount = money(amount)
        if amount <= 100:
            return Decimal("0.00")
        return max(money(amount * Decimal("0.01")), Decimal("0.50"))

    def transfer(self, src, dst, amount, day):
        amount = money(amount)
        if amount <= 0:
            raise ValueError("amount must be positive")
        fee = self.fee(amount)
        if self.balances[src] < amount + fee:
            raise InsufficientFunds(src)
        used = self.sent_today.get((src, day), Decimal("0.00"))
        if used + amount > 1000:
            raise LimitExceeded(src)
        self.balances[src] -= amount + fee
        self.balances[dst] += amount
        self.sent_today[(src, day)] = used + amount
        self.history.append((day, src, dst, amount, fee))
        return fee
'''
LEDGER_MUT = [
    ('if amount <= 100:', 'if amount < 100:'),
    ('return max(money(amount * Decimal("0.01")), Decimal("0.50"))', 'return min(money(amount * Decimal("0.01")), Decimal("0.50"))'),
    ('if self.balances[src] < amount + fee:', 'if self.balances[src] < amount:'),
    ('if used + amount > 1000:', 'if used + amount >= 1000:'),
    ('self.sent_today[(src, day)] = used + amount', 'self.sent_today[(src, day)] = used + amount + fee'),
    ('return Decimal(str(x)).quantize(CENT, rounding=ROUND_HALF_UP)', 'return Decimal(str(x)).quantize(CENT)'),
]
LEDGER_TESTS = '''import unittest
from decimal import Decimal as D
from ledger import Ledger, InsufficientFunds, LimitExceeded, money


class T(unittest.TestCase):
    def mk(self, a=5000, b=0):
        l = Ledger(); l.open("a", a); l.open("b", b); return l

    def test_no_fee_at_100(self):
        l = self.mk(); self.assertEqual(l.transfer("a", "b", 100, 1), D("0.00")); self.assertEqual(l.balances["a"], D("4900.00"))

    def test_fee_percent(self):
        l = self.mk(); self.assertEqual(l.transfer("a", "b", 500, 1), D("5.00"))

    def test_fee_minimum(self):
        l = self.mk(); self.assertEqual(l.transfer("a", "b", 101, 1), D("1.01")); self.assertEqual(l.fee(D("100.01")), D("1.00"))

    def test_fee_min_floor(self):
        l = self.mk(); self.assertEqual(l.fee(D("100.10")), D("1.00"))

    def test_insufficient_with_fee(self):
        l = self.mk(a=101)
        with self.assertRaises(InsufficientFunds):
            l.transfer("a", "b", 101, 1)

    def test_exact_funds_ok(self):
        l = self.mk(a=202); l.transfer("a", "b", 200, 1); self.assertEqual(l.balances["a"], D("0.00"))

    def test_daily_limit(self):
        l = self.mk(); l.transfer("a", "b", 900, 1)
        with self.assertRaises(LimitExceeded):
            l.transfer("a", "b", 101, 1)

    def test_daily_limit_exact(self):
        l = self.mk(); l.transfer("a", "b", 600, 1); l.transfer("a", "b", 400, 1); self.assertEqual(l.balances["b"], D("1000.00"))

    def test_limit_resets_next_day(self):
        l = self.mk(); l.transfer("a", "b", 1000, 1); l.transfer("a", "b", 1000, 2); self.assertEqual(l.balances["b"], D("2000.00"))

    def test_fee_not_in_limit(self):
        l = self.mk(); l.transfer("a", "b", 500, 1); l.transfer("a", "b", 500, 1)

    def test_rounding_half_up(self):
        self.assertEqual(money("2.675"), D("2.68")); self.assertEqual(money("0.005"), D("0.01"))

    def test_history(self):
        l = self.mk(); l.transfer("a", "b", 200, 3); self.assertEqual(l.history, [(3, "a", "b", D("200.00"), D("2.00"))])

    def test_failed_transfer_leaves_no_trace(self):
        l = self.mk(a=50)
        with self.assertRaises(InsufficientFunds):
            l.transfer("a", "b", 60, 1)
        self.assertEqual((l.history, l.balances["a"], l.sent_today), ([], D("50.00"), {}))

    def test_bad_amount(self):
        with self.assertRaises(ValueError):
            self.mk().transfer("a", "b", 0, 1)


if __name__ == "__main__":
    unittest.main()
'''


def h_ledger():
    prompt = ("ledger.py implements the rules in its module docstring, but the test suite test_ledger.py shows "
              "failures. Fix ledger.py so the behaviour matches the docstring and all tests pass. Do not modify the "
              "tests. There may be more than one defect, and fixing one can reveal another.")

    def setup(d):
        src = LEDGER_OK
        for old, new in LEDGER_MUT:
            assert old in src
            src = src.replace(old, new, 1)
        (Path(d) / "ledger.py").write_text(src)
        (Path(d) / "test_ledger.py").write_text(LEDGER_TESTS)

    def verify(d):
        rc, out = _sh(f"{sys.executable} -m unittest -q test_ledger 2>&1 | tail -4", d)
        visible = "OK" in out and rc == 0
        code = r'''
from decimal import Decimal as D
from ledger import Ledger, money
ok = total = 0
def c(v):
    global ok, total
    total += 1; ok += bool(v)
l = Ledger(); l.open("a", 5000); l.open("b", 0)
c(l.fee(D("100.00")) == D("0.00")); c(l.fee(D("100.01")) == D("1.00")); c(l.fee(D("2000")) == D("20.00"))
c(l.fee(D("333.335")) == D("3.33"))
c(money("1.005") == D("1.01")); c(money("-0.005") in (D("-0.01"), D("-0.00")))
l.transfer("a", "b", 1000, 1)
try: l.transfer("a", "b", 0.01, 1); c(False)
except Exception as e: c(type(e).__name__ == "LimitExceeded")
l2 = Ledger(); l2.open("a", 100); l2.open("b", 0)
try: l2.transfer("a", "b", 100, 1); c(True)
except Exception: c(False)
l3 = Ledger(); l3.open("a", 300); l3.open("b", 0)
try: l3.transfer("a", "b", 299, 1); c(False)
except Exception as e: c(type(e).__name__ == "InsufficientFunds")
print("RESULT", ok, total)
'''
        rc2, o2 = _py(code, d)
        hidden = _frac(o2)
        n_fail = len(re.findall(r"FAIL|ERROR", out))
        return 0.6 * (1.0 if visible else 0.0) + 0.4 * hidden, f"visible_ok={visible} hidden={hidden:.2f} tail={out.strip()[-60:]!r}"
    return setup, prompt, verify


HARD = {"h_expr": h_expr, "h_cache": h_cache, "h_retry": h_retry, "h_trace": h_trace, "h_constraints": h_constraints,
        "h_security": h_security, "h_sched": h_sched, "h_ledger": h_ledger}
