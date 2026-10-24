# Third-party notices for selected prompt adaptations

This file records licenses for excerpts and modified prompts in
[communication-and-context.md](communication-and-context.md). It is attribution material, not agent instructions.
Only prompt material is included; no upstream runtime, binary, font or transitive dependency is distributed.

## Engine v2 role adaptations

The following sources were inspected at the pinned revisions by the role-adaptation workers. The local prompts
and private skills use independently written procedures; no upstream scripts, plugins or runtime were executed
or included. Each row records the exact source, license at that revision and the adapted technique. Role-local
references retain the conditional triggers and exclusions. An unavailable or unverified source is excluded.

| Repository | Source path(s) | Commit SHA | License | Original local adaptation |
|---|---|---|---|---|
| `DietrichGebert/ponytail` | `skills/ponytail/SKILL.md` | `09c434ab73ca43761c5d8b0c5d341926c2fba710` | MIT (`LICENSE`) | Implementer: minimal complete work, reuse and preserved checks. |
| `JuliusBrussee/caveman` | `skills/caveman/SKILL.md` | `b4531dfc05a3ef0ba93b57e8bfa5f48564a4b4d6` | Apache-2.0 (`LICENSE`, `LICENSING.md`, `NOTICE`) | Implementer: concise reports retaining technical facts and structured fields. This revision uses the post-3.0 license, unlike the earlier master description. |
| `jakubkrehel/skills` | `skills/better-writing/SKILL.md`, `skills/better-layout/SKILL.md`, `skills/better-accessibility/SKILL.md`, `skills/better-colors/SKILL.md`, `skills/state-machine/SKILL.md` | `4c66b1fa86e9ab70187b43d7da9b6fdb29f2ef63` | MIT (`LICENSE`) | Designer: copy, hierarchy, accessibility, colors/tokens and reachable states. `build-design` excluded. |
| `wshobson/agents` | `plugins/ui-design/skills/design-system-patterns/SKILL.md`, `plugins/ui-design/skills/responsive-design/SKILL.md` | `0874a27b17a22e2b7c2e2bcd725768e0803cad06` | MIT (`LICENSE`) | Designer: token hierarchy and responsive specifications; no plugin or implementation workflow. |
| `mae616/design-skills` | `skills/ui-designer/SKILL.md` | `79e3398bee27664de70c7b97a30dd928f6fe7976` | MIT (`LICENSE`) | Designer: information architecture, hierarchy and states as specifications. |
| `anthropics/skills` | `skills/frontend-design/SKILL.md` | `dbd4588f9e1033efb41dad4bef2f7947c8993d44` | Apache-2.0 (`skills/frontend-design/LICENSE.txt`) | Designer: conditional aesthetic direction only; no production-code authority. |
| `akkie76/code-review-skills` | `dist/codex/evidence-code-review/SKILL.md` | `ca7b11c91906c60cc8aed611d5acb191d0335723` | MIT (`LICENSE`) | Reviewer: frozen scope, coverage, verifiable evidence and false-positive checks. |
| `JUNERDD/skills` | `skills/code-review/SKILL.md` | `f76dec9eacbcea858e1d469710067020bd3fec6a` | MIT (`LICENSE`) | Reviewer: semantic finding identity and lineage; no delegation or report automation. |
| `trailofbits/skills` | `plugins/differential-review/skills/differential-review/SKILL.md` | `196a9073ab10d35bacf111f945e02c00b2c6883a` | CC BY-SA 4.0 (`LICENSE`) | Reference to general risk-scoped review principles only. No source text copied or adapted. |
| `testdino-hq/playwright-skill` | `SKILL.md` | `178d1cb537604279d7b54500c4823a6db42b9de6` | MIT (`LICENSE`) | Visual Reviewer: breakpoint/state screenshots and conditional accessibility checks. |
| `anthropics/skills` | `skills/webapp-testing/SKILL.md` | `dbd4588f9e1033efb41dad4bef2f7947c8993d44` | Apache-2.0 (`skills/webapp-testing/LICENSE.txt`) | Visual Reviewer: rendered-app inspection and screenshot evidence; no helper scripts or upstream workflow. |
| `PriNova/pi-agent-codebase-workflows` | `skills/arch-code-review/SKILL.md` | `35cad6fb3a3e559a2519beed3887cb02497de5b2` | MIT | Antagonist: invariant-first architecture and contract checks. |
| `UnitOneAI/SecuritySkills` | `skills/appsec/threat-modeling/SKILL.md` | `70bc259bb01abb3015ad2ad859ad5253cbf0bcab` | MIT | Antagonist: conditional, focused STRIDE lens. |
| `vibeeval/vibecosystem` | `skills/premortem/SKILL.md` | `3b763b1fb288f57bfa3cce76ef18184b96461a78` | MIT | Antagonist: localized composition failure scenarios. |
| `ultimatile/development-skills` | `skills/codex-contract-test-review/SKILL.md` | `f68aaf63fa077906a7e4d62e9747d262a4c9c4fd` | MIT | Antagonist: contract tests must exercise the claimed invariant. |
| `magnus919/agent-skills` | `playwright/SKILL.md` | `7f446e60055b335dd26831371a027fa6b59da3e2` | MIT (`LICENSE.md`) | Runner: bounded commands and evidence. |
| `voidmatcha/e2e-skills` | `skills/playwright-debugger/SKILL.md` | `4ff48ba91ba5ef228e96852adcfb156b1ad49047` | Apache-2.0 | Runner: classify failed reports without repairing code. |
| `apache/magpie` | `plugins/magpie-repo-health/skills/flaky-test-triage/SKILL.md` | `27268f28a253978137e0cfa17bc19ef6e8897c28` | Apache-2.0 | Runner: history-based flakiness triage. |
| `j4flmao/agent-skills` | `skills/quality/smoke-testing/SKILL.md` | `5a19d636db60d2f7e08f036037a5b49c0a4ae8bd` | MIT | Runner: bounded smoke scenarios. |
| `douinc/agent-skills` | `skills/graph-engineering/SKILL.md` | `99ec1c314078a37a55a8534682b20a7a52683907` | MIT | Explorer: evidence-backed, read-only graph deltas. |
| `Data-System-School/agent-skills` | `investigate-codebase/SKILL.md` | `a117418ab3596c59d641cab4cb89bdbe560fb277` | MIT | Explorer candidate reference only; no procedure imported. |
| `event4u-app/agent-config` | `src/skills/blast-radius-analyzer/SKILL.md` | `4502d328ff6402f0dfb7bc1b970007179587282f` | MIT | Explorer candidate reference only; no procedure imported. |
| `SkillMedev/skills` | `skills/deep-research/SKILL.md`, `skills/research-synthesis/SKILL.md` | `97a13607d669157a4a16d5ba79b77f208319f7b9` | MIT (`LICENSE`) | Researcher: question decomposition, independent sources, atomic claims, tensions and evidence gaps. |
| `citypaul/.dotfiles` | `claude/.claude/skills/evaluate-existing-solutions/SKILL.md` | `cd4028d57d6e4e95814f7b8ee55ca13c23a9c2f0` | MIT (root license; target directory has no nested license/notice and is outside the `cli-design/` exception) | Researcher: compare existing options with the build baseline, ownership and reversibility; proposals only. |
| `jp-cruz/agent-skills` | `fact-checker/skill.md` | `ace4ecdcdffdfd7c37f8fa55d315e4c455b2e6bd` | MIT (`LICENSE`) | Researcher: checkable claims, supporting/refuting evidence, temporal scope and circular sources. |

`jamditis/claude-skills-journal` / `journalism-core/skills/source-verification/SKILL.md` could not be verified
(repository not found); no revision/license was established and no content was adapted.

Detailed local records: [Implementer](../agents/implementer/references/PROVENANCE.md),
[Designer](../agents/designer/references/public-design-techniques.md),
[Reviewer](../agents/reviewer/skills/evidence-based-findings/SKILL.md),
[visual Reviewer](../agents/reviewer/skills/rendered-ui-fidelity-audit/SKILL.md),
[Antagonist](../agents/antagonist/references/public-adversarial-techniques.md),
[Runner](../agents/runner/references/public-testing-techniques.md),
[Explorer](../agents/explorer/skills/subplan-dependency-analysis/SKILL.md), and
[Researcher](../agents/researcher/references/public-research-techniques.md).

## Caveman

Caveman
Copyright 2026 Julius Brussee

Adapted and modified from revision `2e08b9177c07bb7249a8a2d1a6758e5db281d002`.
The retained portion of the upstream NOTICE relevant to these prompts follows:

Before Caveman 3.0.0, the parts of this repository outside the Engine-linked
runtime were licensed under the MIT License (see LICENSING.md). Contributions
made to those parts before 3.0.0 were received under the MIT License and remain
available under it. Its copyright and permission notice is retained in
LICENSE-MIT.

Current licensing: Apache-2.0, reproduced below. Legacy MIT notice retained verbatim:

```text
MIT License

Copyright (c) 2026 Julius Brussee

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## RTK

Adapted and modified from `rtk-ai/rtk`, revision `311ebcbfd8efdb09b03219e7615a153b5b5e3c97`.
Upstream root LICENSE contains the same Apache-2.0 terms reproduced below and this copyright notice;
no root NOTICE was present at that revision. Retained notice:

```text
Copyright 2024 rtk-ai and rtk-ai Labs

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
```

## Matt Pocock's Grill Me / grilling

Adapted and modified from revision `49dd158d1076134a641b33efb035946536778336`.
Retained upstream license:

```text
MIT License

Copyright (c) 2026 Matt Pocock

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Matt Pocock's engineering and productivity skills (policy adaptations)

Adapted and modified from `mattpocock/skills`, revision `49dd158d1076134a641b33efb035946536778336`, the same
revision and license as the Grill Me / grilling section above. License: MIT, "Copyright (c) 2026 Matt Pocock"; the
complete permission notice is reproduced in that section and applies to every file below.

Only prompt material was reviewed and re-expressed; no upstream script, template, runtime or dependency is
distributed. Each adapted file begins with `Source: mattpocock/skills@49dd158 (MIT), <path>` and states which rules
are adapted and which are original or deliberately not imported.

| metodologia file | Upstream source (at the revision above) |
|---|---|
| `references/design-vocabulary.md` | `skills/engineering/codebase-design/SKILL.md`, `DEEPENING.md`, `DESIGN-IT-TWICE.md` |
| `references/improve-architecture.md` | `skills/engineering/improve-codebase-architecture/SKILL.md`, `HTML-REPORT.md` |
| `references/domain-glossary.md` | `skills/engineering/domain-modeling/SKILL.md`, `GLOSSARY-FORMAT.md`, `ADR-FORMAT.md` |
| `references/glossary-conventions.md`, `templates/GLOSSARY.md` | `skills/engineering/domain-modeling/GLOSSARY-FORMAT.md`, `ADR-FORMAT.md` |
| `references/test-seams.md` | `skills/engineering/tdd/SKILL.md`, `tests.md`, `mocking.md`; seam step of `skills/engineering/to-spec/SKILL.md` |
| `references/diagnosing-bugs.md` | `skills/engineering/diagnosing-bugs/SKILL.md` |
| `references/retro-feedback.md` | `skills/engineering/retro/SKILL.md` |
| `references/writing-for-agents.md` | `skills/productivity/writing-for-agents/SKILL.md`, `SKILL-MECHANICS.md` |
| `references/wait-what.md` | `skills/productivity/wait-what/SKILL.md` |

Reviewed and not adopted (no text used): all other upstream skills, including `pr`, whose visual-summary menu is
credited upstream to Dex Horthy's `show-me` (`skills/engineering/pr/CREDITS.md`); if `pr` is ever adopted, that
credit must be carried here as well.

The pinned upstream copy used for review is `/home/david/.local/share/metodologia-migration/upstream/skills`;
the review record is `bitacora/metodologia/migracion/evidence/POCOCK-REVIEW.md`.

## Planner-only skill adaptations

These resources are available only through the `planner` agent definition. The instructions were re-expressed for
this methodology's requirement rounds, `PLAN.json` contract and deterministic validator; no upstream code,
scripts, dependencies or verbatim workflow text is distributed.

| metodologia file | Upstream source (pinned revision) | Adaptation |
|---|---|---|
| `agents/planner/skills/socratic-elicitation/SKILL.md` | [`mthines/agent-skills` `interview`](https://github.com/mthines/agent-skills/blob/39b3f44106590db62e7f1509b2d9c727e47243cf/skills/analysis/interview/SKILL.md) | Adaptive, research-first clarification; the existing requirement workflow remains authoritative. |
| `agents/planner/skills/wbs-dag-decomposition/SKILL.md` | [`addyosmani/agent-skills` `planning-and-task-breakdown`](https://github.com/addyosmani/agent-skills/blob/aeac41d4d005999432bb7312f7ff06383a91d59d/skills/planning-and-task-breakdown/SKILL.md) | Small verifiable tasks and dependency mapping, constrained to the local schema. |
| `agents/planner/skills/adversarial-plan-review/SKILL.md` | [`ctxr-dev/agent-plan-reviewer`](https://github.com/ctxr-dev/agent-plan-reviewer/tree/2cff4fefc44576aa28217a4af728117d511a1c57) | Read-only evidence checks and actionable findings; local structural validation remains deterministic. |

The optional Mermaid projection is original glue over `PLAN.json`; no diagram package, renderer, hosted MCP, Gantt
date convention or PlantUML source is included.

MIT License notices for the adapted prompt concepts:

```text
MIT License

Copyright (c) 2026 Mads Thines <madsthines@gmail.com> (https://github.com/mthines)
Copyright (c) 2025 Addy Osmani
Copyright (c) 2026 Dmitri Meshin <dmitri.meshin@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Apache License 2.0

Full license text from the pinned Caveman LICENSE. Sections 1–9 and END OF TERMS AND CONDITIONS
are also identical to RTK's LICENSE; RTK's specific copyright notice is retained above.

```text
Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity. For the purposes of this definition,
      "control" means (i) the power, direct or indirect, to cause the
      direction or management of such entity, whether by contract or
      otherwise, or (ii) ownership of fifty percent (50%) or more of the
      outstanding shares, or (iii) beneficial ownership of such entity.

      "You" (or "Your") shall mean an individual or Legal Entity
      exercising permissions granted by this License.

      "Source" form shall mean the preferred form for making modifications,
      including but not limited to software source code, documentation
      source, and configuration files.

      "Object" form shall mean any form resulting from mechanical
      transformation or translation of a Source form, including but
      not limited to compiled object code, generated documentation,
      and conversions to other media types.

      "Work" shall mean the work of authorship, whether in Source or
      Object form, made available under the License, as indicated by a
      copyright notice that is included in or attached to the work
      (an example is provided in the Appendix below).

      "Derivative Works" shall mean any work, whether in Source or Object
      form, that is based on (or derived from) the Work and for which the
      editorial revisions, annotations, elaborations, or other modifications
      represent, as a whole, an original work of authorship. For the purposes
      of this License, Derivative Works shall not include works that remain
      separable from, or merely link (or bind by name) to the interfaces of,
      the Work and Derivative Works thereof.

      "Contribution" shall mean any work of authorship, including
      the original version of the Work and any modifications or additions
      to that Work or Derivative Works thereof, that is intentionally
      submitted to Licensor for inclusion in the Work by the copyright owner
      or by an individual or Legal Entity authorized to submit on behalf of
      the copyright owner. For the purposes of this definition, "submitted"
      means any form of electronic, verbal, or written communication sent
      to the Licensor or its representatives, including but not limited to
      communication on electronic mailing lists, source code control systems,
      and issue tracking systems that are managed by, or on behalf of, the
      Licensor for the purpose of discussing and improving the Work, but
      excluding communication that is conspicuously marked or otherwise
      designated in writing by the copyright owner as "Not a Contribution."

      "Contributor" shall mean Licensor and any individual or Legal Entity
      on behalf of whom a Contribution has been received by Licensor and
      subsequently incorporated within the Work.

   2. Grant of Copyright License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to reproduce, prepare Derivative Works of,
      publicly display, publicly perform, sublicense, and distribute the
      Work and such Derivative Works in Source or Object form.

   3. Grant of Patent License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      (except as stated in this section) patent license to make, have made,
      use, offer to sell, sell, import, and otherwise transfer the Work,
      where such license applies only to those patent claims licensable
      by such Contributor that are necessarily infringed by their
      Contribution(s) alone or by combination of their Contribution(s)
      with the Work to which such Contribution(s) was submitted. If You
      institute patent litigation against any entity (including a
      cross-claim or counterclaim in a lawsuit) alleging that the Work
      or a Contribution incorporated within the Work constitutes direct
      or contributory patent infringement, then any patent licenses
      granted to You under this License for that Work shall terminate
      as of the date such litigation is filed.

   4. Redistribution. You may reproduce and distribute copies of the
      Work or Derivative Works thereof in any medium, with or without
      modifications, and in Source or Object form, provided that You
      meet the following conditions:

      (a) You must give any other recipients of the Work or
          Derivative Works a copy of this License; and

      (b) You must cause any modified files to carry prominent notices
          stating that You changed the files; and

      (c) You must retain, in the Source form of any Derivative Works
          that You distribute, all copyright, patent, trademark, and
          attribution notices from the Source form of the Work,
          excluding those notices that do not pertain to any part of
          the Derivative Works; and

      (d) If the Work includes a "NOTICE" text file as part of its
          distribution, then any Derivative Works that You distribute must
          include a readable copy of the attribution notices contained
          within such NOTICE file, excluding those notices that do not
          pertain to any part of the Derivative Works, in at least one
          of the following places: within a NOTICE text file distributed
          as part of the Derivative Works; within the Source form or
          documentation, if provided along with the Derivative Works; or,
          within a display generated by the Derivative Works, if and
          wherever such third-party notices normally appear. The contents
          of the NOTICE file are for informational purposes only and
          do not modify the License. You may add Your own attribution
          notices within Derivative Works that You distribute, alongside
          or as an addendum to the NOTICE text from the Work, provided
          that such additional attribution notices cannot be construed
          as modifying the License.

      You may add Your own copyright statement to Your modifications and
      may provide additional or different license terms and conditions
      for use, reproduction, or distribution of Your modifications, or
      for any such Derivative Works as a whole, provided Your use,
      reproduction, and distribution of the Work otherwise complies with
      the conditions stated in this License.

   5. Submission of Contributions. Unless You explicitly state otherwise,
      any Contribution intentionally submitted for inclusion in the Work
      by You to the Licensor shall be under the terms and conditions of
      this License, without any additional terms or conditions.
      Notwithstanding the above, nothing herein shall supersede or modify
      the terms of any separate license agreement you may have executed
      with Licensor regarding such Contributions.

   6. Trademarks. This License does not grant permission to use the trade
      names, trademarks, service marks, or product names of the Licensor,
      except as required for reasonable and customary use in describing the
      origin of the Work and reproducing the content of the NOTICE file.

   7. Disclaimer of Warranty. Unless required by applicable law or
      agreed to in writing, Licensor provides the Work (and each
      Contributor provides its Contributions) on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
      implied, including, without limitation, any warranties or conditions
      of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
      PARTICULAR PURPOSE. You are solely responsible for determining the
      appropriateness of using or redistributing the Work and assume any
      risks associated with Your exercise of permissions under this License.

   8. Limitation of Liability. In no event and under no legal theory,
      whether in tort (including negligence), contract, or otherwise,
      unless required by applicable law (such as deliberate and grossly
      negligent acts) or agreed to in writing, shall any Contributor be
      liable to You for damages, including any direct, indirect, special,
      incidental, or consequential damages of any character arising as a
      result of this License or out of the use or inability to use the
      Work (including but not limited to damages for loss of goodwill,
      work stoppage, computer failure or malfunction, or any and all
      other commercial damages or losses), even if such Contributor
      has been advised of the possibility of such damages.

   9. Accepting Warranty or Additional Liability. While redistributing
      the Work or Derivative Works thereof, You may choose to offer,
      and charge a fee for, acceptance of support, warranty, indemnity,
      or other liability obligations and/or rights consistent with this
      License. However, in accepting such obligations, You may act only
      on Your own behalf and on Your sole responsibility, not on behalf
      of any other Contributor, and only if You agree to indemnify,
      defend, and hold each Contributor harmless for any liability
      incurred by, or claims asserted against, such Contributor by reason
      of your accepting any such warranty or additional liability.

   END OF TERMS AND CONDITIONS

   APPENDIX: How to apply the Apache License to your work.

      To apply the Apache License to your work, attach the following
      boilerplate notice, with the fields enclosed by brackets "[]"
      replaced with your own identifying information. (Don't include
      the brackets!)  The text should be enclosed in the appropriate
      comment syntax for the file format. We also recommend that a
      file or class name and description of purpose be included on the
      same "printed page" as the copyright notice for easier
      identification within third-party archives.

   Copyright [yyyy] [name of copyright owner]

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
```

