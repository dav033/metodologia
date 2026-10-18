# oraldenti — Summary

_Rewritten (not appended) whenever the state changes. Keep it under ~60 lines._

## Purpose
A lead-oriented dental-clinic homepage for Oraldenti in Barranquilla, built with Astro and reusable React sections. David authorized a premium redesign following frontend-design and the sections/content of the existing Wix site.
Last confirmed with owner: 2026-10-17.

## Current state
Premium homepage implemented at `/home/david/dev/oraldenti`: original logo and photo carousel, about, nine service accordions with all87 original procedure entries, smile gallery, appointment request, location and institutional-publication link. Local Bricolage Grotesque/Manrope fonts; original cyan #00b9e8 complements white/lilac and violet. All static checks and fourteen browser tests pass. No commits or remote publishing.

## Active focus
- Ready for owner visual review at http://localhost:4321. Screenshots, source scans and design/review evidence are in artifacts.
- Hero reduced to1200px maximum width and593px desktop height, with less vertical padding on mobile, per owner feedback. Typography and autoplay preserved.
- Primary buttons now use deeper blue #006f8c with white text, darkening to #005a73 on hover, per owner contrast feedback. Measured ratios5.75 and7.75 respectively.

## Top pending (see PENDING.md)
- Confirm current contact data before publishing: old source header disagrees with its contact page/footer. Current phone +57 605 349 1774; email info@oraldenti.com.
- A separately authorized backend/provider is needed if the owner wants direct lead submission. Current form explicitly prepares a draft for the visitor to send in their email application.

## Recent decisions (see DECISIONS.md)
- Use Astro with the official React integration; static output and selective hydration.
- Carousel shows only images, rotating automatically every seven seconds even while hovered, with no arrows, dots or playback controls, per David's request. Reduced-motion preferences keep the current image static.

## Known issues
- Fourteen Playwright regressions pass, including complete service counts/examples at desktop and mobile widths. Original-source comparison independently checks all87 entries. Previous spec/standards corrections for tablet clipping and no-JavaScript form safety remain covered.
- Do not build while dev runs: a production React dependency cache was observed to break development hydration; restarting dev restored it. See README.

_Last updated: 2026-10-17_
