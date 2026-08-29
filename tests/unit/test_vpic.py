from __future__ import annotations

import httpx
import pytest

from enthusiast_lens.adapters import (
    VPICClient,
    VPICDecodeError,
    VPICHTTPError,
    VPICResponseError,
    VPICTransportError,
)


SYNTHETIC_VIN = "1M8GDM9AXKP042788"


def successful_payload(**overrides: object) -> dict[str, object]:
    result: dict[str, object] = {
        "ErrorCode": "0",
        "ErrorText": "0 - VIN decoded clean",
        "Make": "Synthetic Motors",
        "Model": "Apex",
        "ModelYear": "2025",
        "Trim": "Track",
        "Series": "S",
        "BodyClass": "Coupe",
        "DisplacementL": "2.3",
        "EngineConfiguration": "In-Line",
        "EngineCylinders": "4",
        "EngineHP": "315.0",
        "Turbo": "Yes",
        "FuelTypePrimary": "Gasoline",
        "ElectrificationLevel": "",
        "TransmissionStyle": "Automatic",
        "TransmissionSpeeds": "10",
        "DriveType": "Rear-Wheel Drive",
        "CurbWeightLB": "",
        "Axles": "2",
        "BrakeSystemType": "Hydraulic",
        "AdaptiveCruiseControl": "Standard",
        "LaneDepartureWarning": "Optional",
        "LaneKeepSystem": "Not Available",
    }
    result.update(overrides)
    return {"Count": 1, "Message": "Results returned successfully", "Results": [result]}


def mock_client(transport: httpx.MockTransport) -> VPICClient:
    return VPICClient(httpx.Client(transport=transport))


def fact_by_provider(seed: object, provider_field: str):
    return next(fact for fact in seed.facts if fact.provider_field == provider_field)


def test_successful_decode_sends_model_year_and_normalizes_selected_fields() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith(f"/DecodeVinValuesExtended/{SYNTHETIC_VIN}")
        assert request.url.params["format"] == "json"
        assert request.url.params["modelyear"] == "2025"
        return httpx.Response(200, json=successful_payload())

    seed = mock_client(httpx.MockTransport(handle)).decode_vin(SYNTHETIC_VIN.lower(), 2025)

    assert seed.identity.make == "Synthetic Motors"
    assert seed.identity.model == "Apex"
    assert seed.identity.model_year == 2025
    assert fact_by_provider(seed, "EngineHP").normalized_value == 315
    assert fact_by_provider(seed, "DriveType").normalized_value == "rwd"


def test_blank_and_equipment_values_preserve_non_boolean_semantics() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=successful_payload()))
    seed = mock_client(transport).decode_vin(SYNTHETIC_VIN, 2025)

    blank = fact_by_provider(seed, "CurbWeightLB")
    standard = fact_by_provider(seed, "AdaptiveCruiseControl")
    optional = fact_by_provider(seed, "LaneDepartureWarning")
    unavailable = fact_by_provider(seed, "LaneKeepSystem")

    assert (blank.state.value, blank.normalized_value) == ("unknown", None)
    assert (standard.state.value, standard.normalized_value) == ("standard", True)
    assert (optional.state.value, optional.normalized_value) == ("optional", None)
    assert (unavailable.state.value, unavailable.normalized_value) == (
        "not_available",
        None,
    )


def test_provenance_and_raw_payload_are_preserved() -> None:
    payload = successful_payload()
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    seed = mock_client(transport).decode_vin(SYNTHETIC_VIN, 2025)
    fact = fact_by_provider(seed, "EngineHP")

    assert seed.raw_provider_payload == payload
    assert fact.provider_value == "315.0"
    assert fact.provenance.origin.value == "structured"
    assert fact.provenance.publisher == "National Highway Traffic Safety Administration (NHTSA)"
    assert fact.provenance.source_type.value == "government_or_regulatory"
    assert fact.provenance.configuration_match.value == "exact"
    assert "manufacturer-reported" in fact.provenance.notes.casefold()


@pytest.mark.parametrize(
    "vin",
    ["", "SHORTVIN", "1M8GDM9AOKP042788", "1M8GDM9AIKP042788", "1M8GDM9AQKP042788"],
)
def test_malformed_vin_is_rejected_without_a_request(vin: str) -> None:
    transport = httpx.MockTransport(lambda request: pytest.fail("request should not run"))
    with pytest.raises(ValueError, match="17 valid VIN characters"):
        mock_client(transport).decode_vin(vin, 2025)


def test_nonzero_decode_error_is_distinct() -> None:
    payload = successful_payload(ErrorCode="1,14", ErrorText="1 - Check digit error")
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=payload))

    with pytest.raises(VPICDecodeError, match="1,14") as caught:
        mock_client(transport).decode_vin(SYNTHETIC_VIN, 2025)
    assert caught.value.error_code == "1,14"


def test_http_error_is_distinct() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(503, text="unavailable"))
    with pytest.raises(VPICHTTPError, match="HTTP 503"):
        mock_client(transport).decode_vin(SYNTHETIC_VIN, 2025)


def test_transport_error_is_distinct() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    with pytest.raises(VPICTransportError, match="request failed"):
        mock_client(httpx.MockTransport(handle)).decode_vin(SYNTHETIC_VIN, 2025)


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, content=b"not-json"),
        httpx.Response(200, json=[]),
        httpx.Response(200, json={"Results": []}),
        httpx.Response(200, json={"Results": [{}]}),
    ],
)
def test_malformed_json_or_schema_shape_is_rejected(response: httpx.Response) -> None:
    transport = httpx.MockTransport(lambda request: response)
    with pytest.raises(VPICResponseError):
        mock_client(transport).decode_vin(SYNTHETIC_VIN, 2025)


def test_malformed_numeric_field_becomes_unknown_with_warning() -> None:
    payload = successful_payload(EngineHP="not-a-number")
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    seed = mock_client(transport).decode_vin(SYNTHETIC_VIN, 2025)

    assert fact_by_provider(seed, "EngineHP").state.value == "unknown"
    assert any("EngineHP" in warning for warning in seed.provider_warnings)
