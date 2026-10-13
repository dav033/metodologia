# proposal-studio — Pending

_Sorted automatically by `bitacora.py pending` (urgency high → low, then complexity S → L: quick urgent wins first).
One line per item: `P-NNN · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`.
Move items between sections as they change; closed items keep 14 days in "Recently closed", then go to the
month summary._

## Open
- P-010 · Reauthenticate Claude Code and verify a proposal-studio MCP tool call · urgency: high · complexity: S · added 2026-10-11 · REQ-007
  - `claude mcp list` reports the production endpoint connected, but `claude -p` could not invoke a tool because the Claude OAuth session expired. After `claude auth login`, retry a read-only call; no MCP token change is needed.
- P-011 · Import and share the Oraldenti proposal prototype · urgency: med · complexity: S · added 2026-10-11 · production proposal setup
  - David is generating the prototype code. When he provides its GitHub repository and built output path, import it, validate Inicio/Servicios/Contacto comparisons, publish, then create a temporary share link.
- P-007 · Add a custom domain after David purchases one · urgency: low · complexity: S · added 2026-10-10 · REQ-003
  - Optional future polish only. Current share URLs use `proposal-studio-orpin.vercel.app`; this does not block the simple proposal flow.

## Blocked
_None_

## Recently closed
- P-009 · Restore local Google OAuth credentials and verify login · urgency: high · complexity: S · added 2026-10-11 · local auth troubleshooting
  - Closed on 2026-10-11. Created a separate localhost-only Google OAuth client so production credentials remain untouched. Saved its credentials only in ignored `.env.development.local` (mode 600); local sign-in completed and `/admin` loaded at `http://localhost:4321`. Local development uses the production database as requested; no migrations were run.
- P-006 · Configure sender domain for prospect notifications · urgency: med · complexity: M · added 2026-10-10 · REQ-003
  - Closed by David's 2026-10-11 scope decision: Proposal Studio will not send email.
- P-008 · Import and preview the static fixture from the authorized repository · urgency: med · complexity: S · added 2026-10-10 · REQ-003
  - Verified in production on 2026-10-11. Imported `proposal-studio-import-demo` from branch `proposal-studio/p008-import-smoke`, pinned to commit `cb10529f6642a980f967e13d3cc0d7f160158508`. The integration preview rendered the imported Clínica Horizonte page in its sandboxed iframe and the proposal editor displayed the imported prototype in its comparison preview. The clearly labeled QA draft was not published and had no email recipient; archived it afterward (DELETE returned 200, `{"archived":true}`), and the admin overview returned to 0 drafts / 0 proposals.
- P-004 · Expand service/API security and workflow tests to the approved REQ-003 matrix · urgency: high · complexity: L · added 2026-10-10 · REQ-003
  - Expanded the serial Chromium suite to 8 tests: authenticated proposal lifecycle and revoke failure/retry, unavailable Resend state, mobile admin layout, prototype storage/top-navigation isolation, pointer/keyboard comparison, anonymous access, and logout failure/success. Unit/integration coverage remains 25 Vitest files / 83 tests. The later P-008 session completed a real production import and preview, then archived its QA draft.
- P-003 · Create GitHub App and install it on selected prototype repositories · urgency: high · complexity: M · added 2026-10-10 · REQ-003
  - Registered GitHub App `Creative Tech Proposal Studio` (`creative-tech-proposal-studio`, ID `5268438`) and installed it only on `dav033/maros-construction-web`. Granted permissions are repository metadata and contents read-only. Production callback returned successfully; Proposal Studio shows `Conectado · @dav033` and the repository selector exposes exactly that repository. Its default branch has no built static output with `index.html`, so an actual import remains unverified until an appropriate built prototype folder exists.
- P-005 · Persist audit events for security-sensitive admin mutations · urgency: med · complexity: M · added 2026-10-10 · REQ-003
  - Proposal create/update/publish/archive, share create/revoke, and GitHub connect/import/disconnect actions write minimal events in the same database transaction as their mutation.
- P-001 · Approved REQ-003 scope and Vercel architecture · urgency: high · complexity: L · added 2026-10-10 · REQ-003
- P-012 · Apply review findings for the client simulator, then editor usability pass (checklist, sticky actions, collapsible sections) · urgency: high · complexity: M · added 2026-10-13 · requirement from owner

## Notes
One line per item: `<ID> · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
One line per item: `P-xxx · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
One line per item: `<id> · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Each pending item has one stable ID; indented lines hold its details.
