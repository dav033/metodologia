# oraldenti — Architecture

**Last verified:** 2026-10-17 against the uncommitted working tree.
**Audit status:** partial (single frontend workspace) · **Independent review:** spec and standards reviews completed; two verified findings fixed and narrowly re-reviewed.

## Purpose and constraints
A lead-oriented dental-clinic homepage for Oraldenti in Barranquilla. Last confirmed with owner: 2026-10-17. Owner requires Astro with reusable React sections, the real logo and three supplied photos rotating every seven seconds without carousel controls. No deployment, commit, remote publishing or live email submission authorized.

## Containers
| Container | Technology | Responsibility | Data |
|---|---|---|---|
| Static site | Astro 7, React 19, TypeScript strict | Routes, section composition, client carousel and appointment draft | Local content modules and image/font assets |
| Browser email application | mailto protocol | User reviews and sends an appointment request | Draft only; website does not persist or send it |

## Modules and dependency direction
Pages → React sections → shared UI. Content modules supply typed props; section components do not import page content. Astro owns the document shell and slots. CSS modules own section layout; tokens/global CSS own typography, palette and base controls.

- HomepageHero hydrates at load and owns the client carousel; its accessible carousel region contains only images.
- AppointmentForm hydrates when visible. Inputs and submit are disabled in SSR until handlers are mounted. A noscript fallback exposes the real email.
- Services use native details/summary, functioning without client JavaScript.
- src/content/services.ts owns all nine specialty groups and87 source procedure entries; clinic.ts supplies the same catalog to both accordions and appointment options. Implantology has no invented sublist.
- Contact links use tel, mailto and a Google Maps address search. Publications link to the existing institutional page.
- Fonts are local variable-font dependencies; no remote font requests.

## Main flows
1. Visitor reads services and follows a CTA to #contacto.
2. Form validates name, phone, email and selected service; creates an encoded mailto draft. User explicitly opens the mail application and sends it. No request is stored or sent by the website.
3. Carousel advances at 7000 ms, including while hovered; reduced-motion preference prevents automatic changes.

## Evidence and known traps
- Source scans and design notes: artifacts/reference-*.json, reference-desktop.png and homepage-design.md.
- Original site disagrees on telephone: header 6053008989; repeated footer and contact page 6053491774. Current content uses the latter with Colombian prefix. Owner must confirm contact details before publishing.
- Stop development before Astro check/build/verify. Those commands were observed to overwrite the dev dependency cache with a production React runtime, producing _jsxDEV is not a function. Restart development after static checks, then run browser tests.
- Development server: http://localhost:4321. Astro may background agent-started servers; inspect/stop with npx astro dev status/stop.
- No production host, backend, CMS, analytics or database configured.

## Verification
npm run verify passes lint, formatting, Astro/TypeScript and static production build. Twelve Playwright regressions cover carousel behavior, contact links, service keyboard interaction, email draft validation, mobile navigation/overflow, no-JavaScript form safety and tablet hero fit. Desktop, mobile and tablet screenshots saved under artifacts. These checks do not establish full accessibility conformance or actual email delivery.
