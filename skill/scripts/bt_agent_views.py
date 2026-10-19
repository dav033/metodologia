"""Prompt-facing rendering of the agent catalog."""
import bt_profiles
from bt_agent_models import LADDER


def brief(project: str | None = None) -> str:
    """Compact markdown of the catalog for prompts and `bitacora.py context`."""
    from bt_agents import catalog, account_key

    cat = catalog(project)
    lines = ["### Agents available (any session may delegate to any of them)",
             "| model | provider | tier | use it for |", "|---|---|---|---|"]
    tiers = {}
    for provider, rungs in LADDER.items():
        for i, (m, e) in enumerate(rungs):
            tiers.setdefault(m, []).append(f"{i}{'·' + e if e else ''}")
    for m in cat["models"]:
        lines.append(f"| `{m['id']}` ({m['label']}) | {m['provider']} | {', '.join(tiers.get(m['id'], []))} | {m['use']} |")
    acc = []
    for a in cat["accounts"]:
        if a["profile"] in bt_profiles.DEFAULTS and any(
                account_key(a["profile"]) == account_key(b["profile"]) for b in cat["accounts"] if b is not a):
            continue
        flags = [f for f, on in (("work projects only", a["work_only"]), ("NOT allowed for this project", a["allowed_here"] is False),
                                 (f"usage limit until {a['cooling_until']}", a["cooling_until"]),
                                 ("CLI missing", not a["installed"])) if on]
        acc.append(f"`{a['profile']}` ({a['provider']}{'; ' + '; '.join(flags) if flags else ''})")
    lines.append("Accounts: " + ", ".join(acc) + ".")
    lines += ["Approved automatic role routes (D-070; quota selects the family):", "| role | approved configurations |", "|---|---|"]
    for role, choices in cat["roles"].items():
        lines.append(f"| {role} | " + " / ".join(f"{model} {effort}" for _, model, effort in choices) + " |")
    lines.append("Use delegate --role ROLE for quota-family balancing; --complexity L selects approved complex-task "
                 "alternatives. Failures/risk alone do not change these configurations. Audit provider independence "
                 "is preserved; documentation-only work and explicit pins retain their separate budgets.")
    return "\n".join(lines)
