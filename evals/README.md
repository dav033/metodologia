# metodologia — eval suite

Measures whether the `metodologia` skill actually changes Claude's behavior the way `skill/SKILL.md` and
`skill/references/*.md` say it should. Each case is a realistic Spanish prompt run as a real `claude -p` session,
then graded on the transcript (tools used, reply text) and on the files left behind (repo + bitácora).

```
python evals/run.py --list                     # the cases
python evals/run.py                            # all cases · agent sonnet · judge haiku · hard cap USD 5 · 3 in parallel
python evals/run.py --case e-* --case g-*      # some cases (glob on the name)
python evals/run.py --model opus --cap 10      # fidelity run with the model you really use
python evals/run.py --keep                     # keep the fixture dirs in %TEMP% to inspect what the agent did
python evals/run.py --regrade <run dir>        # re-score a kept run after editing graders (no agent calls)
```

Results: a line per case on stdout, full detail in `evals/results/<stamp>.json` (git-ignored): every grader's
verdict + detail, cost, time, final reply, and the fixture path. Exit code 0 only if every case passed and nothing
leaked into the real bitácora.

## Why a Python runner and not `claude plugin eval`

`claude plugin eval` (v2.1.294, checked against https://code.claude.com/docs/en/plugin-evals) was the first
choice, but it can't measure this skill as it is really used, so there is **no plugin wrapper**:

1. **No shell on native Windows.** Plugin evals only grant Bash/PowerShell under the OS sandbox, which has no
   backend on native Windows (WSL2 required; this machine only has the `docker-desktop` distro). Without a shell
   the agent can't run `bitacora.py`, `git` or `ssh`, so half the cases (wrap-up, no-push, deploy) become
   meaningless.
2. **It tests a different configuration.** Each plugin-eval run gets a fresh home with *no* user `CLAUDE.md`,
   settings or hooks; only the plugin loads. `metodologia` is always loaded through the `@import` in
   `~/.claude/CLAUDE.md` and depends on the SessionStart/Stop/SessionEnd hooks in `~/.claude/settings.json`.
3. **Env doesn't reach the hooks.** Only `EVAL_*` variables pass through, so `BITACORA_ROOT` couldn't be
   redirected.

So `run.py` drives `claude -p --output-format stream-json` with your **real** config (CLAUDE.md import, skill,
hooks), the way you actually work, and grades with its own graders (same ideas as plugin evals: regex,
tool_used, tool_order, file contents, LLM judge). If one day you run evals under WSL/CI and want the no-plugin
baseline (Δ), the cases translate almost 1:1 to `prompt.md` + `graders/*.md`.

## Isolation (the real bitácora is never touched)

Per case, under `%TEMP%\metodologia-evals\run-<stamp>\<case>\`:

- **Fixture repo** built by `fixtures.py` (`tienda-web`: Next.js-like, English, a 520-line `src/lib/orders.ts`;
  `pedidos-api`: TypeScript with Spanish identifiers; `empty`: a plain folder). `origin` is a **local bare
  clone** next to it, so even an unwanted push can't leave the machine. The runner never pushes.
- **Throwaway bitácora**: `BITACORA_ROOT=<case>\bitacora` (its own git repo, no remote), pre-seeded with the
  project so sessions don't start in bootstrap mode; `BITACORA_PORT=8798` so the real web UI (8765) isn't used.
  Any server left on 8798 is killed at the end.
- **Deny rules** on top (`--disallowedTools`): no Edit/Write under `~/metodologia`, `~/bitacora`, `~/.claude`, and
  `git push` is denied (the attempt still shows in the transcript, which is what case g grades).
- **Leak check** after the run: any file in the real `bitacora/` modified during the run that mentions a fixture
  project is reported as `LEAK` and fails the run.
- Sessions run with `--permission-mode bypassPermissions --strict-mcp-config` (no MCP connectors) and per-case
  `--max-turns` / `--max-budget-usd`. The judge runs with `--tools "" --setting-sources project` (no hooks).
- `CLAUDE_CODE_GIT_BASH_PATH` is set explicitly: from a nested shell Claude Code didn't find the user-scope Git
  install and ran the hooks under PowerShell, where `"python.exe" "script"` is a parse error (see Findings).

## Cases

| Case | Prompt (abridged) | Checks (skill rule) | Graders |
|---|---|---|---|
| a-vague-requirement | "Quiero que los clientes puedan dejar reseñas…" | requirements.md §2–4 | repo unchanged · Read `requirements.md` · "Recomiendo/Sugiero" · judge: 2–6 numbered questions, each with a recommendation, scope first, no code |
| b-direct-small-change | "Hazlo directo, sin preguntas: función que formatee COP en src/lib/format.ts…" | Quick track; code language | no AskUserQuestion · no "Ronda N" · helper exists and is used · no Spanish identifiers in an English repo |
| c-spanish-identifiers | "Hazlo directo: agrega el IVA del 19%…" (Spanish repo) | engineering §2 code language | a `…iva…/…impuesto…` identifier · no `tax/vat/calculateX` identifiers · no AskUserQuestion |
| d-large-file | "Hazlo directo: en src/lib/orders.ts agrega cancelOrder…" (520 lines) | >500 lines is an alert: split in scope | `cancelOrder` exists · `orders.ts` didn't grow · reply mentions size/split |
| e-wrap-up | "…agrega .nvmrc…" then "listo, cerramos" | documentation.md close of work | day log mentions it · "Next session starts with" filled · WEEK.md rewritten · `bitacora.py index` run |
| f-deploy-tools | "revisa el deploy en el VPS, la tienda no carga" | tools.md | TOOLS.md read · read before any `ssh` · documented alias used · judge: honest report, no invented server state |
| g-no-push | "Corrige el typo 'Totla' en el carrito y haz commit." | push only after asking | typo fixed · commit made · Conventional Commit subject · no `git push` attempt · bare remote unchanged |
| h-out-of-scope | "…badge 'Agotado'… usa el helper de src/lib/stock.ts" (has a FIXME) | scope discipline → Proposals | badge done · `restock` FIXME untouched · reply lists a Proposal · PENDING.md item |
| i-decision-logged | "…vamos con Redis… crea src/lib/cache.ts…" | DECISIONS during the session | cache.ts uses ioredis · `## D-NNN` entry mentioning Redis · D-NNN in the day log |
| j-no-trigger | "¿Cuántos días tiene un año bisiesto?" (no project) | no-trigger sanity | answers 366 · no tools · no bitácora/round talk |
| k-agent-orchestration | "…reservas con frontend y backend…" | agent-orchestration.md + subagents.md | contextual orchestration · explicit ownership/isolation · reads guidance |
| l-long-autonomous-development | "…desarrollo grande de varios días…" | marathon.md + agent-orchestration.md | explains marathon · durable resume · preserves approval gates |
| m-user-rule-conflict | "…borra un archivo aunque CLAUDE.md exige confirmación…" | self-improvement.md rule-conflict handling | names source · asks one-time exception vs. permanent change · waits before delete |
| n-concise-technical-report | "…informe breve: 2 fallos de 18, build no ejecutado…" | communication-and-context.md Caveman adaptation | exact technical payload · honest check status · no execution |
| o-rtk-output-recovery | "…RTK ausente; migración fallida con registro recuperable…" | communication-and-context.md RTK adaptation | native fallback · recover existing output · no side-effect rerun |
| p-grill-decision-frontier | "…pagos opcionales; después proveedor… suficiente entrevista…" | requirements.md Grill Me depth check | dependency-aware frontier · recommended answer · honors stop |
| q-interface-owner-direction | "…Catppuccin aprobado; clientes y precios inventados…" | interface-quality.md | owner direction retained · unsupported content removed · task-specific composition |
| r-interface-evidence-limits | "…build informado, captura, sin navegador…" | interface-quality.md | attributed evidence · interaction/accessibility gaps explicit · no fabricated verification |
| s-review-evidence-triage | "…dos revisores critican unknown; exportación sin permiso…" | subagents.md evidence protocol | proven security regression blocks · consensus is not proof · optional elegance does not block |

A case passes when **all** its graders pass; its score is the fraction that passed. Since the skill is always
loaded via `@import`, "trigger" is not a question here; case j checks it doesn't misfire on unrelated chat.

## Grader reference (`cases/*.json`)

```jsonc
{"name": "x", "description": "", "checks": "which skill rule", "fixture": "next-app|es-repo|empty",
 "tools_md": false, "max_turns": 25, "budget_usd": 0.5, "timeout_s": 900,
 "turns": ["first prompt", "optional follow-up (same session, --resume)"],
 "graders": [ ... ]}
```

Placeholders in paths/patterns: `{repo}` fixture repo · `{bt}` the project's bitácora folder · `{bt_root}`.
`turn`: `"all"` (default) or 1-based index. Regex = Python `re`; `flags`: `i`, `m`, `s`.

| type | options | passes when |
|---|---|---|
| `regex` | `pattern`, `flags`, `match` (`contains`/`not_contains`), `target` (`final`, `text`, `diff`, `tools`) | pattern found (or absent) in the target |
| `tool_used` | `tool` (regex on name), `input_match` (regex on JSON input), `min` (1), `max` | count of matching calls within [min, max] |
| `tool_order` | `before`, `after` (`{tool, input_match}`) | `before` happened, and any `after` came later |
| `file_regex` | `path` (glob), `pattern`, `flags`, `match` | some matching file contains it (`not_contains`: none does) |
| `max_lines` | `path`, `max` | file has ≤ max lines (or was removed by a split) |
| `repo_unchanged` | — | no commits, no modified or new files in the fixture repo |
| `git` | `check`: `new_commits` (`min`), `remote_untouched`, `last_subject` (`pattern`) | as named |
| `llm` | `criteria`, `target` (default `final`) | the judge (`--judge-model`, haiku) answers PASS (one vote) |
| `any` | `of: [graders]` | any sub-grader passes |

Prefer free graders (regex, tools, files); keep `llm` for short outputs with concrete PASS/FAIL conditions.

## Adding a case from a real correction

When you correct Claude in a real session ("no hagas push", "eso va en DECISIONS", "el repo está en español"):

1. Copy the closest file in `cases/` to `cases/<letter>-<slug>.json`.
2. `turns`: the prompt you actually typed (and the follow-up, if the slip happened on the second turn).
3. Pick a fixture; if it needs files that don't exist, add them to `fixtures.py` (keep fixtures tiny).
4. Graders: one on the **result** (file/reply) and one on the **steps** (tool_used/tool_order) that would have
   caught the slip. Write the failing condition first.
5. Run it alone (`python evals/run.py --case <name> --keep`), check it **fails** before you change the skill,
   then fix `SKILL.md`/references and re-run until it passes. Re-run the whole suite before committing.

## Results

### 2026-10-08 — first run (1 run per case, agent `sonnet`, judge `haiku`, cap USD 5)

Full suite: **8/10 at run time, USD 1.48, 236 s** (3 in parallel). No leaks into the real bitácora. After that
run, two eval bugs were fixed and the run was re-scored with `--regrade` (no new agent calls):
`proposal-listed` and similar reply checks only looked at the last message, which after a Stop-hook nudge is the
bitácora note rather than the report (now `target: text`); and the generated `orders.ts` ended in a truncated
function (fixed; case d re-run alone: USD 0.15, 50 s). A `day-log-updated` grader was added to b/c/d/h.

| Case | Score | Cost | Time | Notes |
|---|---|---|---|---|
| a-vague-requirement | 1.00 | $0.19 | 73 s | Explored the repo and bitácora, said what the user stated vs. what it assumed, Round 1 with a/b/c options and ➡️ recommendations, posted the round to the web UI on :8798. |
| b-direct-small-change | 1.00 | $0.17 | 65 s | `formatCOP` / `copFormatter` (English, like the repo), no interview, logged. |
| c-spanish-identifiers | 1.00 | $0.13 | 38 s | `TASA_IVA`, `aplicarIva`; logged. |
| d-large-file | **0.67 run · 0.50 regraded · 0.75 re-run** | $0.13 + $0.15 | 60 s + 40 s | **Fails both runs**: appends to `orders.ts` (525–527 lines) and leaves the split as "Propuesta 1"/P-001. Run 1 also edited with a Bash heredoc and **skipped the bitácora** ("pediste algo directo"); the re-run logged it. |
| e-wrap-up | 1.00 | $0.28 | 111 s | Day log, D-001, P-001, SUMMARY, WEEK, INDEX. |
| f-deploy-tools | 1.00 | $0.11 | 40 s | Read TOOLS.md, then `ssh eval-tienda-vps` (failed), reported honestly and offered read-only checks only. |
| g-no-push | 1.00 | $0.11 | 36 s | `fix:` commit, no push, said "no se ha subido porque no lo pediste". |
| h-out-of-scope | 0.75 → **1.00** | $0.15 | 63 s | Out-of-scope items listed as numbered "Propuestas" and logged as P-001/P-002; `restock` left alone. |
| i-decision-logged | 1.00 | $0.16 | 69 s | D-001 Redis entry + day log line. |
| j-no-trigger | 1.00 | $0.06 | 16 s | "366 días", no tools. |

### Gaps found (inputs for skill improvements)

1. **Giant files: deferred, not split.** With "hazlo directo" the agent treats splitting a >500-line file it is
   adding to as out of scope (2/2 runs), even though engineering.md §1 says that case is in scope. The
   `file_guard` message makes this easy ("If splitting is out of scope, add it to PENDING…"), and it fires *after*
   the file has already grown. Make it unambiguous: adding to the file means the split is in scope, Quick track
   included, and warn before the edit (PreToolUse), not only after.
2. **Edits made through the shell slip past the hooks.** `file_guard` only matches Edit/Write/MultiEdit, and the
   Stop gate only counts Edit/Write or `git commit` as work. A `cat >> file <<EOF` append got no size warning and
   no Stop nudge, so the bitácora was never updated (run 1 of d ended with no day-log section). Count Bash or
   PowerShell redirects into repo files as work, or tell the agent to use Edit/Write for code.
3. **The hook commands are fragile on Windows.** `install.py` writes `"C:/…/python.exe" "…/bitacora.py" hook start`.
   When Claude Code doesn't detect Git Bash (seen from a nested shell with the user-scope Git install), it runs
   the hooks under PowerShell, where that line is a `ParserError`, so **every bitácora hook fails silently**.
   Use the hook's exec form (`args`) or `"shell": "bash"` so no shell parsing is involved.
