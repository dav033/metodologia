# Writing for agents: concise policy and instruction authoring

Source: mattpocock/skills@49dd158 (MIT), skills/productivity/writing-for-agents/SKILL.md and
SKILL-MECHANICS.md. Adapted here: context pointers, the two loads, the information hierarchy, completion
criteria, leading words, positive phrasing and pruning. Original here: the authoring checklist, the governance
carve-outs and the measurement rule. Not imported: skill frontmatter and `disable-model-invocation` mechanics
(platform-specific) and the claim that negations are always wrong. License: `third-party-notices.md`.

## Load when

You create or edit a document an agent will read: SKILL.md, a reference, a template, a CLAUDE.md/AGENTS.md, a
delegation brief or a per-task prompt, or an eval case. Also when a rule is being ignored and you suspect the
wording or placement, and when someone asks to shorten always-loaded text. Not for ordinary prose for humans.

## 1. Pointers decide when material is read

A router row, a line in CLAUDE.md or a description is a **context pointer**: it names material outside the
context and the condition to reach it. The wording, not the target, decides when and how reliably it is read.

- State what the material is and the **branches** that should trigger it. One trigger per distinct branch; synonyms
  for one branch are noise.
- Put the leading word first and cut identity the body already carries.
- A must-have target behind a weak pointer is a variance bug: sharpen the wording first, inline only if that fails.
- Every word of an always-loaded pointer is paid on every turn, so it is pruned harder than the body.

## 2. Two loads

- **Context load**: always-loaded text (SKILL.md, CLAUDE.md, descriptions). It costs tokens and attention each turn.
- **Cognitive load**: the human must remember which documents exist and when to reach for each.

Material reached only by a pointer escapes the context load. Move what only some branches need behind a pointer
and keep inline what every branch needs. Measure with `wc -c` before and after; record the numbers, not a target.

## 3. Shape of a document

- **Steps** are ordered actions; **reference** is rules and facts consulted on demand. Keep steps primary; do
  not bury them in reference that should be disclosed.
- **Co-locate** a concept's definition, rules and caveats under one heading so reading one brings the others.
- **Sprawl** is length alone: attention thins even when every line is unique. Treat the 500-line alert
  (`engineering.md` §2) as a warning for documents, not a hard gate; split by branch or by sequence when it fires.
- **Every step ends on a completion criterion** that is checkable and exhaustive ("every changed contract traced
  to a caller" beats "reviewed"). A vague bound invites finishing early: sharpen it before splitting the sequence.

## 4. Words

- A **leading word** already in the model's priors (tight, red, seam, frontier) replaces a repeated phrase. Define
  a coined word once, or use an existing one.
- Prefer the positive: say the target behaviour. A prohibition earns its place as a hard guardrail you cannot
  phrase positively (no `git push` unasked, no secrets in code); pair it with what to do instead.
- Keep the owner's words and the project's glossary terms (`domain-glossary.md`) in policy text.

## 5. Pruning

- **One source of truth.** Point to the section that owns a rule (`see engineering.md §5`) instead of copying it;
  a copy drifts and inflates the rule's prominence.
- **The environment is a source of truth too** (package.json scripts, config, `--help`). Cache only what cannot
  be found by looking: the unwritten convention, the reason, the gotcha.
- **Relevance.** Remove lines that never bore on the task or went stale; sediment accumulates because adding feels
  safe and removing feels risky.
- **No-ops.** A sentence the model already obeys by default adds load and no behavior. Test by running the document
  or an eval, not by debate, and delete the whole sentence. Never remove permission, approval, safety, language or
  attribution rules on a no-op argument; those need a confirmed learning or an eval (`self-improvement.md`).

## 6. Checklist before saving

1. Does a pointer name when this loads, and is the branch distinct from existing rows?
2. Does it duplicate or contradict another reference? `grep` the rule you restate and link to the owner.
3. Is any adapted text attributed (`Source:` header, `third-party-notices.md`) with adapted versus original marked?
4. Did you record before/after bytes for anything always loaded?
5. Does an eval or a stated check cover the behavior you changed?
