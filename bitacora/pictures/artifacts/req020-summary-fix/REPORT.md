# REQ-020 summary lifecycle repair

## Problem and requirement

Owner asked to fix the two LIVE summary failures. SPEC R11 requires a summary when required facts are complete; its correction edge case requires a regenerated summary and renewed approval.

- Original M1 persisted 9/10 facts, omitting venueType even though the customer explicitly gave the venue type and name. The model received a progress count but not missing field names; the schema did not distinguish venueType from venueName.
- Original M1/M2 correction assertions required summary=null, contradicting the required regenerated summary.
- After field/schema correction, real Gemini saved all facts and proposed a summary but a redundant follow-up model request timed out after that successful write.

## Repair

- Explain venueType versus venueName in tool schemas and the prompt; include the server's missing required field names in model context.
- When a completed provider turn leaves complete structured facts without a summary, generate it through the existing propose_summary domain tool. No model-authored summary data or duplicate summary formatter.
- Complete successful summary proposal/approval operations without a redundant provider round trip. Keep first-look photo turns with the provider so their visual description is retained. Preserve stable assistant IDs, domain tool receipts and error behavior.
- Correct M1/M2 assertions to require a regenerated version containing the corrected theme and approval=null. Old summary versions cannot satisfy these assertions.
- Add four deterministic regression tests (omitted tool, incomplete fields, regenerated version/new approval, no redundant provider request), and wire them plus the earlier deployed-runner tests into the regular asesor:test command.

## Verification

- Regression tests reproduced red before each relevant repair, then green.
- npm run asesor:test: 59 passed, 0 failures (includes four summary and three deployed-runner regressions).
- Existing agent tests plus summary regressions: 12 passed.
- Full repository lint passed with existing warnings before the final orchestration edit; scoped final lint and standalone types are recorded in the day log.
- Final standalone TypeScript and scoped ESLint both exit 0 on the complete repair; whitespace checks pass.
- LIVE M1 on real Gemini/Supabase: PASS, 11 checks, including summary creation, correction/version, explicit approval, admin access and provider failure persistence.
- LIVE M2 on real Gemini/Supabase/Whisper: PASS, 4 grouped checks, including received photo bytes, actual voice transcription, regenerated/current approved brief and admin visibility.
- Both LIVE runs freshly passed workspace builds, production app build (including application types), and application startup.
- Full gate, phone acceptance and deployment of this repair were not performed.

## Delivery

Uncommitted branch fix/req020-summary-lifecycle in /home/david/.local/tmp/req020-live-coordinator, based on att-0087 snapshot 71a8f78400d437f09423cac1b51ca38120b8f6c7. The same worktree retains the earlier owner-authorized deployed-runner work. Summary patch: summary-fix.patch; redacted passing LIVE reports are alongside this file.

Active scheduler att-0088 was not edited, and no receipt was issued for a task whose snapshot does not contain this repair. Integrate onto the current accepted tree before final T14a/production acceptance; published advisor deployment and phone checks remain separate.

### Owner-authorized local integration
- Committed 915a75af07dd33151508cea3c871f7bae4ed8986 and fast-forwarded clean canonical branch feat/req-020-asesor-happia. Combined accepted att-0088 --check-results changes with summary/deployed corrections; unrelated metodologia changes were not committed.
- Independent antagonist: 2 major findings fixed (remote report incompatibility and argument-only SHA), 0 deferred, 0 dropped; single permitted re-review SOUND. D-064 records the versioned public release-identity and remote report contract.
- Current combined code: npm run asesor:test 63/63 PASS; standalone harness 10/10 PASS; scoped ESLint PASS; full production build including application types PASS; staged whitespace and commit secret scanner PASS. Earlier real LIVE M1/M2 passing reports remain valid evidence of that tested candidate only; no fresh manual receipt claimed for this commit. Full gate and deployed/phone acceptance still owed.
- Frozen r7 adds bounded T14.2a import/verification before T14a. Scheduler revise kept all 16 accepted tasks, reset only pending T14a/T15/T15b, added 1 task; active old T14a att-0089 cancelled as superseded. Owner/watcher running, T14.2a att-0090 running, no blockers. No active worktree edited and no push/deploy performed.
- Next: let T14.2a earn independent acceptance, then collect current-snapshot LIVE/deployed/phone evidence for final tasks. Product integration into the local branch is complete; scheduler acceptance remains in progress.
