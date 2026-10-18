# Demo manager MVP

Owner: dav033. Approved in conversation on 2026-10-18: independent Next.js repository, shadcn/ui and React Bits, GitHub account connection, repository selection, demo expiry and parent-owned responsive preview. Netlify is the deployment target.

## Scope

- One authenticated owner can list repositories from their GitHub account and create a demo from a selected branch.
- The parent repository runs a GitHub Actions workflow to build a static child repository. The child does not contain the viewer or expiry logic.
- The owner configures name, slug, repository, build settings, duration; can rebuild, extend, pause, resume and copy the public link.
- GitHub Actions uploads an immutable ZIP to private parent storage using a scoped expiring token. Local filesystem storage is supported for development; Netlify Blobs is used in production.
- The public viewer provides animated desktop/tablet/large-phone/small-phone sizes. Both the viewer and every asset request check enabled status and expiration on the server without CDN caching.
- Static HTML/CSS/JS builds only in this MVP (Astro, Vite, Next static export). Server-rendered child applications are not supported.
- Existing Oraldenti is stripped of its own demo wrapper.

## Acceptance

1. Unauthorized visitors cannot list repositories, read demo configuration, mutate demos or upload artifacts.
2. The authenticated owner sees dav033's actual GitHub repositories, with an explicit error when GitHub is unavailable.
3. Creating a demo dispatches a build in the parent GitHub repository; its state is visible in the dashboard.
4. An active demo can render static files and navigate between pages, including root-relative assets, inside a sandboxed iframe.
5. Expired/paused demos return HTTP 410 for both direct content and viewer requests. An already-open viewer stops displaying content when it expires or is paused.
6. Invalid/oversized/unsafe ZIPs and expired/stale upload tokens are rejected; old builds cannot overwrite newer artifacts.
7. New app passes lint, typecheck, meaningful domain/integration checks and production build; mobile/desktop preview is checked in a browser.

## Constraints

- No child build executes in the admin server process.
- No GitHub or Netlify token appears in client props, browser responses, logs or committed files.
- Each shared demo requires its own unguessable revocable bearer token on the viewer and every asset route. Token rotation invalidates prior links. The token controls link possession, not lead identity. Admin routes require an owner session. Search engines are told not to index demos.
- Limits: 4 MiB ZIP upload, 30 MiB expanded, 1,500 entries. Supported npm-lockfile projects, configurable build script and static output directory.

## Execution

1. Scaffold Next.js/shadcn/React Bits and migrate the wrapper out of Oraldenti.
2. Implement authenticated owner access, GitHub repository listing, persistence and demo lifecycle.
3. Implement private artifact ingestion, checked content gateway, isolated parent viewer and GitHub Actions build workflow.
4. Verify locally, publish the private parent repository and configure authorized hosting; report any external-account restriction with actual evidence.
