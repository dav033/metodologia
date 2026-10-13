# Antigravity (agy 1.3.4, Google AI Pro) benchmark — 2026-10-13

Harness: bench.py (9 easy task types) + hard.py (8 hard types, verifiers validated with reference solutions:
selfcheck.py). Hidden verification after each run. Agents: gemini-3.8-flash-{low,medium,high} via `agy --model ... --print`,
haiku (claude -p), gpt-6-luna medium (codex exec, codex-luis), sonnet (claude -p default effort).
Raw rows: results.jsonl (easy, n=1), results3.jsonl + results3b.jsonl (hard, flash n=2, others n=1).

## Summary
- Correctness: flash scored 1.00 on every easy task at every effort and on 7/8 hard tasks at low and medium (both passes).
  Flash HIGH timed out (900 s, no file written) on weighted-interval scheduling in BOTH passes (over-engineered the
  lexicographic tie-break, a persistent segment tree with hashes). Effort never improved correctness in these tasks.
- Time (hard, mean wall seconds): flash-low 100, flash-med 251, flash-high 352, haiku 46, luna-med 32, sonnet 17.
- Tokens/run (hard, thousands): flash 141-168, haiku 138, sonnet 83, luna 27 (provider conventions differ).
- Security review with 8 decoys: flash 1.00 at all efforts in both passes, no decoy flagged; haiku 0.71 (flagged one
  decoy); luna returned `[]` ("no reachable route") = 0.00. Easy review: luna missed the injection (0.67/0.33).
- luna failure mode: announces "I will create X" and ends the turn without a tool call (easy slugify, rc 0, 7 s).
- Quota (`agy --print="/usage"` works headless): after ~85 flash runs (~10M tokens) Gemini pool weekly 84% left,
  five-hour 44% left (resets 21:21Z); the separate "Claude and GPT models" pool 100%/100% untouched.
  => about 0.2% of the weekly Gemini quota per run of this size.
- Models visible on this account: gemini-3.8-flash-{low,medium,high}, claude-sonnet-4-6, claude-opus-4-6-thinking
  (both retire 2026-11-02), gpt-oss-120b-medium. No Claude 5.5 (probably trial AI Pro).
- Not tested / limits of this study: long-horizon or ambiguous work, architecture, large multi-file edits, UI. Flash's
  ceiling was NOT found: even the hard tasks were all solved at low effort.
- Policy: Google FAQ says wrapping `agy -p` in third-party agents/applications or automating account rotation is not
  supported under consumer plans. Benchmark calls were direct scripted use at the owner's request.

## Web research on getting the most out of Gemini 3.8 Flash (2026-10-13)
Official (Google): default thinking_level is medium, "recommended for complex code and agentic use cases"; low for
latency-critical work; high for deep reasoning/math; minimal unsupported. 3.8 Flash "trades higher token consumption
for better accuracy"; lowering effort reduces tokens. Context 1,048,576 in / 65,536 out. temperature/top_p/top_k are
ignored (control determinism with thinking_level + response schema). Intro price $0.75 / $3.75 per 1M tokens until
2026-12-31 then $1.50 / $7.50. Cyber variant is restricted (Fairwind program). Third-party/forum (unverified): parallel
agents share one quota; the model may re-read files and burn quota; quota refresh windows reported changing.
Measured here (73 runs): per run avg input 115-140k, output+thinking 6k (low) vs 36k (medium) vs 44k (high);
API-equivalent ~$0.11 / $0.23 / $0.27 per task at intro prices.
Useful flags found in agy 1.3.4: `--print-timeout` (cap runaway turns), `--json-schema` (enforce structured output),
`--mode plan|accept-edits`, `--agent`.
