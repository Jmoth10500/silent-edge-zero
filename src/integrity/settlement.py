"""Result-status taxonomy and win-bet settlement with price-type tracking
(spec sections 5 and 6). Pure functions.

Key rule: a horse that FELL / PULLED UP / UNSEATED / was BROUGHT DOWN /
REFUSED / RAN OUT / was CARRIED OUT / DISQUALIFIED *ran and lost*. Only a
true NON_RUNNER or a VOID/ABANDONED race voids the stake. An unknown code
is never guessed: it stays UNKNOWN_PENDING and is not settled.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ResultStatus(str, Enum):
    WIN = "WIN"
    PLACED = "PLACED"
    FINISHED_UNPLACED = "FINISHED_UNPLACED"
    FELL = "FELL"
    PULLED_UP = "PULLED_UP"
    UNSEATED = "UNSEATED"
    REFUSED = "REFUSED"
    RAN_OUT = "RAN_OUT"
    BROUGHT_DOWN = "BROUGHT_DOWN"
    CARRIED_OUT = "CARRIED_OUT"
    DISQUALIFIED = "DISQUALIFIED"
    VOID = "VOID"
    NON_RUNNER = "NON_RUNNER"
    ABANDONED = "ABANDONED"
    UNKNOWN_PENDING = "UNKNOWN_PENDING"


_NOTE_MAP = {
    "PU": ResultStatus.PULLED_UP, "F": ResultStatus.FELL, "FELL": ResultStatus.FELL,
    "UR": ResultStatus.UNSEATED, "SU": ResultStatus.UNSEATED, "U": ResultStatus.UNSEATED,
    "REF": ResultStatus.REFUSED, "RR": ResultStatus.REFUSED,       # RR = refused to race: still a runner
    "RO": ResultStatus.RAN_OUT, "BD": ResultStatus.BROUGHT_DOWN, "CO": ResultStatus.CARRIED_OUT,
    "DSQ": ResultStatus.DISQUALIFIED,
    "NR": ResultStatus.NON_RUNNER, "WD": ResultStatus.NON_RUNNER,
    "VOID": ResultStatus.VOID, "ABD": ResultStatus.ABANDONED,
}

# Statuses that refund the stake.
VOIDING = {ResultStatus.NON_RUNNER, ResultStatus.VOID, ResultStatus.ABANDONED}
# Statuses that are a settled LOSS for a win bet (the horse ran).
LOSING_NON_FINISH = {ResultStatus.FELL, ResultStatus.PULLED_UP, ResultStatus.UNSEATED, ResultStatus.REFUSED,
                     ResultStatus.RAN_OUT, ResultStatus.BROUGHT_DOWN, ResultStatus.CARRIED_OUT,
                     ResultStatus.DISQUALIFIED}


def classify_result(finishing_position: Optional[int], result_note: Optional[str],
                    n_places: int = 0) -> ResultStatus:
    """(position, note) -> ResultStatus. `n_places` = each-way places for the
    field (0 = win-only); used only to split PLACED from FINISHED_UNPLACED."""
    if finishing_position is not None:
        if finishing_position == 1:
            return ResultStatus.WIN
        if n_places and finishing_position <= n_places:
            return ResultStatus.PLACED
        return ResultStatus.FINISHED_UNPLACED
    if result_note is None or not str(result_note).strip():
        return ResultStatus.UNKNOWN_PENDING
    return _NOTE_MAP.get(str(result_note).strip().upper(), ResultStatus.UNKNOWN_PENDING)


def is_settled(status: ResultStatus) -> bool:
    return status != ResultStatus.UNKNOWN_PENDING


def is_genuine_runner(status: ResultStatus) -> bool:
    """Ran in the race (won, finished, or failed to finish) — i.e. an
    observation for calibration/hit-rate. NOT non-runners/void/pending."""
    return status not in VOIDING and status != ResultStatus.UNKNOWN_PENDING


class PriceType(str, Enum):
    EXCHANGE_LOCK = "EXCHANGE_LOCK"
    EXCHANGE_OTHER = "EXCHANGE_OTHER"
    SP = "SP"
    NO_PRICE = "NO_PRICE"


@dataclass
class Settlement:
    status: ResultStatus
    price_type: PriceType
    price: Optional[float]
    stake: float
    gross_return: Optional[float]      # stake returned + winnings (0 when lost); None when unsettled
    commission: float
    net_return: Optional[float]        # net PROFIT/LOSS (-stake when lost, 0 when void)
    settled: bool


def settle_win_bet(stake: float, price: Optional[float], price_type: PriceType, status: ResultStatus,
                   commission_rate: float = 0.0) -> Settlement:
    """£`stake` straight win bet. `commission_rate` applies to exchange
    winnings only (SP is bookmaker-style, no commission)."""
    if status == ResultStatus.UNKNOWN_PENDING:
        return Settlement(status, price_type, price, stake, None, 0.0, None, False)
    if status in VOIDING:
        return Settlement(status, price_type, price, stake, stake, 0.0, 0.0, True)
    if price is None or price_type == PriceType.NO_PRICE:
        return Settlement(status, PriceType.NO_PRICE, None, stake, None, 0.0, None, False)
    if status == ResultStatus.WIN:
        winnings = stake * (price - 1.0)
        comm = winnings * commission_rate if price_type in (PriceType.EXCHANGE_LOCK, PriceType.EXCHANGE_OTHER) else 0.0
        return Settlement(status, price_type, price, stake, round(stake + winnings, 4), round(comm, 4),
                          round(winnings - comm, 4), True)
    return Settlement(status, price_type, price, stake, 0.0, 0.0, round(-stake, 4), True)
