# dav033-demos — Summary

## Purpose
Personal demo manager for dav033: import private/public GitHub repositories, configure validity, revoke/rotate access links and provide parent-owned responsive previews.
Last confirmed with owner: 2026-10-18.

## Current state
Independent Next.js application implemented with shadcn/ui and React Bits. Private GitHub parent and Oraldenti child repositories created; parent published at https://dav033-demos.netlify.app. Owner login and live GitHub repository listing verified in production. Private artifact gateway, signed per-demo tokens, rotation, pause/expiry and viewer behavior pass local checks. Production Oraldenti import/build/upload succeeded through GitHub Actions run 39100845720. Missing-token viewer requests return HTTP 410.

## Active focus
- Production administration uses dark theme; Oraldenti photographs optimized and rebuilt. Live access countdown published in the parent viewer.

## Recent decisions
- D-001: parent-owned private artifacts, server checks and opaque iframe; children contain no demo controls.
- User explicitly requested per-demo revocable access tokens.
- GitHub workflow scope was authorized by the owner through the device flow.

## Known issues
- Production timeout resolved: Next deduplicated fetch prevented SDK cancellation of missing-blob responses. Explicit request AbortSignal bypasses deduplication; transport uses no-store and an eight-second timeout.
- Static builds only in MVP; SSR child applications are not supported.

_Last updated: 2026-10-18_

