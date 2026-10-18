# Tools

## Local
- Parent: /home/david/dev/dav033-demos; dev http://localhost:3000.
- Child: /home/david/dev/oraldenti.
- Ignored .env.local and .env.production.local contain environment references/credentials; never print their values.
- Verification: npm run verify; with dev running, npx playwright test. System Chromium: /usr/bin/chromium.

## GitHub
- Authenticated gh CLI: dav033, repo/read:org/gist/workflow scopes. Scope extension explicitly authorized by owner.
- Parent: https://github.com/dav033/dav033-demos (private), main.
- Child: https://github.com/dav033/oraldenti (private), main.
- Parent Actions secret DEMO_GITHUB_TOKEN is configured.
- Logs: gh run list --repo dav033/dav033-demos; gh run view RUN_ID --log-failed.

## Netlify
- Authenticated CLI account dav033; parent site d346ccf1-f426-4ad4-91e4-705279ca1da5.
- URL: https://dav033-demos.netlify.app.
- Parent local folder linked by ignored .netlify/state.json.
- Deploy: netlify deploy --build --prod.
- Env configured through CLI import; no secret values recorded here.
- Storage: private site-wide Netlify Blobs store demo-manager, strong reads and conditional mutations.
- Logs: netlify logs --since 10m --json.


- Netlify built_with_badge_enabled=false: disabled provider-injected branding on 2026-10-18 after it appeared twice in parent and embedded child. Setting takes effect on subsequent requests without redeployment.
