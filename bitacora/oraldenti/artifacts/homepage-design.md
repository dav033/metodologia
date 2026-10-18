# Oraldenti homepage design

## Scope and acceptance
Owner requested a premium lead-oriented homepage using frontend-design and the sections of https://juanmarquezr.wixsite.com/oraldenti. Implement directly in the existing Astro/React site. Preserve supplied logo and three-image autoplay at 7000 ms without controls. Reuse sections with typed props. No publishing, sending leads, invented patient outcomes or new backend.

Acceptance: existing carousel regressions pass; navigation, service details and contact request composition work on desktop and mobile; `npm run verify` and browser tests pass; inspect screenshots and browser errors.

## Source inventory
Scanned home, about, services, contact and publications using isolated Chromium. Evidence: reference-scan.json, reference-{about,services,contact,testimonials}.json and reference-desktop.png.

Sections: hero, about, services, smile gallery, appointment request, location; institutional publications remain accessible from the footer. Eight specialties listed on the home page, plus oral rehabilitation on services. Gallery photographs are illustrative; never label as clinical results or patients.

Contact: info@oraldenti.com; Centro Nelmar, Carrera 46 #53-34, piso 2, locales 7 y 8, Barranquilla. Footer +57 6053491774 agrees with contact page legacy (5)3491774; header 6053008989 differs. Use the repeated contact number, record need for owner confirmation before production. No WhatsApp inferred.

## First pass
Palette: porcelain #fcfcff, ink #29233f, iris #6650ab, pale lilac #f0edf8, muted plum #6e687e, pale aqua #dcebea. Local Bricolage Grotesque for display headings, Manrope for body and controls. Sentence case. Left-aligned content, 65-character body measure, 1200 px content width.

Option A: split hero, left copy and right image; familiar and would crop the supplied wide portraits.

    [logo       navigation       appointment]
    [copy              | portrait]
    [three identical service cards]

Option B: wide image with copy on its naturally empty right half; photo left and a single rounded lower corner echoing a smile; sections alternate generous editorial layouts with compact service rows.

    [logo       navigation       appointment]
    [portrait        headline + action]
    [location       telephone       email]
    [about photo     purpose and care]
    [services intro | expandable specialties]
    [asymmetric smile image strip]
    [appointment form | address and directions]
    [footer + institutional publications]

## Review before build
Choose B: the supplied photos already contain negative space on the right. Removed the identical service-card grid from A because it would turn a clinical service choice into template decoration. Use expandable rows so visitors can understand each specialty and select it for the appointment request. One visual signature: a soft smile-like lower hero corner; no gradients, decorative numbering, floating badges, invented stats or repeated entrance animations. The retained carousel is the only unsolicited motion.

White/lilac clinical palette and curved type derive from the real Oraldenti logo rather than the owner's provisional desktop theme. Keep the logo intact. CTA text stays 'Solicitar una cita' across the page. Expose phone, email and directions without a fake map pin. Form prepares an email draft, explicitly explains that the user must send it, and never reports a server submission. No third-party email/form provider introduced.

## Verification notes
Implemented the revised layout. Removed the floating about-photo caption in the final critique because it repeated the adjacent copy without helping navigation. Retained supplied photos without labeling them as patient outcomes. Preloaded visible gallery images for screenshot inspection; lazy-hidden carousel slides are exercised by the autoplay tests.

Measured tablet clipping at 721px and 768px in the first pass. Extended the stacked hero layout through 900px and added a regression at 721/768/820/1024px. Independent standards review identified native GET submission before form hydration; disabled fieldset/submit until mount, added noscript email fallback and a JavaScript-disabled browser regression. Both findings reproduced in red tests before correction and were approved on a bounded re-review.

Final checks: npm run verify passes, 27 files checked with zero errors/warnings/hints; production build creates one page. Twelve browser regressions pass in 7.1 seconds. Final desktop/mobile/tablet screenshots saved as homepage-*-final.png, no browser page errors. Solid text/background contrast measurements: ink/porcelain14.58, muted/porcelain5.20, muted/lilac4.61, white/iris6.36, iris/lilac5.51, input placeholder/white4.57. These samples and keyboard tests do not certify full accessibility conformance.
