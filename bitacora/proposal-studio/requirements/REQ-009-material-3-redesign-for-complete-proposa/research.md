---
tipo: research
proyecto: proposal-studio
fecha: 2026-10-11
tags: [material-3, forms, usability, accessibility]
---

# Research — Material 3, forms and UX

## Design direction for this product

Material 3 is useful here as a set of interaction/layout patterns, not as a mandate to copy Google colors or add a framework. Preserve the globally required Catppuccin Mocha palette while adopting consistent surfaces, adaptive navigation, visible field labels, calm state transitions, and clear action/status feedback.

## Evidence-based guidance

1. **Responsive information hierarchy:** Material layouts should be predictable, consistent, and responsive. On compact widths, show a single content level and keep margins/columns adaptive; navigation should change form with available width. Avoid compressing the desktop shell into tiny labels.
2. **Fields and validation:** A text field needs a persistent visible label. Helper text should be short and associated with the field; an error should replace helper text, explain a fix, and be paired with clear state beyond color. Use specific errors and preserve entered values.
3. **Accessible form structure:** W3C recommends programmatic labels, fieldsets/legends for related controls, instructions before they are needed, and validation that identifies the issue. Large groups should not become one undifferentiated field wall.
4. **Error recovery:** GOV.UK's error summary pattern places a concise summary before the form, focuses it after submit, and links each message to the matching answer. Keep the local field error text consistent with the summary.
5. **Motion:** Material's guidance says frequent transitions must not make people wait. Use movement to clarify a state change, keep it brief, and honor reduced-motion preference; do not use motion as decoration.
6. **Actions:** Give one clear primary action per context; keep save as a safe, repeatable task and give irreversible actions explicit confirmation. Label actions with verbs that explain their outcome.

## References (official/primary)

- [Material Design 3 — Layout](https://m2.material.io/guidelines/layout/units-measurements.html): predictable, consistent, responsive layout and adapting margins/columns.
- [Android Developers — Material 3 layout and navigation patterns](https://developer.android.com/design/ui/mobile/guides/layout-and-content/layout-and-nav-patterns): adaptive navigation, persistent destinations, and action placement by importance.
- [Material Design — Text fields](https://m2.material.io/components/text-fields.html): labels, helper text, error text, and replacing helper with actionable error text.
- [Material Design 3 — Motion](https://m3.material.io/styles/motion/overview): current motion principles (site is JavaScript-rendered; its search-indexed guidance describes a physics-based motion system).
- [W3C WAI — Labels](https://www.w3.org/WAI/tutorials/forms/labels/): labels must identify controls and be programmatically associated.
- [W3C WAI — Instructions](https://www.w3.org/WAI/tutorials/forms/instructions/): provide concise overall and inline instructions; connect field help with `aria-describedby`.
- [W3C WAI — Validation](https://www.w3.org/WAI/tutorials/forms/validation/): validate with actionable messages; client validation does not replace server validation.
- [GOV.UK — Text input](https://design-system.service.gov.uk/components/text-input/): short visible labels above controls, do not rely on placeholder text, and keep hints short.
- [GOV.UK — Error summary](https://design-system.service.gov.uk/components/error-summary/): move focus to the summary, link each error to its field, and use matching concise local messages.

## Application to REQ-009

- One shared app shell for all protected routes; adaptive sidebar/compact navigation and a persistent way back to proposals.
- Page title, concise task description, one visually dominant primary action; secondary and destructive actions are visually distinct.
- Group form work in task order: identify business/current website, capture, prototype/import, matched additional pages, preview, then publish/share.
- Keep visible labels above every input, avoid placeholder-as-label, provide one-line format/size hints, and associate hints/errors programmatically.
- On failed submit, preserve data, focus an error summary, link to first affected fields, show specific inline errors, and keep network failures distinct from invalid values.
- During mutations, prevent duplicate requests, expose progress, and report partial success (e.g. saved draft but capture upload failed) with a clear retry path.
- Keep the public proposal focused on the comparison and meaningful next action, with keyboard/touch control and reduced motion.
