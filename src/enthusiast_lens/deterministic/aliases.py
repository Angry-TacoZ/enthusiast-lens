"""Small, explicit alias vocabulary for canonical runtime comparison."""

from collections.abc import Mapping
from types import MappingProxyType

from .normalization import canonicalize_string


AUTOMOTIVE_ALIASES: Mapping[str, str] = MappingProxyType(
    {
        "fwd": "fwd",
        "front wheel drive": "fwd",
        "front-wheel drive": "fwd",
        "rwd": "rwd",
        "rear wheel drive": "rwd",
        "rear-wheel drive": "rwd",
        "awd": "awd",
        "all wheel drive": "awd",
        "all-wheel drive": "awd",
        "dct": "dct",
        "dual clutch transmission": "dct",
        "dual-clutch transmission": "dct",
        "cvt": "cvt",
        "continuously variable transmission": "cvt",
    }
)


def canonicalize_alias(
    value: str | None,
    aliases: Mapping[str, str] = AUTOMOTIVE_ALIASES,
) -> str | None:
    """Map a known alias to its canonical value; retain unknown normalized text."""

    normalized = canonicalize_string(value)
    if normalized is None:
        return None
    return aliases.get(normalized, normalized)
