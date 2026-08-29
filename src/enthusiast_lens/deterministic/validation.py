"""Syntax validation and comparison primitives independent of benchmark data."""

import re
from decimal import Decimal

from enthusiast_lens.models.enthusiast_record import FIELD_ID_PATTERN_TEXT

from .aliases import canonicalize_alias
from .normalization import NumericInput, canonicalize_string, parse_numeric


FIELD_ID_PATTERN = re.compile(FIELD_ID_PATTERN_TEXT)


def is_valid_field_id(field_id: str) -> bool:
    """Return whether a value uses the canonical lower-snake dotted-path syntax."""

    return bool(field_id and FIELD_ID_PATTERN.fullmatch(field_id))


def validate_field_id(field_id: str) -> str:
    """Return a valid field ID or raise a syntax-only validation error."""

    if not is_valid_field_id(field_id):
        raise ValueError("field_id must be a lower-snake-case dotted path")
    return field_id


def compare_exact(actual: object, expected: object) -> bool:
    """Compare strings canonically and other values without type coercion."""

    if isinstance(actual, str) and isinstance(expected, str):
        return canonicalize_string(actual) == canonicalize_string(expected)
    if isinstance(actual, str) or isinstance(expected, str):
        return False
    if isinstance(actual, bool) != isinstance(expected, bool):
        return False
    return actual == expected


def compare_with_aliases(actual: str | None, expected: str | None) -> bool:
    """Compare two values through the explicit automotive alias table."""

    return canonicalize_alias(actual) == canonicalize_alias(expected)


def _required_decimal(value: NumericInput | None, name: str) -> Decimal:
    parsed = parse_numeric(value)
    if parsed is None:
        raise ValueError(f"{name} is required")
    return parsed


def compare_with_tolerance(
    actual: NumericInput,
    expected: NumericInput,
    tolerance: NumericInput,
) -> bool:
    """Compare numeric values using an inclusive absolute tolerance."""

    actual_value = _required_decimal(actual, "actual")
    expected_value = _required_decimal(expected, "expected")
    tolerance_value = _required_decimal(tolerance, "tolerance")
    if tolerance_value < 0:
        raise ValueError("tolerance must be non-negative")
    return abs(actual_value - expected_value) <= tolerance_value


def compare_with_range(
    actual: NumericInput,
    minimum: NumericInput,
    maximum: NumericInput,
) -> bool:
    """Compare a numeric value against an inclusive accepted range."""

    actual_value = _required_decimal(actual, "actual")
    minimum_value = _required_decimal(minimum, "minimum")
    maximum_value = _required_decimal(maximum, "maximum")
    if minimum_value > maximum_value:
        raise ValueError("minimum must not exceed maximum")
    return minimum_value <= actual_value <= maximum_value
