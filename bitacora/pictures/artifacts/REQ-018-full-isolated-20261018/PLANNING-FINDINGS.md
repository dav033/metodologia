# Planning and execution findings (in-progress evidence)

Owner asked why the plan encountered so many problems.

Observed causes:
- T1 combines category equivalence, lexical/style extraction, positive/negative preferences, colour/tone/age/gender constraints and legacy compatibility. Its medium classification and broad acceptance prose did not make the interacting parsing boundaries explicit enough to guide a reliable first implementation. Reclassification deserves review; these failures do not demonstrate comparative model suitability.
- Earlier routing/dependency simulations and the small M3 smoke were narrow proofs. They did not validate full product semantics or the actual rejected-attempt/retry route lifecycle.
- Some tests checked a desired term was present without checking extra fragment predicates or actual matcher/adapter membership. Natural request qualifiers, shared positive/negative heads and equivalent multiword aliases exposed the gap.
- The coordinator allowed successive partial repairs before enforcing one shared source for grammatical heads/modifiers and phrase evidence. The general invariants should have been tested together earlier.
- Real M2 persisted dispatch identity omitted M1 attempt ordinal, causing reuse of a single-use M3 route. This is a separate runtime defect, reproduced and fixed with real-ledger tests.

Changes actually verified so far: schema2 cumulative patch replay, integrity and lineage gates; M2 dispatch generation preserving initial identities; Next-generated type preparation; expanded T1 actual matcher/adapter regressions.

Pending methodology follow-up: strengthen pre-execution adversarial examples and rejection/retry lifecycle coverage; reassess complexity/evidence for coupled natural-language preference tasks. No new plan/routing policy or model-quality claim is made here. Current product plan remains the approved isolated eight-task plan, with acceptance governed by actual independent evidence.
