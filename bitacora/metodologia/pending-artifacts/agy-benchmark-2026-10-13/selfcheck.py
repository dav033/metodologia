import json, shutil, sys, importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location("hard", "hard.py"); h = importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
ROOT = Path("selfcheck"); shutil.rmtree(ROOT, ignore_errors=True)

REF = {}
REF["h_expr"] = {"calc.py": '''
import re
TOK = re.compile(r"\\s*(\\d+\\.\\d+|\\d+|//|\\*\\*|[-+*/%()])")
def evaluate(s):
    pos = 0; toks = []
    s2 = s.strip()
    if not s2: raise ValueError("empty")
    while pos < len(s):
        if s[pos].isspace(): pos += 1; continue
        m = TOK.match(s, pos)
        if not m: raise ValueError("bad char")
        toks.append(m.group(1)); pos = m.end()
    i = [0]
    def peek(): return toks[i[0]] if i[0] < len(toks) else None
    def eat(): t = peek(); i[0] += 1; return t
    def num(t): return float(t) if "." in t else int(t)
    def expr():
        v = term()
        while peek() in ("+", "-"):
            op = eat(); r = term(); v = v + r if op == "+" else v - r
        return v
    def term():
        v = unary()
        while peek() in ("*", "/", "//", "%"):
            op = eat(); r = unary()
            if op == "*": v = v * r
            elif op == "/": v = v / r
            elif op == "//": v = v // r
            else: v = v % r
        return v
    def unary():
        if peek() in ("+", "-"):
            op = eat(); v = unary(); return -v if op == "-" else v
        return power()
    def power():
        b = atom()
        if peek() == "**":
            eat(); e = unary(); return b ** e
        return b
    def atom():
        t = eat()
        if t is None: raise ValueError("eof")
        if t == "(":
            v = expr()
            if eat() != ")": raise ValueError("paren")
            return v
        if t[0].isdigit(): return num(t)
        raise ValueError("unexpected " + t)
    v = expr()
    if i[0] != len(toks): raise ValueError("trailing")
    return v
'''}
REF["h_cache"] = {"cache.py": h.CACHE_BUGGY.replace("<= self.ttl", "< self.ttl").replace('''        value, written = item
        if not self._live(written):
            del self._d[key]
            return default
        return value''', '''        value, written = item
        if not self._live(written):
            del self._d[key]
            return default
        self._d.move_to_end(key)
        return value''').replace('''        if key in self._d:
            self._d[key] = (value, self._d[key][1])
            return
        if len(self._d) >= self.max_size:
            self._d.popitem(last=False)
        self._d[key] = (value, self.clock())''', '''        self._purge()
        if key in self._d:
            del self._d[key]
        elif len(self._d) >= self.max_size:
            self._d.popitem(last=False)
        self._d[key] = (value, self.clock())''').replace('''    def __len__(self):
        return len(self._d)''', '''    def _purge(self):
        for k in [k for k, (_, w) in self._d.items() if not self._live(w)]:
            del self._d[k]

    def __len__(self):
        self._purge()
        return len(self._d)''')}
c = dict(h.SHOP)
REF["h_retry"] = {"config.py": h.SHOP["config.py"] + "RETRY = {'attempts': 3, 'base': 0.1, 'factor': 2.0}\n",
    "client.py": '''from clock import Clock
from transport import Transport, TransportError

import config


class ShopClient:
    def __init__(self, transport=None, clock=None):
        self.transport = transport or Transport()
        self.clock = clock or Clock()

    def _send(self, method, path, payload=None):
        r = config.RETRY
        delay = r["base"]
        for attempt in range(1, r["attempts"] + 1):
            try:
                return self.transport.send(method, path, payload)
            except TransportError:
                if attempt == r["attempts"]:
                    raise
                self.clock.sleep(delay)
                delay *= r["factor"]

    def get_product(self, product_id):
        if not isinstance(product_id, int):
            raise ValueError("product_id must be an int")
        return self._send("GET", f"/products/{product_id}")

    def get_price(self, product_id):
        return self._send("GET", f"/products/{product_id}/price")

    def place_order(self, product_id, qty):
        if qty < 1:
            raise ValueError("qty must be >= 1")
        return self._send("POST", "/orders", {"product": product_id, "qty": qty})
''',
    "test_client.py": h.SHOP["test_client.py"].replace("if __name__", "".join(
        f"\nclass R{i}(unittest.TestCase):\n    def test_r{i}(self):\n        self.assertTrue(True)\n" for i in range(4)) + "\n\nif __name__")}
REF["h_trace"] = {}
REF["h_constraints"] = {"rle.py": '''from itertools import groupby


def encode(s: str) -> str:
    """Run-length encode letters.

    >>> encode("aaabcc")
    'a3bc2'
    >>> encode("")
    ''
    """
    return "".join(c + (str(n) if n > 1 else "") for c, n in ((k, len(list(g))) for k, g in groupby(s)))


def decode(s: str) -> str:
    """Inverse of encode.

    >>> decode("a3bc2")
    'aaabcc'
    >>> decode("z12")
    'zzzzzzzzzzzz'
    """
    import re
    return "".join(c * int(n or 1) for c, n in re.findall(r"([A-Za-z])(\\d*)", s))
'''.replace("    import re\n", "").replace("from itertools import groupby", "import re\nfrom itertools import groupby")}
REF["h_security"] = {"REVIEW.json": json.dumps([{"function": f, "issue": "x"} for f in
    ("find_user", "download", "load_prefs", "delete_user", "after_login", "render_comment", "<module>")])}
REF["h_sched"] = {"sched.py": '''import bisect


def best_schedule(jobs):
    order = sorted(range(len(jobs)), key=lambda i: (jobs[i][1], i))
    ends = [jobs[i][1] for i in order]
    best = [(0, 0, ())]  # (profit, -count, index tuple) per prefix; compare by (-profit, count, tuple)
    prof = [0]; cnt = [0]; sel = [()]
    for k, i in enumerate(order):
        s, e, p = jobs[i]
        j = bisect.bisect_right(ends, s, 0, k)
        take = (prof[j] + p, cnt[j] + 1, tuple(sorted(sel[j] + (i,))))
        skip = (prof[k], cnt[k], sel[k])
        a = (-take[0], take[1], take[2]); b = (-skip[0], skip[1], skip[2])
        pick = take if a < b else skip
        prof.append(pick[0]); cnt.append(pick[1]); sel.append(pick[2])
    return list(sel[-1])
'''}
REF["h_ledger"] = {"ledger.py": h.LEDGER_OK}

bad = 0
for name, fn in h.HARD.items():
    setup, prompt, verify = fn()
    d = ROOT / name; d.mkdir(parents=True)
    setup(str(d))
    s0, n0 = verify(str(d))
    if name == "h_trace":
        rc, out = h._sh("true", str(d))
        import subprocess, os
        ans = {}
        for key, env, att in (("q1", {"PROFILE": "staging", "REGION": "eu"}, 1), ("q2", {"PROFILE": "prod", "REGION": "ap", "BURST": "1"}, 2), ("q3", {"PROFILE": "prod", "REGION": "us", "BURST": "1", "TIMEOUT_CAP": "40"}, 3)):
            r = subprocess.run([sys.executable, "-c", f"import client; print(client.send({att}))"], cwd=d, env={**os.environ, **env}, capture_output=True, text=True)
            ans[key] = float(r.stdout.strip()); 
        print("   trace truth:", ans)
        (d / "ANSWER.json").write_text(json.dumps(ans))
    for fname, content in REF[name].items():
        (d / fname).write_text(content)
    s1, n1 = verify(str(d))
    flag = "" if (s1 >= 0.95 and s0 <= 0.6) else "   <<<<<< VERIFIER SUSPECT"
    bad += bool(flag)
    print(f"{name:14} untouched={s0:.2f}  reference={s1:.2f}  | {n1[:90]}{flag}")
print("suspect verifiers:", bad)
