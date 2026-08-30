"""Deterministic, provider-independent utilities for shared V1 behavior."""

from .aliases import AUTOMOTIVE_ALIASES, canonicalize_alias
from .calculations import (
    PowerToWeight,
    UnresolvedFactError,
    calculate_power_to_weight,
    calculate_power_to_weight_hp_per_us_ton,
)
from .normalization import (
    UNIT_ALIASES,
    canonicalize_string,
    case_insensitive_equal,
    clean_whitespace,
    normalize_unit,
    parse_numeric,
)
from .validation import (
    compare_exact,
    compare_with_aliases,
    compare_with_range,
    compare_with_tolerance,
    is_valid_field_id,
    validate_field_id,
)

__all__ = [
    "AUTOMOTIVE_ALIASES",
    "PowerToWeight",
    "UNIT_ALIASES",
    "UnresolvedFactError",
    "calculate_power_to_weight",
    "calculate_power_to_weight_hp_per_us_ton",
    "canonicalize_alias",
    "canonicalize_string",
    "case_insensitive_equal",
    "clean_whitespace",
    "compare_exact",
    "compare_with_aliases",
    "compare_with_range",
    "compare_with_tolerance",
    "is_valid_field_id",
    "normalize_unit",
    "parse_numeric",
    "validate_field_id",
]
