#!/usr/bin/env python3
"""Add milestone M6 «Production environment» (T20-T24) to REQ-027, as the next plan revision.

Owner decision 2026-10-19: besides shipping, the plan must CREATE the production environment (AdvIn service user,
directories, units and Caddy block; Vercel project; GitHub OAuth App and Telegram bot prerequisites; generated keys)
and verify it live. Until now the plan kept all of that outside the Scheduler («Go-live with the owner»).

    python3 add_production_milestone.py <requirement dir> [--apply]

Without --apply it only reports what it would change. With --apply it edits SPEC.md, PLAN.md and PLAN.json of that
directory (idempotent: nothing happens when M6 already exists) and sets PLAN.json to the next revision; freezing it
(`plan-json freeze`) and rebasing the run (`scheduler-op REQ-027 revise`) stay separate steps, because a revise
cancels live attempts: do it when none is running.
"""
from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

GATEWAY_HOST = "flow-api.185-147-157-25.sslip.io"
RULES = (
    "Rules for every M6 task (owner decision D-078, 2026-10-19: agents ship to production): "
    "(1) Never print, log, commit or pass a secret in argv: read secrets from the owner's file "
    "`~/.config/flow/secrets.env` (mode 600, outside any repo) and move them over ssh stdin or `vercel env add` stdin. "
    "(2) AdvIn also serves other production sites behind the same Caddy: before touching it snapshot the status and TLS "
    "subject of every host, back up what you change (timestamped copy), validate before reload, and if any other host "
    "answers differently afterwards restore the backup at once and fail the task. "
    "(3) Write a receipt `remote/deploy/receipts/<name>.json` (steps with redacted commands and exit codes, named checks "
    "with ok/detail, the git sha you deployed) that `remote/deploy/verify_receipt.py` can validate offline: the "
    "verifier has no network, so the receipt is the evidence. "
    "(4) If something only the owner can supply is missing or a site asks for 2FA, sudo mode, a captcha or a "
    "Cloudflare challenge, stop at once and say exactly which: do not improvise, invent a secret or retry."
)

REQUIREMENT = (
    "- R19. The production environment shall exist and be verified: the gateway and the Telegram bot run as systemd "
    "services of a dedicated no-login user on AdvIn behind the existing Caddy and listen only on the Docker bridge; "
    "the frontend is deployed to a Vercel production project; the GitHub OAuth App and the Telegram bot are configured; "
    "a rollback has been rehearsed; and every other site behind the same Caddy answers exactly as before."
)

MILESTONE = {
    "id": "M6",
    "title": "Production environment",
    "acceptance_criteria": [
        "The AdvIn services, the Caddy block, the Vercel project, the OAuth App and the Telegram bot exist and work together",
        "Every other site behind the AdvIn Caddy answers as before and a rollback has been rehearsed",
    ],
}


def evidence(j: dict, command: str, task: str = "T16") -> dict:
    """Typed evidence for the six dimensions; `j` argues each one for THIS task (shared wording is a planner warning)."""
    return {
        "complexity": {"evidence": [command], "justification": j["complexity"]},
        "scope": {"evidence": ["spec:SPEC.md"], "justification": j["scope"]},
        "duration": {"evidence": [f"task:{task}"], "justification": j["duration"]},
        "risk": {"evidence": ["command:ssh advin docker ps -> caddy serves maros, lotm and training hosts"],
                 "justification": j["risk"]},
        "coupling": {"evidence": [f"task:{task}"], "justification": j["coupling"]},
        "confidence": {"evidence": ["command:ssh advin ss -ltnp -> python on 172.20.0.1:8100"],
                       "justification": j["confidence"]},
    }


def verify(name: str, check: str, purpose: str, category: str) -> dict:
    return {"type": "command", "value": f"cd remote/deploy && python verify_receipt.py {name} --check {check}",
            "purpose": purpose, "category": category}


def task(tid, title, objective, after, complexity, scope, minutes, covers, paths, criteria, checks, rationale,
         evidence_block, resources):
    return {
        "id": tid, "milestone_id": "M6", "title": title, "objective": f"{objective} {RULES}", "repository": "skill",
        "after": after, "complexity": complexity, "scope": scope, "estimated_minutes": minutes, "risk": "high",
        "coupling": "high" if resources else "medium", "confidence": "medium", "estimate_rationale": rationale,
        "classification_evidence": evidence_block, "expected_paths": paths, "shared_resources": resources,
        "acceptance_criteria": [c for c, *_ in criteria],
        "verification": [item for item in checks], "covers": covers, "kind": "implement",
    }


def build_tasks() -> list[dict]:
    tasks = []

    c = [("A pre-change snapshot of every existing Caddy host (status, TLS subject, first-byte time) is recorded",),
         ("A no-login service user, release/state/env directories and both systemd units exist and pass systemd-analyze verify",),
         ("The Caddyfile was backed up, validated, reloaded and every pre-existing host answers as in the snapshot",),
         ("A rollback that restores the Caddyfile backup and removes the units was rehearsed and left AdvIn as before",),
         ("The receipt verifier rejects failed checks, missing steps, secret-looking values and a git sha that is not an ancestor of HEAD",)]
    v = [verify("advin-provision", "snapshot-before", c[0][0], "functional"),
         verify("advin-provision", "service-layout", c[1][0], "functional"),
         verify("advin-provision", "other-hosts-unchanged", c[2][0], "integration"),
         verify("advin-provision", "rollback-rehearsed", c[3][0], "integration"),
         {"type": "command", "value": "cd remote/deploy && python -m unittest discover -s tests -p test_receipts.py",
          "purpose": c[4][0], "category": "functional"}]
    tasks.append(task(
        "T20", "Create the AdvIn production environment: service user, directories, units and Caddy block",
        f"AdvIn gets a no-login service user `flow`, /opt/flow-gateway (releases, current), /var/lib/flow-gateway (SQLite) "
        f"and /etc/flow-gateway/env (mode 600, skeleton without values), the gateway and bot systemd units installed "
        f"and hardened (NoNewPrivileges, PrivateTmp, ProtectSystem=strict, bind only 172.20.0.1 on a free port you "
        f"record), and the Caddy block for {GATEWAY_HOST} (reverse_proxy to 172.20.0.1:<port> with SSE flush) added to "
        f"/opt/edge-proxy/Caddyfile and reloaded in the `caddy` container. Create `remote/deploy/verify_receipt.py` and "
        f"its tests first; the units stay stopped until T23.",
        ["T19"], "high", "large_change", 90, ["R16", "R3", "R19"],
        ["remote/deploy/**", "remote/docs/runbook.md"], c, v,
        "Files, a verifier and one reversible change on a shared host",
        evidence({"complexity": "Caddyfile edit and systemd units on a host shared with other production sites, plus a receipt verifier",
         "scope": "Scripts, a verifier with tests and one reversible host change",
         "duration": "A verifier, several scripts and one live rehearsal, longer than the offline kit of T16",
         "risk": "The provisioning reloads the Caddy that serves maros, lotm and training: a mistake takes those sites down",
         "coupling": "Every later production task needs the user, directories, units and Caddy block this task creates",
         "confidence": "Host services on 172.20.0.1 already sit behind this Caddy, so the pattern is proven"}, "command:ssh advin docker ps -> caddy container publishes 80/443"),
        ["advin-host"]))

    c = [("The Vercel project flow-remote exists in dav033s-projects with root remote/web and nothing from .vercel is committed",),
         ("Only non-secret environment variables are set; their names are recorded without values",),
         ("A production deployment is Ready and its URL, deployment id and git sha are recorded",),
         ("The deployed app's same-origin rewrite reaches the AdvIn Caddy and not an app 404",)]
    v = [verify("vercel-frontend", "project-linked", c[0][0], "functional"),
         verify("vercel-frontend", "env-names", c[1][0], "static"),
         verify("vercel-frontend", "deployment-ready", c[2][0], "integration"),
         verify("vercel-frontend", "rewrite-reaches-caddy", c[3][0], "integration")]
    tasks.append(task(
        "T21", "Create the Vercel project and deploy the frontend to production",
        f"Create the Vercel project `flow-remote` in team dav033s-projects (root directory remote/web, Next.js 15) with "
        f"the CLI, set only the non-secret `GATEWAY_ORIGIN=https://{GATEWAY_HOST}`, deploy to production with "
        f"`vercel --prod`, and record the *.vercel.app URL, deployment id and git sha. The gateway is not running yet, "
        f"so the rewrite must reach AdvIn's Caddy (a 502 or a gateway answer carrying Caddy's server header), never "
        f"the app's own 404. Do not commit `.vercel/`.",
        ["T20"], "medium", "small_change", 60, ["R16", "R19"], ["remote/deploy/**"], c, v,
        "One CLI project and one deploy; the rewrite check needs the live host",
        evidence({"complexity": "One Vercel project and one deploy of an app that already builds",
         "scope": "CLI calls and a receipt; no application code changes",
         "duration": "Project creation, environment variable and one production build",
         "risk": "A Vercel deploy is reversible and touches no other site, but it exposes the app publicly",
         "coupling": "Needs the gateway host from T20 and gives T22 the URL for the OAuth homepage",
         "confidence": "vercel whoami works and the scope dav033s-projects is known"}, "command:vercel whoami -> dav033"),
        ["vercel-project"]))

    c = [("The GitHub OAuth App flow-remote exists with the Vercel URL as homepage and the gateway callback; its client id is recorded by name only",),
         ("The Telegram bot token and the owner's chat id came from the owner's secrets file and were verified with getMe and getChat",),
         ("FLOW_GATEWAY_KEY and SESSION_SECRET were generated on the target and never printed",),
         ("Secrets exist only in mode-600 files on AdvIn and the laptop and in Vercel env, and a scan of the tree and the last 50 commits finds none",)]
    v = [verify("identity", "oauth-app", c[0][0], "functional"),
         verify("identity", "telegram", c[1][0], "functional"),
         verify("identity", "generated-keys", c[2][0], "functional"),
         verify("identity", "secrets-placement", c[3][0], "regression")]
    tasks.append(task(
        "T22", "Create the identity and messaging prerequisites and place the secrets",
        "Create the GitHub OAuth App `flow-remote` (homepage = the Vercel URL from T21, callback = the gateway host) in "
        "the agents' Firefox (BiDi on 127.0.0.1:9223, Xephyr) if a GitHub session is there. The Telegram bot is created "
        "by the owner in @BotFather: read TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from `~/.config/flow/secrets.env`, "
        "verify them with getMe/getChat and never create a bot yourself. Generate FLOW_GATEWAY_KEY (48 bytes) and "
        "SESSION_SECRET with `openssl rand` on the target, write /etc/flow-gateway/env on AdvIn and "
        "`~/.config/bitacora/remote.env` on the laptop (mode 600) and set the secret Vercel env vars via stdin. Never "
        "touch GitHub account settings other than that OAuth App.",
        ["T21"], "medium", "small_change", 60, ["R16", "R1", "R19"], ["remote/deploy/**"], c, v,
        "Browser automation of one form plus secret placement; prerequisites only the owner can supply may stop it",
        evidence({"complexity": "Browser automation of one GitHub form plus secret placement across three stores",
         "scope": "One OAuth App, two bot values read from the owner's file and generated keys",
         "duration": "Form filling and key placement, with stops for anything only the owner can do",
         "risk": "Secrets are involved: a leak into git, logs or argv is the failure to prevent",
         "coupling": "The OAuth callback and the Vercel URL must match what T21 and T23 use",
         "confidence": "The agents' Firefox keeps GitHub sessions but 2FA or sudo mode may interrupt"}, "command:ssh advin ss -ltnp -> python on 172.20.0.1:8100"),
        ["advin-host"]))

    c = [("A release for the exact HEAD sha is on AdvIn, dependencies come from the hash-locked file, the database is migrated, current switched atomically and both services are enabled and active",),
         ("The gateway listens only on 172.20.0.1 and AdvIn's port 8765 now exposes only /api/remote/v1 of the laptop, not the whole panel",),
         ("The public health URL answers 200 with the release sha, an unauthenticated API call answers 401 and the security headers are present",),
         ("Rollback to the previous release and forward again were rehearsed with health 200 each time",),
         ("Every pre-existing AdvIn host still answers as in the snapshot",)]
    v = [verify("gateway-release", "release-active", c[0][0], "integration"),
         verify("gateway-release", "listeners-and-tunnel", c[1][0], "integration"),
         verify("gateway-release", "public-health", c[2][0], "integration"),
         verify("gateway-release", "rollback-rehearsed", c[3][0], "integration"),
         verify("gateway-release", "other-hosts-unchanged", c[4][0], "regression")]
    tasks.append(task(
        "T23", "Release the gateway and the Telegram bot to AdvIn and switch them on",
        "Build a release from the exact HEAD sha (git archive), upload it to /opt/flow-gateway/releases/<sha>, create a "
        "venv and install from the hash-locked requirements (no unpinned installs), migrate the SQLite database, "
        "switch `current` atomically, enable and start the gateway and bot units, and keep the previous release (for the "
        "first deploy rehearse with a copy). Replace the laptop's whole-panel reverse tunnel unit with the retargeted "
        "remote-only one (back up the old unit; the local panel and its tests stay unchanged, R18) so AdvIn can no longer "
        "reach anything but /api/remote/v1. Write `remote/deploy/smoke.py` for T24.",
        ["T22"], "high", "large_change", 120, ["R3", "R16", "R17", "R19"],
        ["remote/deploy/**", "remote/docs/runbook.md"], c, v,
        "A live release, a tunnel change on the laptop and a rehearsed rollback",
        evidence({"complexity": "A live release, a database migration, an atomic switch and a laptop tunnel retarget with rehearsed rollback",
         "scope": "Release scripts, a smoke script and changes on two machines",
         "duration": "The longest step: build, upload, install, migrate, switch and rehearse the rollback",
         "risk": "It starts the gateway on the production host and replaces the tunnel that currently exposes the whole panel",
         "coupling": "Uses the secrets of T22 and gives T24 a running service",
         "confidence": "Releases with a current symlink and a systemd unit are an established pattern on this host"}, "command:ssh advin ss -ltnp -> python on 172.20.0.1:8100"),
        ["advin-host"]))

    c = [("Sign-in start redirects to github.com with the OAuth App's client id, a state and the gateway callback, and the cookies carry Secure, HttpOnly and SameSite=Strict",),
         ("A callback with a bad state is refused, an unauthenticated API call is 401 and a state-changing call without X-Flow-Request is refused",),
         ("Through the Vercel URL the page loads and the event stream connects and reconnects with Last-Event-ID",),
         ("One Telegram test message was accepted by the Bot API for the owner's chat",)]
    v = [verify("live-smoke", "signin-start", c[0][0], "integration"),
         verify("live-smoke", "negative-paths", c[1][0], "integration"),
         verify("live-smoke", "sse", c[2][0], "integration"),
         verify("live-smoke", "telegram-delivery", c[3][0], "integration")]
    manual_purpose = "David signs in with GitHub on his phone, sees the runs list at 360 px, and a foreign GitHub account is refused"
    c.append((manual_purpose,))
    v.append({"type": "manual", "value": "Open the Vercel URL on the phone, sign in as dav033, look at the runs list; try another GitHub account",
              "purpose": manual_purpose, "expected": "The owner confirms sign-in works, the list renders at 360 px and a foreign account is refused",
              "category": "product"})
    t = task(
        "T24", "Live smoke test of the production environment and handover",
        "Run `remote/deploy/smoke.py --live` against the real Vercel URL and the gateway host and record every named "
        "check in the receipt `live-smoke`; send exactly one Telegram test message to the owner. Report the URLs, the "
        "release sha, how to roll back (`remote/docs/runbook.md`) and what remains manual. Do not change code in this task.",
        ["T23"], "medium", "small_change", 60, ["R1", "R2", "R10", "R19"], ["remote/deploy/receipts/**"], c, v,
        "A scripted live run plus one human confirmation",
        evidence({"complexity": "A scripted live run of known checks plus one human confirmation",
         "scope": "Running a smoke script and recording a receipt, no code changes",
         "duration": "Minutes of checks plus the owner's phone test",
         "risk": "It sends one real Telegram message and probes the public sign-in, nothing destructive",
         "coupling": "Depends on every previous M6 task being live",
         "confidence": "The checks mirror the loopback end-to-end of T17"}, "command:ssh advin docker ps -> caddy container publishes 80/443", "T17"),
        ["advin-host"])
    t["kind"] = "test"
    tasks.append(t)
    return tasks


def apply(rdir: Path, write: bool) -> list[str]:
    spec_path, md_path, json_path = rdir / "SPEC.md", rdir / "PLAN.md", rdir / "PLAN.json"
    plan = json.loads(json_path.read_text(encoding="utf-8"))
    if any(m.get("id") == "M6" for m in plan["milestones"]):
        return ["M6 already exists: nothing to do"]
    out = []
    spec = spec_path.read_text(encoding="utf-8")
    if "- R19." not in spec:
        spec = spec.replace("- R18. The local panel", REQUIREMENT + "\n- R18. The local panel", 1) if False else \
            re.sub(r"(- R18\. [^\n]*(?:\n  [^\n]*)*)", lambda m: m.group(1) + "\n" + REQUIREMENT, spec, count=1)
        spec = spec.replace("Must: R1–R12, R14, R16–R18", "Must: R1–R12, R14, R16–R19", 1)
        out.append("SPEC.md: R19 added")
    plan["requirements"] = sorted({*plan["requirements"], "R19"}, key=lambda r: int(r[1:]))
    plan["milestones"].append(MILESTONE)
    new = build_tasks()
    plan["tasks"].extend(new)
    revisions = sorted((rdir / "plan-revisions").glob("PLAN.r*.json"))
    last = max((int(re.search(r"r(\d+)", p.name).group(1)) for p in revisions), default=plan["revision"])
    plan["revision"] = last + 1
    out.append(f"PLAN.json: milestone M6, tasks {', '.join(t['id'] for t in new)}, revision {plan['revision']}")

    md = md_path.read_text(encoding="utf-8")
    lines = ["", "### M6 — Production environment"]
    for t in new:
        verify_cmd = next((v["value"] for v in t["verification"] if v["type"] == "command"), "")
        lines.append(f"- [ ] {t['id']} — {t['title']} · repo: skill · files: {', '.join(t['expected_paths'])} · "
                     f"after: {', '.join(t['after'])} · verify: `{verify_cmd}` · covers: {', '.join(t['covers'])} · "
                     f"kind: {t['kind']}")
    marker = "\n## Go-live with the owner"
    assert marker in md, "PLAN.md layout changed: «Go-live with the owner» section not found"
    md = md.replace(marker, "\n".join(lines) + "\n" + marker, 1)
    md = md.replace("- Tasks never edit `bitacora/`, never merge to `main`, never deploy, never ssh to AdvIn: notes go to `remote/docs/`.",
                    "- T1-T19 never edit `bitacora/`, never merge to `main`, never deploy, never ssh to AdvIn: notes go to `remote/docs/`. "
                    "M6 (T20-T24) may ssh to AdvIn and deploy to Vercel, only as its criteria describe (owner decision 2026-10-19, D-078).", 1)
    md = md.replace("## Go-live with the owner (after the run; not scheduler tasks)",
                    "## Go-live with the owner (superseded by milestone M6 where noted)\n"
                    "_Steps 2-5 are now tasks T20-T24; steps 1 and 6 (merge to `main`, copy the notes) stay with the owner._", 1)
    out.append("PLAN.md: M6 section, constraint amended")
    if write:
        spec_path.write_text(spec, encoding="utf-8")
        md_path.write_text(md, encoding="utf-8")
        json_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        raise SystemExit(__doc__)
    for line in apply(Path(args[0]), "--apply" in sys.argv):
        print(line)
