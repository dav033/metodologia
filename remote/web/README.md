# Flow Remote web

Mobile-first Next.js app scaffold for the remote Flow control panel. The app uses local Manrope and JetBrains Mono
fonts, Catppuccin Mocha CSS tokens, and a static PWA manifest. No external font or asset URL is required at build time.

## Local development

Use Node.js 22 or newer and install the exact versions recorded in `package-lock.json`:

```sh
npm ci
npm run mock
```

In a second terminal, run `npm run dev`. The `/api/:path*` rewrite targets the mock gateway at
`http://127.0.0.1:8790` by default. Set `FLOW_GATEWAY_ORIGIN` to the gateway origin for a deployed environment.
The mock serves `GET /api/state` from `mocks/fixtures/snapshot.json` and returns `404` for other routes; it is local
development data and is not included in production code paths.

## Verification

`npm run verify` runs ESLint, strict TypeScript checking, mock gateway tests and a production Next.js build. The build
uses bundled local fonts and static assets and does not fetch network resources.
