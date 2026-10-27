"""Zero-context Designer brief generation, separate from draft state and lifecycle."""
from pathlib import Path


def _brief(project: str, rdir: Path, row: dict, feedback: list[dict], *, fresh: bool = False,
           behavior: Path | None = None) -> str:
    import bt_design_ui_brief as ui_brief
    from bt_design_drafts import KIT, SKILL_ROOT, paths
    md, html = paths(rdir, row["ref"])
    cloned = ui_brief.cloned_repos(project)
    repos = "\n".join(f"  - {role}: {path}" for role, path in cloned.items()) or "  - (none cloned on this machine)"
    source = (f"The UI brief for this subplan is {behavior}: read it first; it is your scope." if behavior else
              "The UI brief for this subplan (your scope):\n\n" + ui_brief.build(rdir, row, cloned))
    previous = ("A previous draft exists at those paths: revise it, keeping everything the feedback and the plan "
                "changes do not touch." if md.is_file() else "There is no previous draft.")
    if fresh:
        previous = ("FRESH START: compose from requirements and unresolved owner feedback. Do not patch or copy the "
                    "previous draft. Previous revisions in history/ are immutable. Keep the behavioural requirements.")
    asks = "\n".join(f"  - ({f['when'][:16]}) direction={f.get('direction') or 'all'}: {f['text']}" for f in feedback) or "  - none"
    return f"""Planning-time UI/UX design for subplan {row['id']} — {row['title']}.

The owner and the Planner are still discussing this plan. Design the best version for the plan as it stands now;
record open decisions as questions in the contract instead of stopping. This draft becomes the approved contract
`{row['ref']}` when the owner approves the plan.

{source}

For context only: {Path(rdir) / 'SPEC.md'}, {Path(rdir) / 'PLAN.md'} and {Path(rdir) / 'PLAN.json'} (subplan
{row['id']}). Engineering-only tasks, checks and paths there are not design scope. Project repositories, read-only,
for the existing product surface, design system, tokens and components:
{repos}

The mockup is a CHANGE to an existing product surface, never a new page or landing: reproduce the existing
shell/navigation/header and change only what the requirements demand. Locate the current screens in the
repositories above (or use the ones the UI brief names) and base the mockup on them.
The project's design system is FIXED: read the repository's globals.css / token files / theme and its components,
and use exactly those tokens, font families and components. Do not propose a new palette, new font families or a
new brand/identity. Variation is allowed only in composition, hierarchy, density, component arrangement and motion
within that system. If the repository has no token source, say so in CONCERNS and use the kit's existing defaults.
No invented content: no invented names, dates, slogans, headlines or marketing copy. Use copy from the requirements
and the existing UI; mock data is neutral, realistic, clearly mock and limited to what the flows need.

Before building the mockup read {SKILL_ROOT / 'agents/designer/skills/david-ui-kit/SKILL.md'} and
{SKILL_ROOT / 'agents/designer/references/mockup-craft.md'} and follow them. Use the REAL installed libraries first;
the components may be recomposed to serve the flows, inside the project's design system. Build an entry TSX with
mountMockup/useMockup from {KIT.parent / 'real/runtime/mockup.tsx'} (reference:
{KIT.parent / 'real/reference/acceso.tsx'}).
The toolchain lives outside git; run the tools by absolute path (builder and audit work offline):
  python3 {SKILL_ROOT / 'scripts/bitacora.py'} components mockup build ENTRY.tsx --out {html}
  python3 {KIT / 'contrast.py'} {html}
  UV_OFFLINE=1 uv run --offline --with playwright python {KIT / 'audit_mockup.py'} {html}
Do not install packages or fetch assets. Fallback HTML snippets are allowed only if the real builder is unavailable;
report why in CONCERNS. The project's design system and the owner's feedback win over the kit; map the
project's tokens onto the kit's roles.

Write exactly these two files and nothing else (no SPEC, PLAN, repository or other bitácora file):
1. {md} — the contract `{row['ref']}` with status `draft`, following the ui-ux-contract-authoring skill (all twelve
   sections, visual acceptance criteria table included).
2. {html} — a self-contained static mockup of that contract: inline CSS and JS only, no network request, no external
   font or image (use CSS or data: URIs), realistic mock data, every view of the subplan, a visible switch for each
   declared state (loading, empty, error, …) and layouts that reflow at the contract's breakpoints. Use the
   project's design tokens (mapped onto the kit's roles). Keep the template's "Mockup" label so nobody takes it for
   the product.

{previous}
Owner feedback to address (oldest first):
{asks}

In your report put one line per open question for the owner in "notes", each starting with "Q:", and one line with the
audit's RESULT line (or "audit not run: <reason>").
"""
