# Third-party notices for selected prompt adaptations

This file records licenses for excerpts and modified prompts in
[communication-and-context.md](communication-and-context.md). It is attribution material, not agent instructions.
Only prompt material is included; no upstream runtime, binary, font or transitive dependency is distributed.

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

