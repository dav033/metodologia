#!/usr/bin/env python3
"""Routing benchmark: the same objective tasks given to several agent configurations; hidden verification after the
run. Usage: bench.py OUT.jsonl [--only task,task] [--agents a,b]"""
import concurrent.futures, json, os, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUNS = ROOT / os.environ.get("BENCH_RUNS", "runs")
AGENTS = {
    "flash-low": ("agy", "gemini-3.8-flash-low"),
    "flash-med": ("agy", "gemini-3.8-flash-medium"),
    "flash-high": ("agy", "gemini-3.8-flash-high"),
    "haiku": ("claude", "haiku"),
    "luna-med": ("codex", "gpt-6-luna"),
    "sonnet": ("claude", "sonnet"),
}


def sh(cmd, cwd, timeout=60):
    try:
        r = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, timeout=timeout,
                           env={"PATH": os.environ["PATH"], "HOME": os.environ["HOME"], "PYTHONDONTWRITEBYTECODE": "1"})
        return r.returncode, (r.stdout + r.stderr)
    except subprocess.TimeoutExpired:
        return 124, "timeout"


def py(code, cwd):
    p = Path(cwd) / "_verify.py"
    p.write_text(code)
    return sh(f"{sys.executable} _verify.py", cwd, 60)


# ------------------------------------------------------------------ tasks: (setup, prompt, verify) -> score 0..1

def t_docs():
    prompt = ("Create README.md in the current directory documenting the command line tool `fx`. Use ONLY these facts, "
              "invent nothing else: the command is `fx`; it has one option `--rate` with default 1.0; the cache "
              "directory is set with the environment variable FX_CACHE_DIR; exit code 0 means success and exit code 2 "
              "means invalid arguments; it requires Python 3.10 or newer. Required sections, with these exact "
              "headings: `## Install`, `## Usage`, `## Exit codes`.")

    def verify(d):
        t = (Path(d) / "README.md").read_text() if (Path(d) / "README.md").exists() else ""
        checks = [bool(re.search(r"\bfx\b", t)), "--rate" in t and "1.0" in t, "FX_CACHE_DIR" in t,
                  re.search(r"\b0\b", t) and re.search(r"\b2\b", t), "3.10" in t,
                  all(h in t for h in ("## Install", "## Usage", "## Exit codes"))]
        flags = set(re.findall(r"(?<![\w-])--[a-z][a-z-]+", t))
        invented = flags - {"--rate"}
        score = sum(bool(c) for c in checks) / len(checks)
        return (score if not invented else max(0, score - 0.34)), f"checks={[bool(c) for c in checks]} invented_flags={sorted(invented)}"
    return (lambda d: None), prompt, verify


def t_impl_easy():
    prompt = ("Create text_utils.py with a function `slugify(text)`: lowercase the text, strip accents (é->e, ñ->n), "
              "replace every run of non-alphanumeric characters with a single '-', remove leading and trailing '-', and "
              "return 'untitled' if the result is empty.")

    def verify(d):
        code = '''
import importlib.util, sys
spec = importlib.util.spec_from_file_location("text_utils", "text_utils.py"); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
cases = [("Hello World","hello-world"),("  Café  con   leche!! ","cafe-con-leche"),("Año Nuevo","ano-nuevo"),("---","untitled"),("","untitled"),
 ("a_b-c","a-b-c"),("Ünï©ode 2026","uni-ode-2026"),("--x--","x")]
ok = 0
for i, o in cases:
    try: ok += m.slugify(i) == o
    except Exception: pass
print(ok, len(cases))
sys.exit(0 if ok == len(cases) else 1)
'''
        rc, out = py(code, d)
        m = re.findall(r"(\d+) (\d+)\s*$", out.strip())
        return (int(m[-1][0]) / int(m[-1][1]) if m else 0.0), out.strip()[-160:]
    return (lambda d: None), prompt, verify


def t_impl_medium():
    prompt = ("Create durations.py with `parse_duration(s)` returning total seconds as a number. Rules: units d, h, m, s "
              "(case-insensitive), any combination in descending order e.g. '1d2h3m4s', optional whitespace between "
              "parts, decimals allowed on any part ('1.5h' = 5400), a bare number string like '90' means seconds, "
              "leading/trailing whitespace ignored. Raise ValueError for: empty string, negative values, unknown units, "
              "units out of descending order ('3m1h'), the same unit twice ('1h1h'), and non-string input (TypeError).")

    def verify(d):
        code = '''
import importlib.util, sys
spec = importlib.util.spec_from_file_location("durations", "durations.py"); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
good = [("1d2h3m4s",93784),("90",90),("1.5h",5400),(" 2m 30s ",150),("1H",3600),("0s",0),("10m",600),("1d",86400),("1h 1s",3601),("0.5m",30)]
bad = [("",ValueError),("-5s",ValueError),("3m1h",ValueError),("1h1h",ValueError),("5x",ValueError),("abc",ValueError),("h",ValueError),(5,TypeError),("1h-2m",ValueError),("1 2 3",ValueError)]
ok = 0
for i, o in good:
    try: ok += abs(m.parse_duration(i) - o) < 1e-9
    except Exception: pass
for i, e in bad:
    try: m.parse_duration(i)
    except e: ok += 1
    except Exception: pass
print(ok, len(good) + len(bad))
'''
        rc, out = py(code, d)
        m = re.findall(r"(\d+) (\d+)\s*$", out.strip())
        return (int(m[-1][0]) / int(m[-1][1]) if m else 0.0), out.strip()[-160:]
    return (lambda d: None), prompt, verify


BUGGY = '''"""Inventory pages and stock helpers."""


def paginate(items, page, per_page=10):
    """Return the items of 1-based `page`."""
    start = page * per_page
    return items[start:start + per_page]


def add_tag(item, tags=[]):
    """Return a new tag list for `item` with its name appended."""
    tags.append(item["name"])
    return tags


def restock_cost(unit_price, qty):
    """Cost in dollars rounded to cents; every 10th unit is free (qty 25 pays for 23)."""
    paid = qty - qty // 10
    return round(unit_price * paid, 2)


def low_stock(items, threshold=5):
    """Names of items whose stock is below the threshold."""
    return [i["name"] for i in items if i["stock"] <= threshold]
'''
BUGGY_TESTS = '''import unittest
from inventory import paginate, add_tag, restock_cost, low_stock

class T(unittest.TestCase):
    def test_paginate_first(self): self.assertEqual(paginate(list(range(25)), 1), list(range(10)))
    def test_paginate_last(self): self.assertEqual(paginate(list(range(25)), 3), [20, 21, 22, 23, 24])
    def test_tag(self): self.assertEqual(add_tag({"name": "a"}), ["a"])
    def test_restock(self): self.assertEqual(restock_cost(2.5, 25), 57.5)
    def test_low(self): self.assertEqual(low_stock([{"name": "x", "stock": 5}, {"name": "y", "stock": 4}]), ["y"])

if __name__ == "__main__":
    unittest.main()
'''


def t_bugfix():
    prompt = ("The tests in test_inventory.py fail. Fix the bugs in inventory.py so every test passes. Do not edit the "
              "tests. Also look for any other defect of the same kind in that file and fix it.")

    def setup(d):
        (Path(d) / "inventory.py").write_text(BUGGY)
        (Path(d) / "test_inventory.py").write_text(BUGGY_TESTS)

    def verify(d):
        rc, out = sh(f"{sys.executable} -m unittest -q test_inventory 2>&1 | tail -3", d)
        visible = 1.0 if "OK" in out else 0.0
        code = '''
from inventory import add_tag, paginate, restock_cost
a = add_tag({"name": "a"}); b = add_tag({"name": "b"})
print(int(a == ["a"] and b == ["b"]), int(paginate(list(range(5)), 2, 2) == [2, 3]), int(restock_cost(1.005, 3) in (3.0, 3.01)))
'''
        rc2, out2 = py(code, d)
        nums = re.findall(r"\d", out2.strip().splitlines()[-1]) if out2.strip() else []
        hidden = sum(int(n) for n in nums[:3]) / 3 if len(nums) >= 3 else 0.0
        return 0.6 * visible + 0.4 * hidden, f"visible={visible} hidden={nums}"
    return setup, prompt, verify


CART = '''class Cart:
    MAX_QTY = 10

    def __init__(self):
        self.lines = {}

    def add(self, name, price, qty=1):
        if qty < 1 or qty > self.MAX_QTY:
            raise ValueError("qty out of range")
        if price < 0:
            raise ValueError("negative price")
        cur = self.lines.get(name, (price, 0))
        if cur[1] + qty > self.MAX_QTY:
            raise ValueError("qty out of range")
        self.lines[name] = (price, cur[1] + qty)

    def remove(self, name):
        del self.lines[name]

    def total(self, code=None):
        t = sum(p * q for p, q in self.lines.values())
        if code == "SAVE10":
            t = t * 0.9
        return round(t, 2)
'''
MUTANTS = [
    ("t = t * 0.9", "t = t * 0.1"),
    ("return round(t, 2)", "return t"),
    ("if qty < 1 or qty > self.MAX_QTY:", "if qty < 1 or qty >= self.MAX_QTY:"),
    ("        del self.lines[name]", "        self.lines.pop(name, None)"),
    ("if cur[1] + qty > self.MAX_QTY:", "if cur[1] + qty > self.MAX_QTY + 5:"),
]


def t_write_tests():
    prompt = ("cart.py contains a Cart class. Write test_cart.py using unittest that thoroughly tests it: every rule "
              "and edge case, including error cases. The tests must pass against the current implementation and "
              "must be strong enough to fail if the implementation were subtly wrong. Do not modify cart.py.")

    def setup(d):
        (Path(d) / "cart.py").write_text(CART)

    def verify(d):
        rc, out = sh(f"{sys.executable} -m unittest -q test_cart 2>&1 | tail -2", d)
        if rc != 0 or "OK" not in out:
            return 0.0, "tests do not pass on the original: " + out.strip()[-100:]
        killed = 0
        for old, new in MUTANTS:
            m = Path(d + "_m"); shutil.rmtree(m, ignore_errors=True); shutil.copytree(d, m)
            src = (m / "cart.py").read_text()
            assert old in src
            (m / "cart.py").write_text(src.replace(old, new, 1))
            rc, o = sh(f"{sys.executable} -m unittest -q test_cart 2>&1 | tail -2", str(m))
            killed += rc != 0 or "FAILED" in o
            shutil.rmtree(m, ignore_errors=True)
        return killed / len(MUTANTS), f"killed {killed}/{len(MUTANTS)} mutants"
    return setup, prompt, verify


REVIEW_FILE = '''# change under review: orders/report.py (new file)
import sqlite3
from datetime import datetime, timezone

def orders_since(conn: sqlite3.Connection, customer: str, since: datetime):
    # all orders of a customer created after `since`
    cur = conn.execute(
        f"SELECT id, total, created_at FROM orders WHERE customer = '{customer}' AND created_at > ?",
        (since.isoformat(),),
    )
    return [dict(id=r[0], total=r[1], created_at=r[2]) for r in cur.fetchall()]

def average_total(orders):
    return sum(o["total"] for o in orders) / len(orders)

def is_recent(order, days=7):
    created = datetime.fromisoformat(order["created_at"])
    return (datetime.now() - created).days < days

def format_money(cents: int) -> str:
    return f"${cents // 100}.{cents % 100:02d}"

def top_customers(totals: dict, n=3):
    return sorted(totals, key=totals.get, reverse=True)[:n]
'''


def t_review():
    prompt = ("Review the file change_under_review.py as a strict code reviewer. Write REVIEW.md listing ONLY real "
              "defects (bugs, security problems, crashes), each as a bullet with the function name, what is wrong and "
              "why it matters. Do not list style opinions, and do not flag code that is correct. Do not modify the file.")

    def setup(d):
        (Path(d) / "change_under_review.py").write_text(REVIEW_FILE)

    def verify(d):
        p = Path(d) / "REVIEW.md"
        t = p.read_text().lower() if p.exists() else ""
        found = [bool(re.search(r"injection|parameteri|f-string|string interpol|format.*sql", t)),
                 bool(re.search(r"zero.?division|empty (list|orders)|len\(orders\)|no orders|divide by zero|average_total", t)),
                 bool(re.search(r"naive|timezone|tz|utc|aware", t))]
        bullets = len(re.findall(r"^(?:[-*]|\d+\.)\s", t, re.M))
        score = sum(found) / 3
        if bullets > 5:  # reporting correct code as defective
            score = max(0.0, score - 0.15 * (bullets - 5))
        return score, f"found={found} bullets={bullets}"
    return setup, prompt, verify


PKG = {
    "cache.py": '''import os
from storage import write_blob

def save(key, data):
    path = os.path.join(CACHE_DIR, key)
    write_blob(path, data)

CACHE_DIR = "/tmp/c"
''',
    "storage.py": '''def write_blob(path, data):
    with open(path, "wb") as fh:
        fh.write(data)

def read_blob(path):
    with open(path, "rb") as fh:
        return fh.read()
''',
    "sync.py": '''from cache import save

def refresh(items):
    for k, v in items:
        save(k, v)
''',
    "api.py": '''from sync import refresh
from storage import read_blob

def handle_update(payload):
    refresh(payload["items"])

def handle_read(path):
    return read_blob(path)
''',
    "cli.py": '''from api import handle_update

def main():
    handle_update({"items": []})
''',
    "report.py": '''from storage import read_blob

def show(path):
    return read_blob(path)[:20]
''',
}


def t_explore():
    prompt = ("Explore the Python files in this directory. Find every function that (directly or indirectly) writes "
              "to disk, i.e. calls open() in write mode or calls a function that does. Write ANSWER.json with the "
              "form {\"writers\": [\"module.function\", ...]} listing ALL such functions (module.function names, "
              "including the lowest-level one and every function that reaches it through calls). Nothing else.")
    truth = {"storage.write_blob", "cache.save", "sync.refresh", "api.handle_update", "cli.main"}

    def setup(d):
        for n, c in PKG.items():
            (Path(d) / n).write_text(c)

    def verify(d):
        p = Path(d) / "ANSWER.json"
        try:
            got = set(json.loads(p.read_text())["writers"])
        except Exception as e:
            return 0.0, f"bad answer: {e}"
        tp = len(got & truth)
        fp = len(got - truth)
        return max(0.0, (tp - fp) / len(truth)), f"tp={tp} fp={sorted(got - truth)} missing={sorted(truth - got)}"
    return setup, prompt, verify


def t_refactor():
    prompt = ("Rename the function `get_user` to `fetch_user` everywhere it is defined, called or mentioned in this "
              "project (code, tests and docs), and add a keyword parameter `timeout=5` to it (use it only by "
              "returning it inside the result dict under 'timeout'). Do NOT touch `get_user_agent` or anything else "
              "with a similar name. All tests must still pass; update them where they reference the old name.")

    files = {
        "users.py": 'def get_user(uid):\n    return {"id": uid}\n\ndef get_user_agent(req):\n    return req.get("ua", "none")\n',
        "service.py": 'from users import get_user, get_user_agent\n\ndef greet(uid, req):\n    u = get_user(uid)\n    return f"hi {u[\'id\']} via {get_user_agent(req)}"\n',
        "test_service.py": 'import unittest\nfrom service import greet\nfrom users import get_user\n\nclass T(unittest.TestCase):\n    def test_greet(self):\n        self.assertEqual(greet(7, {"ua": "x"}), "hi 7 via x")\n    def test_get(self):\n        self.assertEqual(get_user(3)["id"], 3)\n\nif __name__ == "__main__":\n    unittest.main()\n',
        "README.md": "# users\n\nUse `get_user(uid)` to load a user. `get_user_agent(req)` reads the UA header.\n",
    }

    def setup(d):
        for n, c in files.items():
            (Path(d) / n).write_text(c)

    def verify(d):
        allt = {n: (Path(d) / n).read_text() for n in files if (Path(d) / n).exists()}
        old_left = sum(len(re.findall(r"\bget_user\b", t)) for t in allt.values())
        ua_kept = "get_user_agent" in allt.get("users.py", "") and "get_user_agent" in allt.get("service.py", "") \
            and "get_user_agent" in allt.get("README.md", "")
        new_def = "def fetch_user" in allt.get("users.py", "") and "timeout" in allt.get("users.py", "")
        rc, out = sh(f"{sys.executable} -m unittest -q test_service 2>&1 | tail -2", d)
        checks = [old_left == 0, ua_kept, new_def, "OK" in out and rc == 0, "fetch_user" in allt.get("README.md", "")]
        return sum(checks) / len(checks), f"old_left={old_left} checks={checks}"
    return setup, prompt, verify


def t_json_format():
    text = ("Invoice INV-2026-0042 issued 2026-03-14 to Acme Constructions LLC (tax id 98-7654321). Subtotal 1,250.00 USD, "
            "tax 8.25% = 103.13 USD, total 1,353.13 USD. Payment terms: net 30, due 2026-04-13. Contact: ana.ruiz@acme.example")
    prompt = ("Read invoice.txt and write out.json containing exactly one JSON object with these keys and nothing else: "
              "invoice_number (string), issue_date (YYYY-MM-DD string), customer (string), subtotal (number), "
              "tax_rate (number, percent), tax (number), total (number), currency (string), due_date (YYYY-MM-DD string), "
              "email (string).")

    def setup(d):
        (Path(d) / "invoice.txt").write_text(text)

    def verify(d):
        try:
            o = json.loads((Path(d) / "out.json").read_text())
        except Exception as e:
            return 0.0, f"invalid json: {e}"
        want = {"invoice_number": "INV-2026-0042", "issue_date": "2026-03-14", "customer": "Acme Constructions LLC",
                "subtotal": 1250.0, "tax_rate": 8.25, "tax": 103.13, "total": 1353.13, "currency": "USD",
                "due_date": "2026-04-13", "email": "ana.ruiz@acme.example"}
        ok = sum(1 for k, v in want.items() if k in o and (abs(o[k] - v) < 0.005 if isinstance(v, float) else o[k] == v))
        extra = set(o) - set(want)
        return max(0.0, ok / len(want) - 0.1 * len(extra)), f"ok={ok}/10 extra={sorted(extra)}"
    return setup, prompt, verify


TASKS = {"docs": t_docs, "impl_easy": t_impl_easy, "impl_medium": t_impl_medium, "bugfix": t_bugfix,
         "write_tests": t_write_tests, "review": t_review, "explore": t_explore, "refactor": t_refactor,
         "json_format": t_json_format}


import hard as _hard
TASKS.update(_hard.HARD)

# ------------------------------------------------------------------ running agents

def run_agent(kind, model, workdir, prompt, timeout=900):
    start = time.time()
    env = {**os.environ}
    for k in ("CLAUDE_CONFIG_DIR", "CODEX_HOME", "BITACORA_RUN", "BITACORA_TASK", "BITACORA_PROJECT", "BITACORA_SESSION"):
        env.pop(k, None)
    if kind == "agy":
        argv = ["agy", "--model", model, "--dangerously-skip-permissions", "--output-format", "stream-json",
                f"--print={prompt}"]
        stdin = None
    elif kind == "claude":
        argv = ["claude", "-p", "--model", model, "--dangerously-skip-permissions", "--output-format", "json", prompt]
        stdin = None
    else:
        env["CODEX_HOME"] = str(Path.home() / ".codex-luis")
        argv = ["codex", "exec", "--dangerously-bypass-approvals-and-sandbox", "--skip-git-repo-check", "-C", workdir,
                "-m", model, "-c", 'model_reasoning_effort="medium"', "-"]
        stdin = prompt
    try:
        r = subprocess.run(argv, cwd=workdir, env=env, input=stdin, capture_output=True, text=True, timeout=timeout)
        out, rc, timed = r.stdout + "\n" + r.stderr, r.returncode, False
    except subprocess.TimeoutExpired as e:
        out, rc, timed = (e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or ""), -9, True
    secs = time.time() - start
    usage = {"input": None, "output": None, "thinking": None, "total": None, "turns": None, "cost": None}
    limit = bool(re.search(r"RESOURCE_EXHAUSTED|usage limit|quota|session limit|at capacity|\b429\b", out[-3000:], re.I)) and rc != 0
    try:
        if kind == "agy":
            for line in reversed(out.splitlines()):
                if line.startswith("{") and '"event": "result"' in line.replace('":"', '": "'):
                    res = json.loads(line)["result"]
                    u = res.get("usage") or {}
                    usage.update(input=u.get("input_tokens"), output=u.get("output_tokens"),
                                 thinking=u.get("thinking_tokens"), total=u.get("total_tokens"),
                                 turns=res.get("num_turns"))
                    if res.get("status") != "SUCCESS":
                        limit = limit or "EXHAUSTED" in json.dumps(res)
                    break
        elif kind == "claude":
            res = json.loads(out.split("\n")[0]) if out.strip().startswith("{") else {}
            u = res.get("usage") or {}
            usage.update(input=u.get("input_tokens"), output=u.get("output_tokens"), turns=res.get("num_turns"),
                         cost=res.get("total_cost_usd"),
                         total=(u.get("input_tokens") or 0) + (u.get("output_tokens") or 0)
                         + (u.get("cache_read_input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0))
        else:
            m = re.findall(r"tokens used\s*\n\s*([\d,]+)", out)
            usage["total"] = int(m[-1].replace(",", "")) if m else None
    except Exception:
        pass
    return {"rc": rc, "timed_out": timed, "seconds": round(secs, 1), "usage": usage, "limit": limit,
            "tail": re.sub(r"\s+", " ", out[-500:])}


def rescore(task, agent):
    d = RUNS / f"{task}-{agent}"
    setup, prompt, verify = TASKS[task]()
    return verify(str(d))


def one(task, agent):
    kind, model = AGENTS[agent]
    d = RUNS / f"{task}-{agent}"
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    setup, prompt, verify = TASKS[task]()
    setup(str(d))
    r = run_agent(kind, model, str(d), prompt)
    try:
        score, note = verify(str(d))
    except Exception as e:
        score, note = 0.0, f"verify error {type(e).__name__}: {e}"
    files = sorted(p.name for p in d.iterdir() if not p.name.startswith("_") and p.name != "__pycache__")
    return {"task": task, "agent": agent, "model": model, "score": round(score, 3), "note": note[:300], "files": files, **r}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("out"); ap.add_argument("--only"); ap.add_argument("--agents")
    ns = ap.parse_args()
    out = Path(ns.out)
    tasks = ns.only.split(",") if ns.only else list(TASKS)
    agents = ns.agents.split(",") if ns.agents else list(AGENTS)
    jobs = [(t, a) for t in tasks for a in agents]
    par = {"agy": 3, "claude": 2, "codex": 2}
    print(f"{len(jobs)} runs", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex, out.open("a") as fh:
        for row in ex.map(lambda j: one(*j), jobs):
            fh.write(json.dumps(row) + "\n"); fh.flush()
            print(f"{row['task']:12} {row['agent']:10} score={row['score']:.2f} {row['seconds']:6.1f}s "
                  f"tok={row['usage'].get('total')} {'LIMIT' if row['limit'] else ''} {row['note'][:70]}", flush=True)
