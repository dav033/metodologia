# SP-14 v2 subscription cards — owner review

Status: three ready design choices;owner selection,final contract and SP-14 confirmation pending. No UI approval/freeze or product implementation by Planner.

## Authority

P211 rejects published SP14version2 commit0715a331b72111afe085e35d773b284764924fe4. Reproduction evidence/owner-rejected/SP-14-v2.md and its linked screenshots show the old comparison/selection UI. The owner now requests conventional subscription cards without that logic. This explicitly supersedes round13 extra-view behavior;it is not a D241 repair. P211 stays open until owner approval of a later published product version.

## Exact proposed plan/contract delta

- New planes@v2 is a breaking presentation/interaction revision. Approved planes@v1 and unchangedT14.1 remain immutable. NewT14.11 copies only the independently owner-approved v2 artifact afterCG1,parallel with oldv1 copy. T14.2 gains that real design prerequisite.
- T14.2 uses the existing page/component/style/copy files for four informational catalogue cards. Remove comparison tabs,index,selection/highlight state/summary and old-view actions. All names,prices,tools,availability,public-route and tablet criteria remain;new focused static checks cover changed files.
- T14.3 retains all entry-link criteria/checks;only its objective clarifies preservation of the active SP2 contract. No account-menu redesign in SP14.
- T14.4 preserves its main signed-in/out/currency/entry flow and protected-route refusal. Replace only selection assertions with actual no-mutation,legacy-query equivalence and4width card cases.
- T14.5 compares the new card contract through the same visual-ledger command. T14.6 audit is exactly unchanged.
- CG4/T94 keeps its primary admin-assignment/permission criterion and planes:test-composicion command;replace only its selection-specific second criterion with no-mutation using the producer-ownedT14.4 case. CG4 membership/id/task and every other gate are unchanged.

## Check retirement map

| Existing comparison-specific check | New expectation/check |
|---|---|
| T14.2 planes:test-ui --solo vista-eleccion | --solo tarjetas:4informational cards,no selection/highlight/card actions |
| T14.4 selector-sin-cambio mapping1 | --solo tarjetas-sin-mutacion:actual assignment and next-request permissions unchanged |
| T14.4 selector-sin-cambio mapping2 | --solo legado-sin-comparacion:old query URLs restore no alternate mode |
| T14.5 v1 comparison/extra-view criterion | v2cards/full tools/no comparison atdeclared widths,languages;existing ledger retained |
| T94 comparison-only selection criterion | card/no-mutation integration case;primary admin assignment/guard acceptance unchanged |

No skips,lowered thresholds or unrelated test removals. New --solo tarjetas-responsive checks360/390/768/1280. Old /planes?vista=seleccionar or selected-plan queries show the same cards.

## Preserved constraints

Exactly4canonical plans in order;monthly COP for ES and USD for EN,neverboth;Entusiasta free;complete cumulative tools and unavailable markers;existing chat-limit descriptions without numbers. No purchase,request,signup,contact,account mutation,current/recommended-plan badge,selected card or collapsed tools. Public route and sign-in/account-menu links remain. Host shell,theme,language/account mechanism,permissions,role storage and catalogue validation stay unchanged. Catalogue data is a static import validated atmodule load:do not invent a catalogue fetch or no-op Retry. Keep canonical punctuation;any optional item count is derived from visible entries,not a quota. Back navigation retains the current host behavior/target;no unrelated origin-tracking feature.

## Consumer impact

SP14only changes its UI contract and requires owner reconfirmation. Existing CG4→CG2→CG3→CG5…CG13 reverify their integrated candidates. No other subplan contract or implementation is reopened without a proven incompatibility. SP2 was independently confirmed by the owner after its chosenC correction. SP3 has a separate bounded repair frozen inr31;neither is part of the unapproved card redesign.

## Concrete design choices

A — Fichas en fila;B — Estantería;C — Cartas al pie. All3are ready and normal comparison passes. Default and768/360 supplemental audits pass:A80+80renders,B100+100,C100+100;each contrast158pairs passes. These are static preview checks,not product/account mutation acceptance. Technical/current-brief clarifications fold into the selected final artifact through normal D162;no new broad interview is needed.

Next:owner chooses A/B/C in Plan→SP14,Designer finalizes the selected exact contract/mockup,owner confirms SP14. Planner never chooses/confirms/freezes the UI on behalf of the owner. Exact conservation evidence:/home/david/.local/tmp/req021-sp14-amendment-1a41/semantic-review.json.
