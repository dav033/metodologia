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
`http://127.0.0.1:8790` by default. Set `GATEWAY_ORIGIN` to the gateway origin for a deployed environment.
The mock implements the gateway's session, snapshot, `/api/remote/v1/stream` (named `event`/`resync` frames), read
models and command endpoints. Its payloads are `remote/contract/fixtures/*.json`, validated against the contract.

## Contract and shared assets

`src/contract.generated.ts` holds the wire types and constants generated from the Pydantic models
(`skill/scripts/bt_contracts/remote.py`); regenerate it with `uv run python -m bt_contracts.schemas` from
`skill/scripts`, never by hand. `src/app/remote-contract.ts` holds the runtime checks typed by it.
`public/flow-core.js` is a build copy of `skill/assets/flow-core.js`: `npm run dev`/`build` refresh it
(`npm run sync:flow-core`) and `npm run check:flow-core` fails when it drifted.

For GitHub OAuth, configure the gateway's `GITHUB_CALLBACK_URL` to the **public frontend origin** at
`/api/auth/callback` (for example, `https://flow.example.com/api/auth/callback`). The browser must start login and
return from GitHub through the same frontend host so its state cookie reaches the callback and the session cookie
remains available to the `/api/*` rewrite. Do not point GitHub directly at the gateway/API hostname.

## Verification

`npm run verify` runs ESLint, strict TypeScript checking, mock gateway and headless Chromium OAuth tests, and a production Next.js build. The build
uses bundled local fonts and static assets and does not fetch network resources.
