import pytest

from enthusiast_lens.deterministic import AUTOMOTIVE_ALIASES, canonicalize_alias


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("FWD", "fwd"),
        ("front-wheel drive", "fwd"),
        ("Front Wheel Drive", "fwd"),
        ("RWD", "rwd"),
        ("rear-wheel drive", "rwd"),
        ("AWD", "awd"),
        ("all wheel drive", "awd"),
        ("DCT", "dct"),
        ("dual-clutch transmission", "dct"),
        ("CVT", "cvt"),
        ("continuously variable transmission", "cvt"),
    ],
)
def test_known_aliases_map_to_inspectable_canonical_values(
    value: str,
    expected: str,
) -> None:
    assert canonicalize_alias(value) == expected
    assert canonicalize_alias(expected) == expected


def test_unknown_alias_is_preserved_without_guessing() -> None:
    assert canonicalize_alias("Torque converter automatic") == "torque converter automatic"
    assert canonicalize_alias(None) is None


def test_alias_definitions_are_read_only() -> None:
    with pytest.raises(TypeError):
        AUTOMOTIVE_ALIASES["4wd"] = "awd"  # type: ignore[index]
