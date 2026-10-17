"""Run the two additionally requested small models after the original pool.

Accounts match the original experiment. Model calls on the same account never
overlap within this experiment; inputs and oracle remain unchanged.
"""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import run

ROOT = Path(__file__).resolve().parent
cases = json.loads((ROOT / "cases.json").read_text())
routes = [("claude-work", "claude", "claude-haiku-5-5", "claude-work-haiku55"),
          ("codex-2", "codex", "gpt-6-luna", "codex-2-luna")]
run.save(ROOT / "additional-protocol-corrected.json", {
    "schema_version": 1, "scope": "Owner-requested extension of the same synthetic reviewer pilot",
    "additional_calls": 10, "total_planned_calls": 25, "effort": "max", "routes": routes,
    "oracle_sha256": hashlib.sha256((ROOT / "cases.json").read_bytes()).hexdigest(),
    "instruction_sha256": hashlib.sha256(run.INSTRUCTION.encode()).hexdigest(),
    "account_isolation": "Run only after all 15 original calls; Haiku shares Claude Work, Luna shares Codex-2",
    "capability_evidence": "Local Codex-2 models_cache advertises max for gpt-6-luna. Official Claude Haiku 5.5 effort documentation supports max. The haiku alias returned Sonnet and was excluded; use full model ID and stop on metadata mismatch.",
    "comparison": "Original models remain at high; the two added models are requested at max, per owner instruction. This is a comparison of the requested routes, not an equal-effort model experiment."
})
missing = [f"{c['id']}-{p}.json" for c in cases for p, _, _ in run.ROUTES
           if not (ROOT / f"{c['id']}-{p}.json").exists()]
if missing:
    raise SystemExit("Original run incomplete: " + ", ".join(missing))
for case in cases:
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda route: run.run_one(case, route[:3], "max", route[3]), routes))
    haiku = json.loads((ROOT / f"{case['id']}-claude-work-haiku55.json").read_text())
    if haiku.get("observed_models") != ["claude-haiku-5-5"]:
        raise SystemExit("Haiku effective model not confirmed; stop rather than silently compare another model")
    print(f"ADDITIONAL CASE COMPLETE {case['id']}", flush=True)
