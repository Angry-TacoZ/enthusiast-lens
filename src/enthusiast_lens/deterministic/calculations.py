"""Deterministic calculations justified by the V1 product specification."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from enthusiast_lens.models import FactResult, FactState

from .normalization import NumericInput, parse_numeric


POWER_TO_WEIGHT_QUANTUM = Decimal("0.01")
US_TON_LB = Decimal("2000")


class UnresolvedFactError(ValueError):
    """Raised when a calculation receives a non-known runtime fact."""


@dataclass(frozen=True, slots=True)
class PowerToWeight:
    """Canonical US-market power-to-weight result in pounds per horsepower.

    The result retains normalized raw horsepower and curb-weight inputs and
    rounds pounds-per-horsepower to two decimals using ROUND_HALF_UP.
    """

    horsepower: Decimal
    curb_weight_lb: Decimal
    pounds_per_horsepower: Decimal


def _known_numeric(value: NumericInput | FactResult, name: str) -> Decimal:
    if isinstance(value, FactResult):
        if value.state is not FactState.KNOWN:
            raise UnresolvedFactError(
                f"{name} requires a known fact; received {value.state.value}"
            )
        raw_value = value.value
    else:
        raw_value = value

    parsed = parse_numeric(raw_value)
    if parsed is None:
        raise ValueError(f"{name} is required")
    return parsed


def calculate_power_to_weight(
    horsepower: NumericInput | FactResult,
    curb_weight_lb: NumericInput | FactResult,
) -> PowerToWeight:
    """Calculate canonical pounds per horsepower from known positive inputs."""

    horsepower_value = _known_numeric(horsepower, "horsepower")
    curb_weight_value = _known_numeric(curb_weight_lb, "curb_weight_lb")
    if horsepower_value <= 0:
        raise ValueError("horsepower must be greater than zero")
    if curb_weight_value <= 0:
        raise ValueError("curb_weight_lb must be greater than zero")

    ratio = (curb_weight_value / horsepower_value).quantize(
        POWER_TO_WEIGHT_QUANTUM,
        rounding=ROUND_HALF_UP,
    )
    return PowerToWeight(
        horsepower=horsepower_value,
        curb_weight_lb=curb_weight_value,
        pounds_per_horsepower=ratio,
    )


def calculate_power_to_weight_hp_per_us_ton(
    horsepower: NumericInput | FactResult,
    curb_weight_lb: NumericInput | FactResult,
) -> Decimal:
    """Calculate canonical horsepower per US ton from known inputs."""

    horsepower_value = _known_numeric(horsepower, "horsepower")
    curb_weight_value = _known_numeric(curb_weight_lb, "curb_weight_lb")
    if horsepower_value <= 0:
        raise ValueError("horsepower must be greater than zero")
    if curb_weight_value <= 0:
        raise ValueError("curb_weight_lb must be greater than zero")
    return (US_TON_LB * horsepower_value / curb_weight_value).quantize(
        POWER_TO_WEIGHT_QUANTUM,
        rounding=ROUND_HALF_UP,
    )
