The independent audit T18 rejected the accepted result of this task. Fix these confirmed findings and prove each one with a test that exercises the real entry point, not only the module in isolation:
- F4 (high): The ledger commits OK before validation/effects; invalid commands and interrupted commands can replay as successful without performing the requested action.
- F5 (high): Idempotency ignores effect-bearing request content and preconditions ignore revision/updatedAt, accepting changed requests and stale plan revisions.
