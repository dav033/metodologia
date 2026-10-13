# Astro (landing pages, marketing sites)

Only what differs from defaults. General rules: `../engineering.md`.

## Layout
```
src/
  pages/                    routes; thin, compose sections
  layouts/                  base layout(s): <head>, SEO, analytics
  components/atoms|molecules|organisms/   Atomic Design (.astro components)
  content/                  content collections (markdown/MDX + zod schema) for copy, blog, FAQs
  styles/  assets/
```

## Defaults
- Static output by default; zero JS unless needed. Islands (`client:visible` / `client:idle`) only for genuinely
  interactive bits, in React if the team's other projects are React.
- Copy lives in content collections, not hardcoded across components — easy to edit and translate.
- Tailwind for styling.
- SEO: per-page title/description/OG image, sitemap, robots, canonical URLs, semantic HTML.
- Performance: `astro:assets` `<Image>` for every image (sizes, lazy loading, modern formats); Lighthouse ≥ 95.
- Accessibility: alt text, heading order, contrast, keyboard focus.
- Forms post to an endpoint/service (serverless function or the main API); validate with zod.

## Testing
Usually no unit tests. Build must pass with no warnings; check links; one Playwright smoke test if there's a
form or critical CTA.

## Verify
`npm run build` (+ `astro check`) and a Lighthouse run on the main pages.
