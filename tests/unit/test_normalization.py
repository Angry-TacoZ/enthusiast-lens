from decimal import Decimal

import pytest

from enthusiast_lens.deterministic import (
    canonicalize_string,
    case_insensitive_equal,
    clean_whitespace,
    normalize_unit,
    parse_numeric,
)


def test_whitespace_and_case_normalization_is_stable() -> None:
    assert clean_whitespace("  Front\n wheel\t drive  ") == "Front wheel drive"
    assert canonicalize_string("  STRASSE  ") == "strasse"
    assert canonicalize_string("  Straße  ") == "strasse"
    assert case_insensitive_equal("  All-Wheel Drive ", "all-wheel   drive")


def test_missing_and_blank_values_remain_missing() -> None:
    assert clean_whitespace(None) is None
    assert clean_whitespace(" \t\n ") is None
    assert canonicalize_string(None) is None
    assert parse_numeric(None) is None
    assert parse_numeric("  ") is None


def test_unit_and_numeric_normalization_are_explicit() -> None:
    assert normalize_unit(" Pounds ") == "lb"
    assert normalize_unit("widgets") == "widgets"
    assert parse_numeric(" 3525.5 ") == Decimal("3525.5")
    assert parse_numeric(300) == Decimal("300")


def test_normalization_does_not_infer_or_parse_prose() -> None:
    assert canonicalize_string("Mystery drivetrain") == "mystery drivetrain"
    with pytest.raises(ValueError, match="structured number"):
        parse_numeric("300 horsepower")


@pytest.mark.parametrize("value", [True, float("inf"), float("nan")])
def test_unsafe_numeric_inputs_are_rejected(value: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        parse_numeric(value)
