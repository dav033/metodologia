"""Compare native and RTK output on Git and an isolated pytest fixture."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import sys
import time

import tiktoken

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skill" / "scripts"))
import install_rtk


def execute(argv, cwd, output_dir, stem, environment, tokenizer):
    started = time.perf_counter()
    result = subprocess.run(argv, cwd=cwd, env=environment, capture_output=True, timeout=45)
    elapsed = (time.perf_counter() - started) * 1000
    output = result.stdout + result.stderr
    path = output_dir / f"{stem}.txt"
    path.write_bytes(output)
    text = output.decode("utf-8", errors="replace")
    return {"argv": argv, "cwd": str(cwd), "exit_code": result.returncode,
            "bytes": len(output), "tokens": len(tokenizer.encode(text)),
            "elapsed_ms": elapsed, "output_file": path.name}


def make_fixture(path):
    (path / "test_pass.py").write_text(
        "import pytest\n\n@pytest.mark.parametrize('value', range(300))\n"
        "def test_round_trip(value):\n    assert int(str(value)) == value\n")
    (path / "test_fail.py").write_text(
        'def test_touching_intervals():\n'
        '    assert True is False, "E_OVERLAP: touching endpoints must not overlap"\n\n'
        'def test_cross_tenant_admin():\n'
        '    raise PermissionError("E_TENANT_DENIED: tenant_b must be inaccessible")\n\n'
        'def test_expired_token():\n'
        '    raise ValueError("E_TOKEN_EXPIRED: session is not valid")\n')
    (path / "conftest.py").write_text(
        "from pathlib import Path\n\n"
        "def pytest_sessionfinish(session, exitstatus):\n"
        "    with (Path(__file__).parent / 'executions.log').open('a') as f:\n"
        "        f.write(f'{exitstatus}\\n')\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New or empty results directory; existing evidence is preserved")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1],
                        help="Git repository used for read-only inspection")
    parser.add_argument("--rtk", default=shutil.which("rtk") or "rtk", help="RTK executable")
    args = parser.parse_args()
    if not Path(args.rtk).is_file() and shutil.which(args.rtk) is None:
        parser.error("RTK not found; install the pinned binary with python install.py --rtk-only")
    if shutil.which("pytest") is None:
        parser.error("pytest not found; use the README uv run command")
    executable = Path(args.rtk) if Path(args.rtk).is_file() else Path(shutil.which(args.rtk))
    rtk_version = subprocess.run([str(executable), "--version"], capture_output=True,
                                 timeout=10, check=True).stdout.decode().strip()
    rtk_binary_sha256 = hashlib.sha256(executable.read_bytes()).hexdigest()
    pinned_release_match = (rtk_version == f"rtk {install_rtk.VERSION}"
                            and rtk_binary_sha256 == install_rtk.BINARY_SHA256)
    if rtk_version == f"rtk {install_rtk.VERSION}" and not pinned_release_match:
        parser.error("RTK version matches the pinned release but binary SHA-256 differs")
    args.output.mkdir(parents=True, exist_ok=True)
    output_dir = args.output.resolve()
    if any(output_dir.iterdir()):
        parser.error("output directory must be empty; existing benchmark evidence is preserved")
    fixture_root = output_dir / "fixture"
    fixture_root.mkdir()
    make_fixture(fixture_root)
    tokenizer = tiktoken.get_encoding("o200k_base")
    environment = os.environ | {
        "RTK_TELEMETRY_DISABLED": "1", "NO_COLOR": "1", "COLUMNS": "100",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "XDG_CONFIG_HOME": str(output_dir / "xdg-config"),
        "XDG_DATA_HOME": str(output_dir / "xdg-data"),
        "XDG_CACHE_HOME": str(output_dir / "xdg-cache"),
    }
    cases = [
        ("git-status", ["git", "status"], [args.rtk, "git", "status"], args.repo, 0),
        ("git-diff", ["git", "diff", "--", "skill/SKILL.md"],
         [args.rtk, "git", "diff", "--", "skill/SKILL.md"], args.repo, 0),
        ("git-log", ["git", "log", "-n", "20"], [args.rtk, "git", "log", "-n", "20"], args.repo, 0),
        ("pytest-pass", ["pytest", "-vv", "--color=no", "test_pass.py"],
         [args.rtk, "pytest", "-vv", "--color=no", "test_pass.py"], fixture_root, 0),
        ("pytest-fail", ["pytest", "-vv", "--color=no", "."],
         [args.rtk, "pytest", "-vv", "--color=no", "."], fixture_root, 1),
        ("pytest-fail-quiet", ["pytest", "-q", "--color=no", "."],
         [args.rtk, "pytest", "-q", "--color=no", "."], fixture_root, 1),
    ]
    runs = []
    for repeat in range(3):
        for name, native, wrapped, cwd, status in cases:
            order = [("native", native), ("rtk", wrapped)]
            if repeat % 2:
                order.reverse()
            for variant, argv in order:
                data = execute(argv, cwd, output_dir, f"{name}-{repeat}-{variant}", environment, tokenizer)
                data.update(case=name, repeat=repeat, variant=variant, expected_exit=status)
                data["exit_preserved"] = data["exit_code"] == status
                text = (output_dir / data["output_file"]).read_text()
                if name.startswith("pytest-fail"):
                    required = ["test_touching_intervals", "test_cross_tenant_admin", "test_expired_token",
                                "E_OVERLAP", "E_TENANT_DENIED", "E_TOKEN_EXPIRED"]
                    data["diagnostics"] = {marker: marker in text for marker in required}
                runs.append(data)
    summary = []
    for name, *_ in cases:
        item = {"case": name}
        for variant in ("native", "rtk"):
            group = [r for r in runs if r["case"] == name and r["variant"] == variant]
            item[variant] = {key: statistics.median(r[key] for r in group)
                             for key in ("tokens", "bytes", "elapsed_ms")}
        item["output_token_reduction_pct"] = 100 * (1 - item["rtk"]["tokens"] / item["native"]["tokens"])
        summary.append(item)
    recovery = {"attempted": False}
    for run in runs:
        if run["variant"] != "rtk":
            continue
        text = (output_dir / run["output_file"]).read_text()
        match = re.search(r"rtk recall(?: --[\w-]+)* ([a-f0-9]{6,64})", text)
        if match:
            before = (fixture_root / "executions.log").read_bytes()
            recalled = execute([str(executable), "recall", "--full", match[1]], fixture_root,
                               output_dir, "recall-full", environment, tokenizer)
            after = (fixture_root / "executions.log").read_bytes()
            recovery = {"attempted": True, "source_case": run["case"], "result": recalled,
                        "exit_code_zero": recalled["exit_code"] == 0,
                        "did_not_rerun_pytest": before == after}
            recovered = (output_dir / recalled["output_file"]).read_text()
            required = ["test_touching_intervals", "test_cross_tenant_admin", "test_expired_token",
                        "E_OVERLAP", "E_TENANT_DENIED", "E_TOKEN_EXPIRED", "300 passed", "3 failed"]
            recovery["diagnostics"] = {marker: marker in recovered for marker in required}
            recovery["diagnostics_all_preserved"] = all(recovery["diagnostics"].values())
            break
    result = {"rtk_version": rtk_version, "rtk_binary_sha256": rtk_binary_sha256,
              "pinned_release_match": pinned_release_match,
              "pinned_archive_sha256": install_rtk.ARCHIVE_SHA256,
              "tokenizer": "tiktoken o200k_base", "scope": "combined command stdout/stderr only",
              "repeats": 3, "fixture_executions": len((fixture_root / "executions.log").read_text().splitlines()),
              "runs": runs, "summary": summary, "recovery": recovery,
              "exit_codes_all_preserved": all(r["exit_preserved"] for r in runs),
              "diagnostics_all_preserved": all(all(r.get("diagnostics", {}).values()) for r in runs)}
    (output_dir / "metrics.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({"summary": summary, "recovery": recovery,
                      "pinned_release_match": pinned_release_match,
                      "fixture_executions": result["fixture_executions"],
                      "exit_codes_all_preserved": result["exit_codes_all_preserved"],
                      "diagnostics_all_preserved": result["diagnostics_all_preserved"]}, indent=2))
    if not result["exit_codes_all_preserved"] or not result["diagnostics_all_preserved"] \
            or not recovery.get("did_not_rerun_pytest", False) \
            or not recovery.get("exit_code_zero", False) \
            or not recovery.get("diagnostics_all_preserved", False):
        raise SystemExit("Benchmark invariant failed; inspect metrics.json and saved command outputs")


if __name__ == "__main__":
    main()
