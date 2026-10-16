# escritorio — Pending

_Sorted automatically by `bitacora.py pending` (urgency high → low, then complexity S → L: quick urgent wins first).
One line per item: `P-NNN · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`.
Move items between sections as they change; closed items keep 14 days in "Recently closed", then go to the
month summary._

## Open
- P-003 · Move Google Drive MCP OAuth audience from Testing to Production · urgency: high · complexity: M · added 2026-10-16 · REQ-004
  The genuine homepage and privacy policy are live at https://local-file-manager-three.vercel.app/ and /privacy.html (HTTP 200). Google requires these URLs on a verified domain David controls, so the free `vercel.app` hostname does not finish this requirement. A DuckDNS subdomain is being evaluated because its API supports DNS TXT records; no DuckDNS account or domain has been created. Its GitHub sign-in may disclose name, username, email, profile picture, login IP, and DNS-service data under DuckDNS's privacy policy. Google OAuth remains External/Testing and its refresh token expires after seven days. The isolated Google Cloud sign-in currently returns “This browser or app may not be secure.”
- P-001 · Confirm Alt+1/Alt+2 tab navigation in Firefox during normal use · urgency: low · complexity: S · added 2026-10-11 · REQ-001
  The Hyprland binds are loaded and inspectable. Temporary Firefox keypress checks did not produce a reliable end-to-end result; verify next time Firefox is used.
- P-002 · Install the signed grave-key image saver in Firefox · urgency: low · complexity: M · added 2026-10-11 · desktop-shortcuts
  The extension package is at `~/.local/share/firefox-image-saver/firefox-image-saver-1.0.0.zip`; the receiver and native messaging host are configured. Mozilla two-step authentication is active; recovery codes are stored at `~/.local/share/mozilla-account/recovery-codes.txt` with mode 600. The AMO agreement was accepted and the developer display name is `dav0322`. In the hidden cloned profile, forced the GTK file picker (`widget.use-xdg-desktop-portal.file-picker=0`), submitted the package as “On your own”, and AMO validation completed with 0 errors and 1 warning. Version 1.0.0 is now `Awaiting Review`; AMO says signing is pending and will email when the XPI is ready. Recheck AMO after its signing queue completes, save the signed XPI locally, then install manually in personal Firefox. Never automate the personal profile.

## Blocked
_None_

## Recently closed
_None_
