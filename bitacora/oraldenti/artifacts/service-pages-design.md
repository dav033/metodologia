# Dedicated service pages

## Scope and acceptance
Owner requested one page per service, including all subservices. Generate nine static /servicios/<slug>/ pages from the verified catalog and link them from the homepage. Preserve all87 procedure entries. No separate procedure pages, new claims, backend, dependencies or publishing.

Each page must return200, display the correct heading/description and full list, link back to working home sections and remain usable on mobile without JavaScript. Unknown slugs return404. Existing checks and new route/navigation tests must pass.

## Design pass and critique
Reuse porcelain #fcfcff, ink #29233f, violet #6650ab, action blue #006f8c, pale cyan #eaf8fc and lavender #f0edf8. Bricolage Grotesque headings, Manrope body; left-aligned text and short body measures.

Option A: repeat oversized carousel and identical cards. Rejected because it delays the requested catalog information. Option B: concise service-specific introduction, readable procedure list and adjacent contact panel.

    [shared logo / home navigation / appointment]
    [home > services > current service]
    [service title + description | illustrative image]
    [all subservices              | contact panel]
    [other specialties]
    [shared footer]

Choose B. Prioritize actual procedure names; no decorative numbering or new motion. Implantology has no source sublist, so use its verified description and an inquiry action instead of invented procedures. The original photos remain illustrative, never patient outcomes.

## Contracts
Add stable readable slugs without changing existing IDs or procedure strings. Catalog owns the shared service type. Presenters receive typed props, no runtime content imports. Root-prefixed anchors return from nested pages to home. Keep one source of truth for home, detail pages and appointment options.
