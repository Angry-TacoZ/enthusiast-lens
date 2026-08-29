from decimal import Decimal

import pytest

from enthusiast_lens.deterministic import (
    UnresolvedFactError,
    calculate_power_to_weight,
)
from enthusiast_lens.models import FactResult


def test_power_to_weight_uses_canonical_lb_per_hp_and_retains_inputs() -> None:
    result = calculate_power_to_weight(horsepower=300, curb_weight_lb=3600)

    assert result.horsepower == Decimal("300")
    assert result.curb_weight_lb == Decimal("3600")
    assert result.pounds_per_horsepower == Decimal("12.00")


def test_power_to_weight_rounds_half_up_to_two_decimals() -> None:
    result = calculate_power_to_weight(horsepower=275, curb_weight_lb=3525)

    assert result.pounds_per_horsepower == Decimal("12.82")


@pytest.mark.parametrize("horsepower", [0, -1, "-250"])
def test_power_to_weight_rejects_non_positive_horsepower(horsepower: int | str) -> None:
    with pytest.raises(ValueError, match="horsepower must be greater than zero"):
        calculate_power_to_weight(horsepower=horsepower, curb_weight_lb=3500)


@pytest.mark.parametrize("curb_weight", [0, -1, "-3500"])
def test_power_to_weight_rejects_non_positive_curb_weight(curb_weight: int | str) -> None:
    with pytest.raises(ValueError, match="curb_weight_lb must be greater than zero"):
        calculate_power_to_weight(horsepower=300, curb_weight_lb=curb_weight)


@pytest.mark.parametrize(
    "fact",
    [
        FactResult(field_id="engine.horsepower", state="unknown"),
        FactResult(
            field_id="engine.horsepower",
            state="conflicted",
            conflict_information="Synthetic sources disagree",
        ),
    ],
)
def test_unresolved_states_never_become_numeric_zero(fact: FactResult) -> None:
    with pytest.raises(UnresolvedFactError):
        calculate_power_to_weight(horsepower=fact, curb_weight_lb=3500)


def test_known_fact_can_enter_calculation_without_losing_state_safety() -> None:
    horsepower = FactResult(field_id="engine.horsepower", value=300, state="known")

    result = calculate_power_to_weight(horsepower=horsepower, curb_weight_lb=3600)

    assert result.pounds_per_horsepower == Decimal("12.00")
