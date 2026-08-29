import pytest
from pydantic import ValidationError

from enthusiast_lens.models import VehicleContext


def test_valid_minimal_context_keeps_optional_fields_absent() -> None:
    context = VehicleContext(year=2025, make="Synthetic Motors", model="Apex")

    assert context.year == 2025
    assert context.trim is None
    assert context.listing_url is None
    assert context.packages == ()


def test_richer_exact_configuration_is_preserved() -> None:
    context = VehicleContext(
        year=2024,
        make="Synthetic Motors",
        model="Apex",
        trim="Circuit",
        body_style="Coupe",
        transmission="6-speed manual",
        drivetrain="RWD",
        market="US",
        vin="SYNTHETICVIN00001",
        listing_id="listing-123",
        listing_url="https://example.com/listings/123",
        packages=("Track Package", "Premium Audio"),
        build_date_or_range="2024-03",
        hardware_generation="Gen 2",
        notes="Synthetic test context",
    )

    assert context.packages == ("Track Package", "Premium Audio")
    assert str(context.listing_url) == "https://example.com/listings/123"
    assert context.hardware_generation == "Gen 2"


@pytest.mark.parametrize("year", [1800, 2200])
def test_invalid_year_is_rejected(year: int) -> None:
    with pytest.raises(ValidationError):
        VehicleContext(year=year, make="Synthetic Motors", model="Apex")


def test_malformed_listing_url_is_rejected() -> None:
    with pytest.raises(ValidationError):
        VehicleContext(
            year=2025,
            make="Synthetic Motors",
            model="Apex",
            listing_url="not a URL",
        )


def test_unknown_fields_are_rejected_instead_of_silently_ignored() -> None:
    with pytest.raises(ValidationError):
        VehicleContext(
            year=2025,
            make="Synthetic Motors",
            model="Apex",
            invented_configuration="not allowed",
        )
