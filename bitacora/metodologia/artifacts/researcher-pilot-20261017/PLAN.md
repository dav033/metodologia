# Researcher native pilot

Owner accepted the proposed matched comparison with “adelante” after research on
Sonnet medium, Sol medium and Luna high. This is a bounded experiment outside
formal REQ-024, not a permanent role assignment. Direct execution in this session.

Assumptions chosen by the coordinator: six cases per model (four frozen corpus,
two live search), one repetition, maximum18 native calls,600s/cell,35 Claude turns.
Profiles: Sonnet on claude-work; both OpenAI candidates on codex-2. One active call
per account, two provider lanes. Alternate Codex route order by case.

1. Prepare shared version-pinned primary-source extracts and six claim criteria
   for each task; keep coordinator rubric outside candidate visibility.
2. Validate corpus coverage, note contract and sandbox masking without model
   calls; obtain spec/standards review and fix verified defects before freeze.
3. Freeze cases, rubric, sources, native commands and collector hashes; invoke
   each cell once. Do not retry/repair, rotate accounts or substitute routes.
   Provider/auth/limit/challenge failures stop that provider lane; report missing
   cells rather than filling them. Any started result file prevents a repeat.
4. Grade content against frozen criteria, verify evidence locators, and report
   JSON contract, native retrieval/tool failures and unsupported claims separately.
   Publish original results, comparison and REPORT; update project memory.

Verification: `python run.py validate` before freeze; `python run.py verify`
after freeze; results must enumerate18 unique planned IDs or explicit stopped
lanes. Recompute usage/time from saved counters, never turn missing usage into0.
Reviewers do not invoke candidate models or access credentials.

Live tasks measure the native research system, with different provider tools;
frozen tasks isolate source interpretation. One sample/cell is not statistical
superiority. Requested identities/efforts are not effective attestation. Token
counts are not invoices or equivalent quota. No prices will be inferred.

Cases: R1 asyncio concurrency; R2 cross-version SQLite lifetime; R3 Node HTTP
timeout scope; R4 PostgreSQL concurrent-index failure/recovery; R5 Node LTS dates
as of2026-10-17; R6 uv lock freshness versus synchronization/network behavior.
