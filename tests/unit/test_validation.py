import pytest

from enthusiast_lens.deterministic import (
    compare_exact,
    compare_with_aliases,
    compare_with_range,
    compare_with_tolerance,
    is_valid_field_id,
    validate_field_id,
)


def test_valid_dotted_field_id() -> None:
    field_id = "driver_assistance_and_highway_automation.adaptive_cruise_control"

    assert is_valid_field_id(field_id)
    assert validate_field_id(field_id) == field_id


@pytest.mark.parametrize(
    "field_id",
    [
        "",
        " ",
        "engine horsepower",
        "engine..horsepower",
        ".engine.horsepower",
        "engine.horsepower.",
        "Engine.horsepower",
        "engine.horse-power",
        "engine/horsepower",
        "horsepower",
    ],
)
def test_invalid_field_ids_are_rejected(field_id: str) -> None:
    assert not is_valid_field_id(field_id)
    with pytest.raises(ValueError, match="dotted path"):
        validate_field_id(field_id)


def test_exact_comparison_normalizes_text_only() -> None:
    assert compare_exact("  Premium   Audio ", "premium audio")
    assert not compare_exact("premium audio", "base audio")
    assert not compare_exact("300", 300)
    assert not compare_exact(True, 1)


def test_alias_comparison_accepts_only_explicit_equivalence() -> None:
    assert compare_with_aliases("FWD", "front-wheel drive")
    assert compare_with_aliases("DCT", "dual clutch transmission")
    assert not compare_with_aliases("AWD", "RWD")
    assert not compare_with_aliases("automatic", "DCT")


def test_tolerance_comparison_is_inclusive() -> None:
    assert compare_with_tolerance(actual=300.5, expected=300, tolerance=0.5)
    assert compare_with_tolerance(actual=299.5, expected=300, tolerance=0.5)
    assert not compare_with_tolerance(actual=300.51, expected=300, tolerance=0.5)


def test_tolerance_rejects_negative_rule() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        compare_with_tolerance(actual=300, expected=300, tolerance=-1)


def test_range_comparison_is_inclusive() -> None:
    assert compare_with_range(actual=4.5, minimum=4.0, maximum=5.0)
    assert compare_with_range(actual=4.0, minimum=4.0, maximum=5.0)
    assert compare_with_range(actual=5.0, minimum=4.0, maximum=5.0)
    assert not compare_with_range(actual=3.99, minimum=4.0, maximum=5.0)
    assert not compare_with_range(actual=5.01, minimum=4.0, maximum=5.0)


def test_range_rejects_reversed_rule() -> None:
    with pytest.raises(ValueError, match="minimum"):
        compare_with_range(actual=4.5, minimum=5.0, maximum=4.0)
