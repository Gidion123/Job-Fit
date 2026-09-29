"""Budget guard: cap US$15, hard stop at US$14 (DECISIONS D-019)."""
from __future__ import annotations

from dataclasses import dataclass

from jobfit.llm.ledger import UsageLedger


class BudgetExceeded(RuntimeError):
    pass


@dataclass
class BudgetGuard:
    ledger: UsageLedger
    cap_usd: float = 15.0
    hard_stop_usd: float = 14.0
    warn_ratio: float = 0.8  # warn at 80% of the hard stop

    def spent(self) -> float:
        return self.ledger.total_spent()

    def check(self, estimated_cost_usd: float) -> None:
        """Raise before the call if it could push spending past the hard stop."""
        if self.hard_stop_usd > self.cap_usd:
            raise ValueError("hard stop must not be above the cap")
        projected = self.spent() + max(0.0, estimated_cost_usd)
        if projected > self.hard_stop_usd:
            raise BudgetExceeded(
                f"Projected spend US${projected:.4f} is above the hard stop US${self.hard_stop_usd:.2f}"
            )

    def should_warn(self) -> bool:
        return self.spent() >= self.warn_ratio * self.hard_stop_usd
