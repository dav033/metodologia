"""Impact selection for the regression: which suites of skill/scripts/tests a branch's changed paths can reach (D-NNN).

Each suite's reach is walked forward over a static graph of the repository (every .py parsed with `ast`; assets read
for the file names they hold), and the suite is selected when its reach holds a changed path. A suite reaches
  - the modules it imports, and everything those import at module level, transitively;
  - lazy imports (inside a function), module names in strings (`importlib.import_module("bt_x")`, `mock.patch(
    "bt_x.f")`, `-m bt_durable`) and scripts it names (`SCRIPTS / "bitacora.py"`, run as a subprocess) — but only from
    the suite itself and from what it imports directly (`LAZY_DEPTH`). Followed everywhere, they would reach the whole
    tree: `bt_core` lazily imports `bt_index`, which imports most of the CLI, and every suite imports `bt_core`;
  - the assets any reached file names (`ASSETS / "plans.js"`; assets name each other the same way), the files under a
    directory it names (`"agents/designer/skills/david-ui-kit/real"`), the files a glob of it matches in a directory it
    names, and — for the suite itself — every .py when it globs `*.py` or runs `unittest discover`.
Changed suites are selected, and so is the always-run set (the boundary, integration and contract suites).

The selection is not trusted, and the full regression runs, when the change reaches what the graph cannot see: the
dependencies (`pyproject.toml` beyond `py-modules`, `uv.lock`, `.python-version`), the regression's own code, the tests'
shared helpers and fixtures (any file of a tests/ folder that is not a test_*.py), a changed file no suite reaches (read
by a computed path, or only through deep lazy imports) — or when more than `integrate.selective_max_percent` of the
suites are selected anyway. Documentation (.md outside agents/ and templates/) may be reached by nothing.

usage: python3 bt_regress_select.py <worktree> [base ref, default main]
"""
from __future__ import annotations

import ast
import fnmatch
import hashlib
import os
import re
import subprocess
import sys
import tomllib
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

TESTS = "skill/scripts/tests"
PRIMARY_ROOTS = ("skill/scripts", "skill/scripts/tests")            # what bt_regress puts on PYTHONPATH
PRUNE = {".git", ".venv", "node_modules", "__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache"}
PRUNE_TOP = {"bitacora"}                                             # the live bitácora, never code
ASSET_SUFFIXES = {".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".css", ".html", ".json", ".sh", ".service", ".toml"}
UNTRUSTED = {"uv.lock": "uv.lock changed (dependencies)", ".python-version": ".python-version changed (interpreter)",
             "skill/scripts/bt_regress.py": "the regression itself changed",
             "skill/scripts/bt_regress_select.py": "the selection itself changed"}
DOC_SUFFIXES = {".md", ".txt", ".rst"}
RUNTIME_DOC_DIRS = ("skill/templates/", "skill/agents/")             # prompts and templates are read at run time
ALWAYS = ("test_scheduler_integration", "test_plan_boundary", "test_stdlib_boundary", "test_wiring_contracts",
          "test_package_modules")
ALWAYS_PATTERN = re.compile(r"_(boundary|integration|contracts?)$")
GENERIC_PARTS = {"skill", "scripts"}
# where code lives: naming one is a PYTHONPATH or a prefix test, and the imports already say what is used from it
CODE_ROOTS = {"skill", "skill/scripts", "skill/scripts/tests"}
LAZY_DEPTH = 2
DEFAULT_MAX_PERCENT = 40
FILE_TOKEN = re.compile(r"[\w.@+-]*[\w-]\.[A-Za-z]\w{0,9}\b")
MODULE_STRING = re.compile(r"^[A-Za-z_]\w*(\.[A-Za-z_]\w*)*$")
SCAN_CALLS = {"glob", "rglob", "iglob", "iterdir", "walk", "listdir", "scandir", "iter_modules", "walk_packages"}


# ------------------------------------------------------------------------------------------------ the graph
@dataclass
class Node:
    path: str                                           # repository-relative, posix
    imports: set[str] = field(default_factory=set)      # module-level imports: always followed
    lazy: set[str] = field(default_factory=set)         # imports inside functions, module names in strings
    names: set[str] = field(default_factory=set)        # file names its string constants hold
    parts: set[str] = field(default_factory=set)        # path components its string constants hold
    dirs: set[str] = field(default_factory=set)         # repository directories its string constants name
    globs: list[str] = field(default_factory=list)      # patterns it scans with ("*" when computed)
    scans_python: bool = False                          # globs *.py, runs `unittest discover`, walks packages


@dataclass(frozen=True)
class Parsed:
    """What a file says, before any name is resolved: cacheable by content."""
    imports: tuple[tuple[str, int, tuple[str, ...], bool], ...] = ()   # (module, level, names, inside a function)
    strings: tuple[str, ...] = ()
    globs: tuple[str, ...] = ()
    scans_python: bool = False


def parse_python(text: str) -> Parsed:
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return Parsed()
    functions, imports, strings, globs, scans = [], [], [], [], False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            functions.append((node.lineno, node.end_lineno or node.lineno))
        elif isinstance(node, ast.Import):
            imports += [(alias.name, 0, (), node.lineno) for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            imports.append((node.module or "", node.level, tuple(a.name for a in node.names), node.lineno))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            strings.append(node.value)
            scans |= node.value == "discover"
        elif isinstance(node, ast.Call):
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else func.id if isinstance(func, ast.Name) else ""
            if name in SCAN_CALLS:
                first = node.args[0] if node.args else None
                pattern = first.value if isinstance(first, ast.Constant) and isinstance(first.value, str) else "*"
                scans |= name in ("iter_modules", "walk_packages") or pattern.endswith(".py")
                globs.append(pattern)
    lazy = lambda line: any(a < line <= b for a, b in functions)            # noqa: E731 - the def line is outside
    return Parsed(tuple((m, lv, names, lazy(line)) for m, lv, names, line in imports), tuple(strings), tuple(globs),
                  scans)


def parse_asset(text: str) -> Parsed:
    return Parsed(strings=tuple(re.findall(r"""["'`]([^"'`\n]{1,300})["'`]""", text)))


def _walk(repo: Path) -> tuple[list[str], set[str]]:
    files, dirs = [], set()
    for top, subdirs, names in os.walk(repo):
        rel = Path(top).relative_to(repo).as_posix()
        subdirs[:] = [d for d in subdirs if d not in PRUNE and not d.endswith(".egg-info")
                      and not (rel == "." and d in PRUNE_TOP)]
        if rel != ".":
            dirs.add(rel)
        files += [name if rel == "." else f"{rel}/{name}" for name in names]
    return sorted(files), dirs


def _console_scripts(repo: Path) -> dict[str, str]:
    """`bt-durable` -> `bt_durable.cli`: a test that runs a console script runs its module."""
    try:
        scripts = tomllib.loads((repo / "pyproject.toml").read_text(encoding="utf-8"))["project"]["scripts"]
    except (OSError, KeyError, TypeError, tomllib.TOMLDecodeError):
        return {}
    return {name: str(target).split(":")[0] for name, target in scripts.items()}


def _module_maps(files: list[str]) -> tuple[dict[str, str], dict[str, list[str]]]:
    """name -> path on the regression's roots; name -> candidate paths in every other folder holding Python."""
    primary: dict[str, str] = {}
    for root in PRIMARY_ROOTS:
        for path in files:
            if path.endswith(".py") and path.startswith(root + "/"):
                parts = path[len(root) + 1:-3].split("/")
                if root == PRIMARY_ROOTS[0] and parts[0] == "tests":
                    continue
                if parts[-1] == "__init__":
                    parts = parts[:-1]
                if parts and all(p.isidentifier() for p in parts):
                    primary.setdefault(".".join(parts), path)
    secondary: dict[str, list[str]] = {}
    for path in files:
        if path.endswith(".py") and not path.startswith(PRIMARY_ROOTS[0] + "/"):
            pure = PurePosixPath(path)
            name = pure.parent.name if pure.stem == "__init__" else pure.stem
            if name.isidentifier():
                secondary.setdefault(name, []).append(path)
    return primary, secondary


class Graph:
    """Every file of the repository but the live bitácora, and what each Python file or asset depends on."""

    def __init__(self, repo: Path, extra: list[str] = (), cache: dict | None = None):
        self.repo = Path(repo)
        self.cache = {} if cache is None else cache            # (python, sha1) -> Parsed, shared across trees
        self.files, self.dir_set = _walk(self.repo)
        known = sorted(set(self.files) | set(extra))           # deleted paths still resolve as import targets
        self.known = set(known)
        self.primary, self.secondary = _module_maps(known)
        self.by_name: dict[str, list[str]] = {}
        for path in known:
            self.by_name.setdefault(PurePosixPath(path).name, []).append(path)
        self._dir_index: dict[str, list[str]] = {}
        for d in self.dir_set:
            self._dir_index.setdefault(PurePosixPath(d).name, []).append(d)
        self.scripts = _console_scripts(self.repo)
        self.nodes: dict[str, Node] = {}
        for path in self.files:
            suffix = PurePosixPath(path).suffix
            if suffix == ".py":
                self.nodes[path] = self._python(path)
            elif suffix in ASSET_SUFFIXES:
                self.nodes[path] = self._asset(path)
        self._named: dict[str, list[str]] = {}

    def _parsed(self, path: str, python: bool) -> Parsed:
        try:
            text = (self.repo / path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            return Parsed()
        key = (python, hashlib.sha1(text.encode("utf-8", "replace")).hexdigest())
        if key not in self.cache:
            self.cache[key] = parse_python(text) if python else parse_asset(text)
        return self.cache[key]

    def _python(self, path: str) -> Node:
        node = Node(path)
        parsed = self._parsed(path, True)
        for module, level, names, lazy in parsed.imports:
            (node.lazy if lazy else node.imports).update(self._resolve_import(path, module, level, list(names)))
        for text in parsed.strings:
            if MODULE_STRING.match(text):
                found = self._resolve_dotted(text, secondary=False)
                node.lazy |= found | {main for init in found if init.endswith("/__init__.py")   # `-m package`
                                      if (main := init.replace("/__init__.py", "/__main__.py")) in self.known}
            elif text in self.scripts:                                                       # a console script
                node.lazy |= self._resolve_dotted(self.scripts[text], secondary=False)
        node.lazy -= node.imports
        self._strings(node, parsed.strings, dirs=True)
        node.globs, node.scans_python = list(parsed.globs), parsed.scans_python
        return node

    def _asset(self, path: str) -> Node:
        node = Node(path)
        self._strings(node, self._parsed(path, False).strings, dirs=False)     # data in a fixture names no folder
        return node

    def _strings(self, node: Node, strings, *, dirs: bool) -> None:
        for text in strings:
            node.names |= {PurePosixPath(token).name for token in FILE_TOKEN.findall(text)}
            pieces = [p for p in re.split(r"[/\\]", text) if p and p not in (".", "..")]
            node.parts |= set(pieces)
            if dirs and len(pieces) > 1 and len(text) < 300 and " " not in text:
                suffix = "/".join(pieces)
                node.dirs |= {d for d in self._dir_index.get(pieces[-1], []) if d not in CODE_ROOTS
                              and (d == suffix or d.endswith("/" + suffix))}

    def _resolve_dotted(self, dotted: str, secondary: bool = True) -> set[str]:
        """Every module along `a.b.c` that exists: `a/__init__`, `a/b/__init__`, `a/b/c`."""
        parts = dotted.split(".")
        found = {hit for i in range(1, len(parts) + 1) if (hit := self.primary.get(".".join(parts[:i])))}
        if not found and secondary:
            found = set(self.secondary.get(parts[0], []))
        return found

    def _resolve_import(self, path: str, module: str, level: int, names: list[str]) -> set[str]:
        if level == 0:
            found = self._resolve_dotted(module)
            for name in names:                                  # `from pkg import submodule`
                found |= {p for p in self._resolve_dotted(f"{module}.{name}", secondary=False)
                          if p.endswith((f"/{name}.py", f"/{name}/__init__.py"))}
            return found
        base = PurePosixPath(path).parent
        for _ in range(level - 1):
            base = base.parent
        parts = module.split(".") if module else []
        target = base.joinpath(*parts)
        candidates = [f"{target}.py", f"{base}/__init__.py"]
        candidates += [f"{base.joinpath(*parts[:i])}/__init__.py" for i in range(1, len(parts) + 1)]
        candidates += [c for name in names for c in (f"{target}/{name}.py", f"{target}/{name}/__init__.py")]
        return {c for c in candidates if c in self.known}

    def named(self, path: str) -> list[str]:
        """Files the node at `path` names: a unique file name, or a shared one (SKILL.md, cli.py) next to one of its
        folders' names."""
        if path not in self._named:
            node = self.nodes[path]
            hits = []
            for name in node.names:
                for target in self.by_name.get(name, []):
                    shared = len(self.by_name[name]) > 1
                    if target != path and (not shared or set(PurePosixPath(target).parent.parts) - GENERIC_PARTS
                                           & node.parts):
                        hits.append(target)
            self._named[path] = sorted(hits)
        return self._named[path]

    def reach(self, start: str, lazy_depth: int = LAZY_DEPTH) -> dict[str, tuple[str, str]]:
        """Every file `start` reaches by imports and names: {file: (from, verb)}; see the module's docstring."""
        seen: dict[str, tuple[str, str]] = {start: ("", "")}
        depth = {start: 0}
        queue = deque([start])
        while queue:
            current = queue.popleft()
            node = self.nodes.get(current)
            if node is None:
                continue
            near = depth[current] < lazy_depth
            edges = [(t, "imports") for t in sorted(node.imports)]
            edges += [(t, "imports") for t in sorted(node.lazy)] if near else []
            for target in self.named(current):
                if not target.endswith(".py"):
                    edges.append((target, "reads"))
                elif near:
                    edges.append((target, "runs"))
            for target, verb in edges:
                if target not in seen:
                    seen[target] = (current, verb)
                    depth[target] = depth[current] + 1
                    queue.append(target)
        return seen

    def touches(self, path: str, changed: str, *, suite: bool = False) -> str:
        """How the node at `path` reads `changed` as data, or "": a directory it names, a glob of a folder it names,
        every .py when it is the suite and scans the source tree."""
        node = self.nodes.get(path)
        if node is None:
            return ""
        pure = PurePosixPath(changed)
        held = [d for d in node.dirs if changed.startswith(d + "/")]
        if held:
            return f"reads {max(held, key=len).removeprefix('skill/')}/"
        if suite and node.scans_python and pure.suffix == ".py":
            return "scans *.py"
        folders = set(pure.parent.parts) - GENERIC_PARTS
        patterns = [g.rsplit("/", 1)[-1] for g in node.globs]
        if pure.suffix == ".py":                                 # a computed pattern reads data, not the source tree
            patterns = [g for g in patterns if g.endswith(".py")]
        if patterns and folders & node.parts and any(fnmatch.fnmatch(pure.name, g) for g in patterns):
            return f"scans {sorted(folders & node.parts)[0]}/"
        return ""


# ------------------------------------------------------------------------------------------------ selection
@dataclass
class Selection:
    changed: list[str]
    total: int
    suites: dict[str, list[str]] = field(default_factory=dict)   # suite -> why
    full: str = ""                                                 # why the selection is not trusted ("" = it is)

    @property
    def names(self) -> list[str]:
        return sorted(self.suites)

    @property
    def trusted(self) -> bool:
        return not self.full

    def headline(self) -> str:
        text = f"selection: {len(self.suites)}/{self.total} suites for {len(self.changed)} changed path(s)"
        return text + (f"; NOT trusted, full regression: {self.full}" if self.full else "")

    def describe(self, limit: int = 3) -> list[str]:
        lines = [self.headline()]
        for suite in self.names:
            why = self.suites[suite]
            more = f" (+{len(why) - limit} more)" if len(why) > limit else ""
            lines.append(f"  {suite}: {'; '.join(why[:limit])}{more}")
        return lines


def _short(path: str) -> str:
    """`skill/scripts/bt_durable/cli.py` -> `bt_durable.cli`; `skill/assets/plans.js` -> `assets/plans.js`."""
    if path.startswith("skill/scripts/") and path.endswith(".py"):
        return path[len("skill/scripts/"):-3].removeprefix("tests/").replace("/", ".").removesuffix(".__init__")
    return path.removeprefix("skill/")


def _hops(seen: dict[str, tuple[str, str]], target: str) -> list[str]:
    """The files from the suite (excluded) to `target` (included)."""
    chain = []
    while seen[target][0]:
        chain.append(target)
        target = seen[target][0]
    return chain[::-1]


def _via(hops: list[str]) -> str:
    return "" if len(hops) < 2 else f" via {_short(hops[0])}" + (f" (+{len(hops) - 2})" if len(hops) > 2 else "")


def _pyproject_trusted(repo: Path, base: str) -> bool:
    """A pyproject.toml that differs from `base` only in `py-modules` (a module added or removed) changes no
    dependency."""
    def without_modules(text: str) -> dict:
        data = tomllib.loads(text)
        data.get("tool", {}).get("setuptools", {}).pop("py-modules", None)
        return data
    old = subprocess.run(["git", "-C", str(repo), "show", f"{base}:pyproject.toml"], capture_output=True, text=True,
                         check=False)
    try:
        return old.returncode == 0 and without_modules(old.stdout) == without_modules(
            (repo / "pyproject.toml").read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return False


def _untrusted(path: str, repo: Path, base: str) -> str:
    if path in UNTRUSTED:
        return UNTRUSTED[path]
    if path == "pyproject.toml" and not _pyproject_trusted(repo, base):
        return "pyproject.toml changed beyond py-modules (dependencies or build)"
    parts = PurePosixPath(path).parts
    if path.startswith("skill/scripts/") and "tests" in parts and not (
            parts[-1].startswith("test_") and parts[-1].endswith(".py")):
        return f"{path} is a shared test helper or fixture"
    return ""


def changed_paths(worktree: Path, base: str = "main") -> list[str]:
    """What the branch changes against `base`, both sides of a rename, never the live bitácora."""
    done = subprocess.run(["git", "-C", str(worktree), "diff", "--name-only", "--no-renames", f"{base}...HEAD"],
                          capture_output=True, text=True, check=False)
    if done.returncode:
        raise RuntimeError(f"git diff {base}...HEAD failed: {done.stderr.strip()[:300]}")
    return [p for p in done.stdout.splitlines() if p and not p.startswith("bitacora/")]


def max_percent() -> int:
    try:
        import bt_config
        value = bt_config.get("integrate.selective_max_percent", DEFAULT_MAX_PERCENT)
    except Exception:  # noqa: BLE001 - outside a bitácora the default holds
        value = DEFAULT_MAX_PERCENT
    return value if isinstance(value, int) and not isinstance(value, bool) else DEFAULT_MAX_PERCENT


def _is_suite(path: str) -> bool:
    pure = PurePosixPath(path)
    return str(pure.parent) == TESTS and pure.name.startswith("test_") and pure.suffix == ".py"


def select(worktree: Path, changed: list[str] | None = None, *, base: str = "main", limit: int | None = None,
           graph: Graph | None = None, lazy_depth: int = LAZY_DEPTH) -> Selection:
    repo = Path(worktree)
    changed = changed_paths(repo, base) if changed is None else [p for p in changed if not p.startswith("bitacora/")]
    suites = sorted(p.stem for p in (repo / TESTS).glob("test_*.py"))
    result = Selection(changed=changed, total=len(suites))

    def add(suite: str, why: str) -> None:
        reasons = result.suites.setdefault(suite, [])
        if why not in reasons:
            reasons.append(why)

    for suite in suites:
        if suite in ALWAYS or ALWAYS_PATTERN.search(suite):
            add(suite, "always")
    reasons = [r for r in (_untrusted(p, repo, base) for p in changed) if r]
    if reasons:
        result.full = reasons[0] + (f" (+{len(reasons) - 1} more)" if len(reasons) > 1 else "")
        return result
    graph = graph or Graph(repo, extra=changed)
    targets = [p for p in changed if not (_is_suite(p) and (repo / p).is_file())]
    for path in changed:
        if _is_suite(path) and (repo / path).is_file():
            add(PurePosixPath(path).stem, "changed")
    reached: set[str] = set()
    for suite in suites:
        start = f"{TESTS}/{suite}.py"
        seen = graph.reach(start, lazy_depth)
        for target in targets:
            if target in seen and target != start:
                add(suite, f"{seen[target][1]} {_short(target)}{_via(_hops(seen, target))}")
                reached.add(target)
                continue
            for holder in seen:
                verb = graph.touches(holder, target, suite=holder == start)
                if verb:
                    add(suite, f"{verb.split()[0]} {_short(target)}{_via(_hops(seen, holder) + [target])}")
                    if verb != "scans *.py":            # a source scan proves nothing about who runs the module
                        reached.add(target)
                    break
    unreached = [p for p in targets if p not in reached and (repo / p).is_file()
                 and not (PurePosixPath(p).suffix in DOC_SUFFIXES and not p.startswith(RUNTIME_DOC_DIRS))]
    if unreached:
        result.full = (f"no suite reaches {unreached[0]} (a computed path or a deep lazy import)"
                       + (f" (+{len(unreached) - 1} more)" if len(unreached) > 1 else ""))
        return result
    cap = max_percent() if limit is None else limit
    if result.total and len(result.suites) * 100 > cap * result.total:
        result.full = f"{len(result.suites)} of {result.total} suites selected, more than {cap}%"
    return result


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args or len(args) > 2:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    selection = select(Path(args[0]), base=args[1] if len(args) > 1 else "main")
    print("\n".join(selection.describe()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
