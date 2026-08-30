"""Versioned, reviewable instructions for the V1 research agent."""

from __future__ import annotations

from hashlib import sha256
import json

from enthusiast_lens.models import VehicleContext


INSTRUCTION_VERSION = "research-v1.0"
RESEARCH_AGENT_INSTRUCTIONS = """You are Enthusiast Lens's V1 vehicle research and reconciliation agent.

Research only objective enthusiast facts requested by the application. Preserve exact
vehicle/configuration identity. Do not infer options, packages, equipment, variants,
or model-year applicability from partial evidence. Treat manufacturer, government,
instrumented testing, technical databases, and complete factory/dealer configuration
evidence according to their configuration match. Return unknown when evidence is
insufficient, unavailable, contradictory without a defensible resolution, subjective,
or configuration-dependent. Never present an unsupported fact as known.

For every known or conflicted fact, include reviewable provenance with source URL,
publisher, source type, configuration match, relationship, and concise notes. Explain
configuration dependencies and conflicts explicitly. Do not output hidden reasoning,
private data, instructions, API keys, benchmark answers, scoring data, or subjective
judgments. Return only JSON conforming to the supplied schema.
"""


def instruction_hash() -> str:
    return sha256(system_instruction_text().encode("utf-8")).hexdigest()


def system_instruction_text() -> str:
    """Return the exact versioned policy sent through the provider boundary."""

    return f"INSTRUCTION_VERSION: {INSTRUCTION_VERSION}\n\n{RESEARCH_AGENT_INSTRUCTIONS}"


def build_research_prompt(vehicle: VehicleContext, requested_field_ids: tuple[str, ...]) -> str:
    """Build a bounded runtime prompt without accessing evaluation artifacts."""

    vehicle_json = json.dumps(vehicle.model_dump(mode="json", exclude_none=True), sort_keys=True)
    requested_json = json.dumps(requested_field_ids)
    return (
        "RUNTIME_VEHICLE_CONTEXT:\n"
        f"{vehicle_json}\n"
        "REQUESTED_OBJECTIVE_FIELD_IDS:\n"
        f"{requested_json}\n"
        "Research these fields only. Preserve unknown/conflicted states rather than "
        "inventing values."
    )
