"""Walk-forward, MDE printer, trial ledger, deflated Sharpe.

Refuses to run a test until n, σ, and MDE have been printed for the current spec.
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

MDE_Z = 2.8
MDE_RATIO_MAX = 0.5
TRIAL_BUDGET = 5
TRIAL_ALPHA = 0.01
EULER_GAMMA = 0.5772156649015329
DEFAULT_LEDGER = Path(__file__).resolve().parent.parent / "logs" / "trial_ledger.jsonl"


class HarnessGuardError(Exception):
    """Raised when a test is invoked before n, σ, and MDE are printed."""


class MdeGateError(Exception):
    """Raised when MDE > 0.5 × hypothesized effect. The book closes without a peek."""


class TrialBudgetError(Exception):
    """Raised when a sixth spec is registered for a book."""


class TrialStatus(StrEnum):
    REGISTERED = "registered"
    RUN = "run"
    ABANDONED = "abandoned"


@dataclass(frozen=True)
class Declaration:
    book_id: str
    spec_id: str
    n: float
    sigma: float
    hypothesized_effect: float
    clustering_haircut: float = 1.0
    unit: str = "bps"

    @property
    def n_effective(self) -> float:
        return self.n / self.clustering_haircut

    @property
    def mde(self) -> float:
        if self.n_effective <= 0:
            raise ValueError("n_effective must be > 0")
        return MDE_Z * self.sigma / math.sqrt(self.n_effective)

    @property
    def mde_ratio(self) -> float:
        if self.hypothesized_effect <= 0:
            raise ValueError("hypothesized_effect must be > 0")
        return self.mde / self.hypothesized_effect

    @property
    def clears_gate(self) -> bool:
        return self.mde_ratio <= MDE_RATIO_MAX


_DECLARATION: Declaration | None = None


@dataclass(frozen=True)
class Fold:
    train_index: tuple[int, ...]
    test_index: tuple[int, ...]


@dataclass(frozen=True)
class Trial:
    spec_id: str
    book_id: str
    hypothesis: str
    status: TrialStatus
    registered_at: str
    abandoned_reason: str | None = None


def reset() -> None:
    global _DECLARATION
    _DECLARATION = None


def print_mde(declaration: Declaration) -> Declaration:
    """Print n, σ, and MDE. Closes the book without a peek if the MDE gate fails."""
    global _DECLARATION
    print(
        f"MDE {declaration.book_id}/{declaration.spec_id}: "
        f"n={declaration.n:g} haircut={declaration.clustering_haircut:g} "
        f"n_eff={declaration.n_effective:g} sigma={declaration.sigma:g} {declaration.unit} "
        f"MDE={declaration.mde:.4g} hypothesized={declaration.hypothesized_effect:g} "
        f"ratio={declaration.mde_ratio:.3f}"
    )
    if not declaration.clears_gate:
        raise MdeGateError(
            f"{declaration.book_id} MDE {declaration.mde:.4g} > "
            f"{MDE_RATIO_MAX} × hypothesized {declaration.hypothesized_effect:g}"
        )
    _DECLARATION = declaration
    return declaration


def require_declared() -> Declaration:
    if _DECLARATION is None:
        raise HarnessGuardError("n, σ, and MDE must be printed before any test")
    return _DECLARATION


def run_declared[T](fn: Callable[[], T]) -> T:
    require_declared()
    return fn()


def purged_embargoed_splits(
    n_rows: int,
    *,
    n_folds: int,
    purge_size: int,
    embargo_size: int,
) -> list[Fold]:
    """Contiguous test folds. Train drops a purge window before the test block
    and an embargo window after it (López de Prado).
    """
    if n_folds < 2 or n_rows < n_folds:
        raise ValueError("need at least two folds and n_rows >= n_folds")
    fold_len = n_rows // n_folds
    folds: list[Fold] = []
    for k in range(n_folds):
        start = k * fold_len
        stop = n_rows if k == n_folds - 1 else (k + 1) * fold_len
        test = tuple(range(start, stop))
        train: list[int] = []
        for i in range(n_rows):
            if start <= i < stop:
                continue
            if i >= start - purge_size and i < start:
                continue
            if i >= stop and i < stop + embargo_size:
                continue
            train.append(i)
        folds.append(Fold(train_index=tuple(train), test_index=test))
    return folds


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_ppf(p: float) -> float:
    if p <= 0.0 or p >= 1.0:
        raise ValueError("p must be in (0, 1)")
    lo, hi = -16.0, 16.0
    for _ in range(80):
        mid = (lo + hi) / 2.0
        if _norm_cdf(mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def deflated_sharpe(
    sharpe: float,
    *,
    n_obs: int,
    n_trials: int,
) -> float:
    """Bailey & López de Prado (2014) deflated Sharpe as a probability in (0, 1)."""
    if n_obs < 3:
        raise ValueError("n_obs must be >= 3")
    sigma_sr = math.sqrt((1.0 + 0.5 * sharpe * sharpe) / (n_obs - 1))
    trials = max(int(n_trials), 1)
    if trials == 1:
        sr0 = 0.0
    else:
        sr0 = sigma_sr * (
            (1.0 - EULER_GAMMA) * _norm_ppf(1.0 - 1.0 / trials)
            + EULER_GAMMA * _norm_ppf(1.0 - 1.0 / (trials * math.e))
        )
    return _norm_cdf((sharpe - sr0) / sigma_sr)


@dataclass
class TrialLedger:
    path: Path = DEFAULT_LEDGER
    trials: list[Trial] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path = DEFAULT_LEDGER) -> TrialLedger:
        if not path.exists():
            return cls(path=path)
        trials: list[Trial] = []
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                raw = json.loads(line)
                trials.append(
                    Trial(
                        spec_id=raw["spec_id"],
                        book_id=raw["book_id"],
                        hypothesis=raw["hypothesis"],
                        status=TrialStatus(raw["status"]),
                        registered_at=raw["registered_at"],
                        abandoned_reason=raw.get("abandoned_reason"),
                    )
                )
        return cls(path=path, trials=trials)

    def _count(self, book_id: str) -> int:
        return sum(1 for trial in self.trials if trial.book_id == book_id)

    def register(self, *, spec_id: str, book_id: str, hypothesis: str) -> Trial:
        if self._count(book_id) >= TRIAL_BUDGET:
            raise TrialBudgetError(
                f"{book_id} already has {TRIAL_BUDGET} specs; a sixth needs a new window"
            )
        if any(trial.spec_id == spec_id for trial in self.trials):
            raise ValueError(f"spec_id {spec_id} already logged")
        trial = Trial(
            spec_id=spec_id,
            book_id=book_id,
            hypothesis=hypothesis,
            status=TrialStatus.REGISTERED,
            registered_at=datetime.now(tz=UTC).isoformat(timespec="seconds"),
        )
        self.trials.append(trial)
        self._append(trial)
        return trial

    def abandon(self, spec_id: str, reason: str) -> Trial:
        return self._update(spec_id, TrialStatus.ABANDONED, reason)

    def mark_run(self, spec_id: str) -> Trial:
        return self._update(spec_id, TrialStatus.RUN, None)

    def _update(self, spec_id: str, status: TrialStatus, reason: str | None) -> Trial:
        for i, trial in enumerate(self.trials):
            if trial.spec_id != spec_id:
                continue
            updated = Trial(
                spec_id=trial.spec_id,
                book_id=trial.book_id,
                hypothesis=trial.hypothesis,
                status=status,
                registered_at=trial.registered_at,
                abandoned_reason=reason,
            )
            self.trials[i] = updated
            self._rewrite()
            return updated
        raise KeyError(spec_id)

    def _append(self, trial: Trial) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(trial.__dict__) + "\n")

    def _rewrite(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as handle:
            for trial in self.trials:
                handle.write(json.dumps(trial.__dict__) + "\n")
