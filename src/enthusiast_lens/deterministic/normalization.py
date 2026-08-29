"""Deterministic normalization for already-structured runtime values.

These helpers clean known input only. They do not parse arbitrary automotive
prose, infer missing facts, or read the frozen evaluation answer key.
"""

import math
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from types import MappingProxyType
from typing import TypeAlias


NumericInput: TypeAlias = int | float | Decimal | str

_STRUCTURED_NUMBER = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")
UNIT_ALIASES = MappingProxyType(
    {
        "hp": "hp",
        "horsepower": "hp",
        "lb": "lb",
        "lb.": "lb",
        "lbs": "lb",
        "pound": "lb",
        "pounds": "lb",
        "kg": "kg",
        "kilogram": "kg",
        "kilograms": "kg",
    }
)


def clean_whitespace(value: str | None) -> str | None:
    """Collapse whitespace and represent blank text as missing."""

    if value is None:
        return None
    cleaned = " ".join(value.split())
    return cleaned or None


def canonicalize_string(value: str | None) -> str | None:
    """Return stable NFKC, whitespace-normalized, case-folded text."""

    cleaned = clean_whitespace(value)
    if cleaned is None:
        return None
    return unicodedata.normalize("NFKC", cleaned).casefold()


def case_insensitive_equal(left: str | None, right: str | None) -> bool:
    """Compare text after canonical normalization without inferring a value."""

    return canonicalize_string(left) == canonicalize_string(right)


def normalize_unit(unit: str | None) -> str | None:
    """Normalize a small inspectable unit vocabulary; preserve unknown units."""

    canonical = canonicalize_string(unit)
    if canonical is None:
        return None
    return UNIT_ALIASES.get(canonical, canonical)


def parse_numeric(value: object | None) -> Decimal | None:
    """Parse a numeric scalar or plain numeric string without interpreting prose."""

    if value is None:
        return None
    if isinstance(value, bool):
        raise TypeError("boolean values are not numeric inputs")
    if isinstance(value, Decimal):
        parsed = value
    elif isinstance(value, int):
        parsed = Decimal(value)
    elif isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("numeric values must be finite")
        parsed = Decimal(str(value))
    elif isinstance(value, str):
        cleaned = clean_whitespace(value)
        if cleaned is None:
            return None
        if _STRUCTURED_NUMBER.fullmatch(cleaned) is None:
            raise ValueError("numeric strings must contain only a structured number")
        try:
            parsed = Decimal(cleaned)
        except InvalidOperation as error:
            raise ValueError("invalid numeric input") from error
    else:
        raise TypeError(f"unsupported numeric input type: {type(value).__name__}")

    if not parsed.is_finite():
        raise ValueError("numeric values must be finite")
    return parsed
