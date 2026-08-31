"""NHTSA vPIC VIN decoder adapter.

vPIC is untrusted, manufacturer-reported structured seed data distributed by
NHTSA. Blank fields are unavailable source data, never inferred absence.
"""

from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
import re
from typing import Any

import httpx

from enthusiast_lens.deterministic import canonicalize_alias, clean_whitespace, parse_numeric
from enthusiast_lens.models import (
    Confidence,
    ConfigurationMatch,
    EvidenceRelationship,
    OriginType,
    Provenance,
    SourceType,
    StructuredContextFact,
    StructuredFactState,
    StructuredSeedFact,
    StructuredVehicleIdentity,
    StructuredVehicleSeed,
)


VPIC_BASE_URL = "https://vpic.nhtsa.dot.gov/api"
VIN_PATTERN = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")
NHTSA_PUBLISHER = "National Highway Traffic Safety Administration (NHTSA)"


class VPICError(RuntimeError):
    """Base exception for vPIC integration failures."""


class VPICTransportError(VPICError):
    """The request could not reach or complete against vPIC."""


class VPICHTTPError(VPICError):
    """vPIC returned an unsuccessful HTTP status."""


class VPICResponseError(VPICError):
    """vPIC returned malformed JSON or an unexpected response shape."""


class VPICDecodeError(VPICError):
    """vPIC returned a syntactically valid decode with a nonzero error code."""

    def __init__(self, error_code: str, error_text: str | None) -> None:
        self.error_code = error_code
        self.error_text = error_text
        message = f"vPIC decode failed with error code {error_code}"
        if error_text:
            message = f"{message}: {error_text}"
        super().__init__(message)


Normalizer = Callable[[str], Any]


def _decimal_to_json(value: Decimal) -> int | float:
    return int(value) if value == value.to_integral_value() else float(value)


def _number(value: str) -> int | float:
    parsed = parse_numeric(value)
    if parsed is None:
        raise ValueError("numeric provider value is blank")
    return _decimal_to_json(parsed)


def _text(value: str) -> str:
    cleaned = clean_whitespace(value)
    if cleaned is None:
        raise ValueError("provider text is blank")
    return cleaned


def _drive_type(value: str) -> str:
    normalized = canonicalize_alias(value)
    if normalized is None:
        raise ValueError("drive type is blank")
    return normalized


FIELD_MAPPINGS: tuple[tuple[str, str, str | None, Normalizer], ...] = (
    ("DisplacementCC", "engine.displacement_cc", "cc", _number),
    ("DisplacementL", "engine.displacement", "L", _number),
    ("EngineConfiguration", "engine.configuration", None, _text),
    ("EngineCylinders", "engine.cylinders", None, _number),
    ("EngineHP", "engine.horsepower", "hp", _number),
    ("FuelTypePrimary", "engine.fuel_type_primary", None, _text),
    ("ElectrificationLevel", "engine.electrification_level", None, _text),
    ("TransmissionStyle", "transmission.style", None, _text),
    ("TransmissionSpeeds", "transmission.speeds", None, _number),
    ("DriveType", "drivetrain.drive_type", None, _drive_type),
    ("CurbWeightLB", "chassis.curb_weight", "lb", _number),
    ("Axles", "chassis.axles", None, _number),
    ("BrakeSystemType", "brakes.system_type", None, _text),
)

EQUIPMENT_MAPPINGS: tuple[tuple[str, str], ...] = (
    ("Turbo", "engine.turbo"),
    ("AdaptiveCruiseControl", "driver_assistance.adaptive_cruise_control"),
    ("LaneDepartureWarning", "driver_assistance.lane_departure_warning"),
    ("LaneKeepSystem", "driver_assistance.lane_keep_system"),
    ("LaneCenteringAssistance", "driver_assistance.lane_centering_assistance"),
)

# A focused allowlist of exact-VIN context used to narrow Hybrid research. These
# values are not silently promoted to canonical answers merely because vPIC
# returned them.
CONTEXT_FIELDS: tuple[tuple[str, str | None], ...] = (
    ("ModelYear", None),
    ("Make", None),
    ("Model", None),
    ("Trim", None),
    ("Series", None),
    ("EngineManufacturer", None),
    ("EngineModel", None),
    ("EngineConfiguration", None),
    ("EngineCylinders", None),
    ("DisplacementCC", "cc"),
    ("DisplacementL", "L"),
    ("EngineHP", "hp"),
    ("FuelTypePrimary", None),
    ("ElectrificationLevel", None),
    ("TransmissionStyle", None),
    ("TransmissionSpeeds", None),
    ("DriveType", None),
    ("CurbWeightLB", "lb"),
    ("Turbo", None),
    ("AdaptiveCruiseControl", None),
    ("LaneCenteringAssistance", None),
    ("BatteryEnergyFrom", "kWh"),
    ("BatteryEnergyTo", "kWh"),
    ("BatteryEnergyUnits", None),
    ("WheelSize", None),
)


def _validate_vin(vin: str) -> str:
    if not isinstance(vin, str):
        raise TypeError("VIN must be a string")
    normalized = vin.strip().upper()
    if VIN_PATTERN.fullmatch(normalized) is None:
        raise ValueError("VIN must contain exactly 17 valid VIN characters")
    return normalized


def _validate_model_year(model_year: int | None) -> int | None:
    if model_year is None:
        return None
    if isinstance(model_year, bool) or not isinstance(model_year, int):
        raise TypeError("model_year must be an integer")
    if not 1886 <= model_year <= 2100:
        raise ValueError("model_year must be between 1886 and 2100")
    return model_year


def _provider_text(result: dict[str, Any], field: str) -> str | None:
    raw = result.get(field)
    if raw is None:
        return None
    if not isinstance(raw, str):
        raise VPICResponseError(f"vPIC field {field} must be a string when present")
    return clean_whitespace(raw)


def _parse_model_year(value: str | None, fallback: int | None) -> int | None:
    if value is None:
        return fallback
    try:
        parsed = _number(value)
    except (TypeError, ValueError) as error:
        raise VPICResponseError("vPIC ModelYear must be an integer") from error
    if not isinstance(parsed, int) or not 1886 <= parsed <= 2100:
        raise VPICResponseError("vPIC ModelYear is outside the supported range")
    return parsed


def _error_codes(raw: str) -> tuple[str, ...]:
    return tuple(code.strip() for code in raw.split(",") if code.strip())


class VPICClient:
    """Synchronous, injectable client for one exact-VIN vPIC decode."""

    def __init__(
        self,
        http_client: httpx.Client | None = None,
        *,
        base_url: str = VPIC_BASE_URL,
        timeout_seconds: float = 10.0,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._http_client = http_client
        self._base_url = base_url.rstrip("/")
        self._timeout = httpx.Timeout(timeout_seconds)

    def decode_vin(
        self,
        vin: str,
        model_year: int | None = None,
    ) -> StructuredVehicleSeed:
        normalized_vin = _validate_vin(vin)
        validated_year = _validate_model_year(model_year)
        path = f"/vehicles/DecodeVinValuesExtended/{normalized_vin}"
        params: dict[str, str | int] = {"format": "json"}
        if validated_year is not None:
            params["modelyear"] = validated_year

        try:
            if self._http_client is None:
                with httpx.Client(base_url=self._base_url, timeout=self._timeout) as client:
                    response = client.get(path, params=params)
            else:
                response = self._http_client.get(
                    f"{self._base_url}{path}", params=params, timeout=self._timeout
                )
        except httpx.RequestError as error:
            raise VPICTransportError("vPIC request failed") from error

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise VPICHTTPError(f"vPIC returned HTTP {response.status_code}") from error

        try:
            payload = response.json()
        except ValueError as error:
            raise VPICResponseError("vPIC returned malformed JSON") from error
        if not isinstance(payload, dict):
            raise VPICResponseError("vPIC response must be a JSON object")
        results = payload.get("Results")
        if not isinstance(results, list) or len(results) != 1 or not isinstance(results[0], dict):
            raise VPICResponseError("vPIC response must contain exactly one result object")

        result: dict[str, Any] = results[0]
        raw_error_code = _provider_text(result, "ErrorCode")
        if raw_error_code is None:
            raise VPICResponseError("vPIC result is missing ErrorCode")
        codes = _error_codes(raw_error_code)
        if not codes or any(code != "0" for code in codes):
            raise VPICDecodeError(raw_error_code, _provider_text(result, "ErrorText"))

        retrieved_at = datetime.now(UTC)
        source_url = str(response.request.url)
        warnings: list[str] = []
        facts = self._map_facts(result, source_url, retrieved_at, warnings)
        context_facts = self._map_context_facts(result, source_url, retrieved_at, warnings)
        identity = StructuredVehicleIdentity(
            vin=normalized_vin,
            model_year=_parse_model_year(_provider_text(result, "ModelYear"), validated_year),
            make=_provider_text(result, "Make"),
            model=_provider_text(result, "Model"),
            trim=_provider_text(result, "Trim"),
            series=_provider_text(result, "Series"),
            body_class=_provider_text(result, "BodyClass"),
        )

        return StructuredVehicleSeed(
            requested_vin=normalized_vin,
            requested_model_year=validated_year,
            source_url=source_url,
            retrieved_at=retrieved_at,
            identity=identity,
            facts=facts,
            context_facts=context_facts,
            provider_warnings=tuple(warnings),
            raw_provider_payload=payload,
        )

    @staticmethod
    def _provenance(
        source_url: str,
        retrieved_at: datetime,
        provider_field: str,
        provider_value: str | None,
        state: StructuredFactState,
    ) -> Provenance:
        original = provider_value if provider_value is not None else "<blank>"
        relationship = (
            EvidenceRelationship.SUPPORTS
            if state in {StructuredFactState.REPORTED, StructuredFactState.STANDARD}
            else EvidenceRelationship.CONTEXT
        )
        return Provenance(
            source_url=source_url,
            publisher=NHTSA_PUBLISHER,
            source_type=SourceType.GOVERNMENT_OR_REGULATORY,
            configuration_match=ConfigurationMatch.EXACT,
            origin=OriginType.STRUCTURED,
            confidence=Confidence.MEDIUM,
            retrieved_at=retrieved_at,
            notes=(
                "Manufacturer-reported data distributed through NHTSA vPIC; "
                f"provider field {provider_field}={original!r}."
            ),
            relationship=relationship,
        )

    @classmethod
    def _map_facts(
        cls,
        result: dict[str, Any],
        source_url: str,
        retrieved_at: datetime,
        warnings: list[str],
    ) -> tuple[StructuredSeedFact, ...]:
        facts: list[StructuredSeedFact] = []
        for provider_field, field_id, unit, normalizer in FIELD_MAPPINGS:
            provider_value = _provider_text(result, provider_field)
            state = StructuredFactState.UNKNOWN
            normalized_value = None
            if provider_value is not None:
                try:
                    normalized_value = normalizer(provider_value)
                    state = StructuredFactState.REPORTED
                except (TypeError, ValueError):
                    warnings.append(
                        f"Ignored malformed {provider_field} value from vPIC: {provider_value!r}"
                    )
            facts.append(
                StructuredSeedFact(
                    field_id=field_id,
                    provider_field=provider_field,
                    provider_value=provider_value,
                    normalized_value=normalized_value,
                    unit=unit,
                    state=state,
                    provenance=cls._provenance(
                        source_url, retrieved_at, provider_field, provider_value, state
                    ),
                )
            )

        for provider_field, field_id in EQUIPMENT_MAPPINGS:
            provider_value = _provider_text(result, provider_field)
            state, normalized_value = cls._interpret_equipment(provider_value, warnings, provider_field)
            facts.append(
                StructuredSeedFact(
                    field_id=field_id,
                    provider_field=provider_field,
                    provider_value=provider_value,
                    normalized_value=normalized_value,
                    state=state,
                    provenance=cls._provenance(
                        source_url, retrieved_at, provider_field, provider_value, state
                    ),
                )
            )
        return tuple(facts)

    @classmethod
    def _map_context_facts(
        cls,
        result: dict[str, Any],
        source_url: str,
        retrieved_at: datetime,
        warnings: list[str],
    ) -> tuple[StructuredContextFact, ...]:
        context: list[StructuredContextFact] = []
        numeric_fields = {"DisplacementCC", "DisplacementL", "EngineCylinders", "EngineHP", "TransmissionSpeeds", "CurbWeightLB", "BatteryEnergyFrom", "BatteryEnergyTo"}
        equipment_fields = {"Turbo", "AdaptiveCruiseControl", "LaneCenteringAssistance"}
        for provider_field, unit in CONTEXT_FIELDS:
            provider_value = _provider_text(result, provider_field)
            state = StructuredFactState.UNKNOWN
            normalized_value = None
            if provider_value is not None:
                try:
                    if provider_field in equipment_fields:
                        state, normalized_value = cls._interpret_equipment(provider_value, warnings, provider_field)
                    elif provider_field in numeric_fields:
                        normalized_value = _number(provider_value)
                        state = StructuredFactState.REPORTED
                    else:
                        normalized_value = _text(provider_value)
                        state = StructuredFactState.REPORTED
                except (TypeError, ValueError):
                    warnings.append(f"Ignored malformed {provider_field} context value from vPIC: {provider_value!r}")
            context.append(
                StructuredContextFact(
                    provider_field=provider_field,
                    provider_value=provider_value,
                    normalized_value=normalized_value,
                    unit=unit,
                    state=state,
                    provenance=cls._provenance(source_url, retrieved_at, provider_field, provider_value, state),
                )
            )
        return tuple(context)

    @staticmethod
    def _interpret_equipment(
        provider_value: str | None,
        warnings: list[str],
        provider_field: str,
    ) -> tuple[StructuredFactState, bool | None]:
        if provider_value is None:
            return StructuredFactState.UNKNOWN, None
        normalized = provider_value.casefold()
        if normalized == "standard":
            return StructuredFactState.STANDARD, True
        if normalized == "optional":
            return StructuredFactState.OPTIONAL, None
        if normalized == "not available":
            return StructuredFactState.NOT_AVAILABLE, None
        if normalized in {"yes", "true"}:
            return StructuredFactState.REPORTED, True
        if normalized in {"no", "false"}:
            return StructuredFactState.REPORTED, False
        warnings.append(f"Unrecognized {provider_field} equipment value: {provider_value!r}")
        return StructuredFactState.UNKNOWN, None
