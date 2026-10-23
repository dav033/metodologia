"""Stable local-persistence errors shared by the M2 ledger stores."""


class DecisionLedgerError(RuntimeError):
    """Stable persistence error without filesystem or SQLite details."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(f"decision_ledger_{code}")
