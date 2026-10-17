from dataclasses import replace

from bt_scheduler_recovery import RecoveryCase


def case(**changes):
    base = RecoveryCase("run-1", "plan-1", 1, "a" * 64, "T-001", "A-001", 1, "execution_failed",
                        technical_cause="connection_lost", confidence="confirmed", evidence_refs=("ledger:" + "b" * 64,),
                        handoff_sha="c" * 64, execution_state="failed", current=True, identity_verified=True,
                        transient_confirmed=True, max_attempts=3, failure_at=100, now=101)
    return replace(base, **changes)
