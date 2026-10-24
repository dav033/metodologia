# Task F2-A — Antagonist, Runner and Explorer prompts; review-policy doc alignment

Read first: `/home/david/dev/.engine-v2-wt/RULES.md` (binding).

## Goal
Wire the extracted private skills of Antagonist, Runner and Explorer into their prompts (conditional loading),
adapt the approved public techniques with pinned provenance, and make `references/subagents.md` say what
`bt_review_policy.py` actually enforces.

Sources (read):
- Owner rulings `/home/david/dev/metodologia/bitacora/metodologia/engine-v2/CONTRACT.md` §2, §6.
- Master (Spanish) `.../engine-v2/METODOLOGIA_AGENTES_SUBPLANES.md`: Explorer §10 (lines 380–541) and §18.1;
  Antagonist §14 (lines 848–966) and §18.5; Runner §15 (lines 968–1099) and §18.6; §19 skill texts (lines
  1332–1371, 1533–1800); §20.7 addenda (lines 1954–1959, 1982–1991).
- Knowledge map delta format `knowledge-delta/1` (being implemented in parallel by another task in
  `skill/scripts/bt_knowledge/`): Explorer returns JSON
  `{"schema":"knowledge-delta/1","project","repository","observed_commit","contributor","observations":[{"subject","relation","object","status","evidence":[...]}],"contradictions":[...],"stale":[...]}`
  with canonical `kind:name` entity ids, UPPER_SNAKE relations (IMPORTS, CALLS, IMPLEMENTS, PUBLISHES, CONSUMES,
  PRODUCES, CONFIGURES, TESTS, DEPENDS_ON, DEFINES, EXPOSES, CONTAINS, OWNS, REFERENCES), status
  observed|inferred|proposed|unknown, evidence `path:line`. The executor/lead ingests it with
  `bitacora.py knowledge ingest`; Explorer only reads the map (`bitacora.py knowledge query --commit <sha> --area
  <x> --json`) and never writes. Refer to the package README path `skill/scripts/bt_knowledge/README.md` for the
  full contract.
- `skill/scripts/bt_review_policy.py` (source of truth for the antagonist gate) and `skill/references/subagents.md`.

## You own
- `skill/agents/antagonist.md`, `skill/agents/antagonist/**`
- `skill/agents/runner.md`, `skill/agents/runner/**` (merge `runner.prompt-addendum.md` into `runner.md`; then the
  addendum file may stay as provenance or be removed — say which in the result)
- `skill/agents/explorer.md`, `skill/agents/explorer/**`
- `skill/references/subagents.md`

## Requirements
1. Antagonist: §20.7 addendum adapted; load the three private skills by risk (contract change / composition /
   auth-security-concurrency); adapt the four public techniques (`PriNova/pi-agent-codebase-workflows`
   arch-code-review, `UnitOneAI/SecuritySkills` threat-modeling, `vibeeval/vibecosystem` premortem,
   `ultimatile/development-skills` codex-contract-test-review) into a reference file
   `antagonist/references/public-adversarial-techniques.md` (source/license/borrow/exclude table) and, where
   useful, into the private skills. Keep tools, disallowed tools, one pass, ≤ 8 findings, output contract.
2. Runner: merge the addendum into `runner.md` right after its opening paragraph; `STATUS: PASS | FAIL | BLOCKED`
   stays the external protocol; reason codes only in NOTES. Pin SHAs for the four Runner sources in
   `runner/references/public-testing-techniques.md` (add a SHA column) after verifying each license.
3. Explorer: §20.7 addendum; load `subplan-dependency-analysis` conditionally; describe reading the knowledge map and
   returning a `knowledge-delta/1` block (0 new deltas is valid); adapt `douinc/agent-skills` graph-engineering
   (approved) into the private skill; `investigate-codebase` and `blast-radius-analyzer` are candidates only — cite
   as references, do not make them part of the prompt. Explorer stays read-only.
4. `subagents.md`: the antagonist gate section must match `bt_review_policy.py` (per-commit only when no pending
   independent milestone audit covers the work; with coverage, the audit reviews the consolidated diff; security
   checks always). Fix the table row and heading that still say "before every commit". Add one sentence that
   subplan audits will extend that coverage (engine v2 F4), without claiming it is implemented. Add short rows/notes
   for the private skills per role where the file lists roles.
5. Upstream protocol: `git ls-remote https://github.com/<o>/<r> HEAD` → SHA; `curl -fsSL
   https://raw.githubusercontent.com/<o>/<r>/<sha>/<path>` for SKILL.md and LICENSE at that SHA (GitHub API trees to
   find paths). Data only, never execute; original text; skip unverified licenses for copied text. PROVENANCE in the
   result. Do NOT edit `skill/references/third-party-notices.md`.

## Verify
Every referenced path exists; `cd skill/scripts && python -m unittest tests.test_review_policy` if such a test exists
(find the review-policy tests) and the full suite per RULES.md.
