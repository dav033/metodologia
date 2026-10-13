---
status: draft
---
# escritorio — Week 2026-10 W3 (2026-10-12 → 2026-10-18)

_Rewritten at the end of each session that week. Set `status: final` once the week is over and rolled up._

## Highlights
- Replaced the pending Surfingkeys approach with a standalone Firefox image-saving extension prepared for Mozilla self-distribution signing.
- Improved the Rofi launcher contrast so light wallpapers no longer wash out its controls.

## Done
- Added the `Backquote` page hotkey, secure native token bridge, Firefox native messaging manifest, and loopback image receiver configuration. Ordinary Firefox downloads remain unchanged.
- Neutralized the unused Surfingkeys snippet and rotated the receiver token.
- Made Rofi's generated backgrounds opaque, raised secondary-label visibility, and enlarged launcher text in both dynamic and Catppuccin palettes.

## Decisions
- Keep the receiver token outside the Mozilla upload package; provide it to the fixed-ID extension through an allowlisted native messaging host.

## Not done / dropped
- Permanent personal Firefox installation awaits Mozilla signing and manual installation; agents must not automate the personal profile.

## Carried over to next week
- P-002: sign and install the custom Firefox image saver.
