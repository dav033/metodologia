"""The owner's «No funciona» on a subplan version, as a Solucionador trigger (`owner_rejected`).

Until 2026-10-31 a rejection in «Probar» (`bt_verification.decide`) recorded the decision and opened a P-item, and
nothing reacted: the owner had to find someone to reproduce it, ask the Planner for the repair and come back. Owner,
2026-10-31: «pues mete lo que me dijiste de que lo pase al solucionador y llena los huecos».

Each maintenance pass reads the verification ledger of every durable run (`<rdir>/.verification/decisions.json`): a
rejection of the subplan's current published version (state `rejected`) is one trigger, keyed by the subplan, the
version and commit the owner saw and his note (`bt_verification.rejection_key`), so it starts the Solucionador once;
a new note on the same version is a new rejection. It stays current while that rejection stands: an approval, a newer
published version (the repair landed) or another note makes it stale. The trigger carries what the panel offered the
owner (the SPEC `## Pruebas` rows and the pages they name) and the P-item; the brief adds how to reproduce it on that
exact commit (the version's copy, its test servers, the test accounts). The Solucionador reproduces it, records the
confirmed defect as run evidence and routes a bounded repair through the run's Planner (D-233); a change of scope or
criteria stays the owner's. Standard library plus the verification module.
"""
from __future__ import annotations

import json
from pathlib import Path

KIND = "owner_rejected"
PLAYWRIGHT = "/home/david/dev/pictures/node_modules/playwright"   # the machine's installed copy


def _ledger(rdir: Path) -> dict:
    try:
        data = json.loads((Path(rdir) / ".verification" / "decisions.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return {}
    return data.get("subplans") if isinstance(data, dict) and isinstance(data.get("subplans"), dict) else {}


def evidence_path(sid: str, version: object) -> str:
    """Where the Solucionador writes its reproduction, relative to the requirement: run evidence a bounded repair may
    cite (`stage freeze --repair-evidence`, D-241)."""
    return f"evidence/owner-rejected/{sid}-v{version}.md"


def triggers(run, rdir: Path) -> list[dict]:
    """One trigger per standing rejection of a subplan's current version. Cheap when nothing is rejected."""
    if not any(isinstance(d, dict) and d.get("decision") == "rejected" for d in _ledger(rdir).values()):
        return []
    import bt_verification as verification

    from .solver import trigger
    st = verification.state(rdir)
    if not st["applies"]:
        return []
    rows = verification.tests(rdir)
    out = []
    for row in st["subplans"]:
        if row["state"] != "rejected":
            continue
        sid, dec = row["id"], row["decision"]
        note = " ".join(str(dec.get("note") or "").split())
        item = trigger(KIND, verification.rejection_key(sid, dec), run.run_id,
                       reason=f"the owner tried {sid} version {row['version']} (commit {str(row['commit'])[:10]}) and "
                              f"rejected it: «{note[:300]}»")
        tests = verification.tests_for(rdir, sid, rows)
        item.update(subplan=sid, title=row["title"], version=row["version"], commit=row["commit"], note=note[:1000],
                    pending=str(dec.get("pending") or ""), decided_at=str(dec.get("at") or ""), via=str(dec.get("via") or ""),
                    tests=tests, pages=verification.test_paths(tests), evidence=evidence_path(sid, row["version"]))
        out.append(item)
    return out


def current(rdir: Path, item: dict) -> bool:
    """The rejection still stands on the version it was given for: not approved, not superseded by a newer version,
    not replaced by another note."""
    try:
        import bt_verification as verification
        row = next((r for r in verification.state(rdir)["subplans"] if r["id"] == item.get("subplan")), None)
    except Exception:  # noqa: BLE001 - unreadable now: kept for the next pass, never launched on a guess
        return False
    return bool(row) and row["state"] == "rejected" and verification.rejection_key(row["id"], row["decision"]) == item["key"]


def brief(item: dict, run, rdir: Path) -> list[str]:
    """The brief's section for an owner rejection: what he saw, where, and how to reproduce it on that exact commit."""
    import bt_verification as verification
    root = Path(rdir).parent.parent.parent
    sid, version, commit = item.get("subplan"), item.get("version"), str(item.get("commit") or "")
    scripts = Path(__file__).resolve().parent.parent
    cli = f"python3 {scripts / 'bitacora.py'} --project {run.project} verify"
    copy = verification.workdir(root, run.project, run.req, str(sid), str(version))
    record = (f"- the owner-visible record: {item.get('pending') or 'no P-item (the project has no PENDING.md)'} in "
              f"`{root / run.project / 'PENDING.md'}`; leave it open: his approval of a later version closes it")
    lines = ["", f"## The owner rejected {sid} version {version}", "",
             f"- subplan: {sid} — {item.get('title') or ''}",
             f"- version {version}, commit `{commit}` (the integrated tree at that subplan's boundary)",
             f"- decided {item.get('decided_at') or '?'} via {item.get('via') or '?'}; the owner's note:", "",
             *[f"  > {line}" for line in str(item.get("note") or "").splitlines() or [""]], "",
             record, "", "What the panel offered him (SPEC `## Pruebas`):", ""]
    for row in item.get("tests") or []:
        lines.append(f"- {row.get('where')}: {row.get('how')}" + (f" — expect: {row.get('expect')}" if row.get("expect") else ""))
    if not item.get("tests"):
        lines.append("- no row names this subplan")
    if item.get("pages"):
        lines += ["", "Pages it names: " + ", ".join(f"`{p}`" for p in item["pages"])]
    opened = (f"- the version's own copy (a detached worktree of `{commit[:10]}`, outside every repository): "
              f"`{cli} open {run.req} {sid}` → `{copy}`. Never edit it: it is the published version, and test servers "
              "never start on a copy with edits.")
    lines += ["", "### Reproduce it on that exact commit", "", opened,
              f"- `{cli} status {run.req}`: every subplan's state, version and commit"]
    try:
        import bt_verify_servers as servers
        data = servers.recipe(root, run.project, rdir)
    except Exception:  # noqa: BLE001 - the brief is still useful without the recipe
        servers, data = None, None
    if data is not None and servers is not None:
        planned = servers.planned(root, run.project, rdir, str(sid))
        login = servers.auto_login(data)
        accounts = servers.login_accounts(login)
        lines.append(f"- its test servers (`verify-servers.json`, the same «Probar» the owner used): `{cli} serve "
                     f"{run.req} {sid}` starts them clean from that commit and waits until they answer (prints the URL, "
                     f"about {planned.get('url') or 'the recipe ports'}); `{cli} stop-servers {run.req} {sid}` stops "
                     "them. Add `--login` to start it as in production (accounts and roles) instead of the local "
                     "administrator.")
        if accounts:
            who = ", ".join(a["email"] + (f" ({a['role']})" if a["role"] else "") for a in accounts)
            lines.append(f"- test accounts: {who}; default {login.get('default') or accounts[0]['email']}. "
                         f"`{cli} storage-state {run.req} {sid} --account <email> --out <file>` writes a Playwright "
                         "storage state (0600) signed in as that account on the running version: "
                         "`browser.newContext({storageState: '<file>'})`. Never print the token.")
    else:
        lines.append("- the project has no test-server recipe (`verify-servers.json`): follow the `## Pruebas` row by "
                     "hand in the version's copy")
    evidence = Path(rdir) / str(item.get("evidence") or "")
    lines += [(f"- a browser: Playwright is installed at `{PLAYWRIGHT}` (`node -e` with `require('{PLAYWRIGHT}')`, "
               "chromium headless); take screenshots into your session folder"),
              "", "### Then", "",
              (f"- confirmed: write the reproduction (steps, what you saw against what the row expects, screenshot and "
               f"log paths, the commit) to `{evidence}`, naming the {sid} task the repair must come before; route the "
               "bounded repair through the Planner (agents/solver.md, known case «the owner rejected a subplan "
               "version»)"),
              "- not reproduced: `asked_owner`, with what you tried in `question` (the owner's note stays open)",
              f"- trigger key for `handled`: `{item['key']}`"]
    return lines


__all__ = ["KIND", "brief", "current", "evidence_path", "triggers"]
