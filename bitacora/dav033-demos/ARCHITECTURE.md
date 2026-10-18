# Architecture

Next.js App Router is the single parent application. shadcn/ui (Base UI) provides controls; React Bits AnimatedContent provides motion. One owner signs in with a strong configured password and an eight-hour signed HttpOnly, SameSite=Strict session. GitHub uses the authorized owner's server-side token, not multi-user OAuth.

## Flow

1. The owner selects a repository, branch, static framework/output settings and duration.
2. The private parent repository runs a GitHub Actions build. Checkout does not persist credentials. Child build subprocesses get a minimal environment without parent GitHub or Netlify credentials. Source code never builds inside a web request.
3. Static output uses a stable `/content/<slug>/` base. A per-generation signed token authorizes one artifact upload for two hours.
4. Private storage holds demo metadata, immutable generations and ZIPs. Production uses Netlify Blobs with strong reads and ETag conditional mutations. Development uses `.data` and exclusive filesystem locks. Uploads atomically claim a generation; artifact writes are create-only.
5. Owner links are `/d/<slug>?token=<bearer>`. The bearer is HMAC-derived from the demo's rotation key and a server secret. Both the viewer and `/content/<slug>/<token>/*` gateway verify the token, enabled state and deadline on every request.
6. The parent owns animated device controls and an iframe with an opaque sandbox origin. The content gateway also applies a sandbox CSP to directly opened content, disables connections/forms/service workers, and rebases static assets and Astro hydration payloads under the tokenized path. Module CORS does not expose the owner's origin or session.
7. An open viewer checks every 15 seconds, on visibility changes and at its authoritative deadline. Pause/rotation can hide already-loaded content within 15 seconds; new page/asset requests are denied immediately. Content already downloaded cannot be erased remotely.

## Boundaries

`app/` composes public feature APIs. `features/demos` owns lifecycle and imports, `features/artifacts` owns archive ingestion/serving, `features/preview` owns the viewer and `features/auth` owns login presentation. `shared/lib` contains signing, auth, GitHub and storage; `shared/ui` contains shadcn atoms and React Bits source.

## Supported builds

MVP: npm-lockfile static projects (Astro/Vite or a custom export consuming `DEMO_BASE_PATH`). SSR children, backend APIs, service workers and arbitrary root-relative JavaScript fetch/navigation are not supported. Custom exports must respect their configured base. Nested static HTML and relative assets are preserved.

ZIP limits: 4 MiB compressed, 30 MiB expanded, 1,500 entries. Paths, duplicates, symlinks, compression types, declared sizes and checksums are validated before publication.

A shared URL is a bearer credential: anyone possessing it can open the demo while active. No lead identity verification is claimed. Referrers and indexing are disabled; hosting request logs may still include URLs. Rotation invalidates the old link. Parent credentials and metadata never ship inside child artifacts.

## Workspace

Parent repository: dav033/dav033-demos (Next.js on Netlify). Example child: dav033/oraldenti (Astro static website). Child owns its content and interactions; parent owns build delivery, access and device controls. Both private repositories are registered in this workspace.
