"""Child-process entry point for one synchronous Gemini model call.

The protocol is stdin JSON in, stdout JSON out. It deliberately never writes
credentials, provider headers, or hidden reasoning to its envelope.
"""

from __future__ import annotations

import json
import sys
import time
from typing import Any

from pydantic import ValidationError

from .base import ModelProviderError, StructuredModelRequest, sanitize_for_trace
from .gemini import GeminiModelClient, GeminiSettings, MissingGeminiApiKeyError


def run_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Execute a validated non-secret request and return a deterministic envelope."""

    started = time.perf_counter()
    try:
        settings = GeminiSettings.model_validate(payload["settings"])
        request = StructuredModelRequest.model_validate(payload["request"])
    except (KeyError, ValidationError, TypeError, ValueError) as error:
        return {
            "status": "validation_error",
            "error": {"exception_class": type(error).__name__},
            "elapsed_ms": round((time.perf_counter() - started) * 1000),
        }
    try:
        execution = GeminiModelClient(settings).execute(request)
    except MissingGeminiApiKeyError as error:
        return {
            "status": "provider_error",
            "error": {
                "normalized_error": str(error),
                "provider_diagnostic": {
                    "request_stage": "configuration",
                    "exception_class": type(error).__name__,
                    "provider_message": str(error),
                    "elapsed_ms": round((time.perf_counter() - started) * 1000),
                    "interaction_id_issued": False,
                },
            },
            "elapsed_ms": round((time.perf_counter() - started) * 1000),
        }
    except ModelProviderError as error:
        diagnostic = error.diagnostic.model_dump(mode="json") if error.diagnostic else None
        return {
            "status": "provider_error",
            "error": {
                "normalized_error": str(error),
                "provider_diagnostic": sanitize_for_trace(diagnostic),
            },
            "elapsed_ms": round((time.perf_counter() - started) * 1000),
        }
    return {
        "status": "completed",
        "execution": sanitize_for_trace(execution.model_dump(mode="json")),
        "usage": sanitize_for_trace(execution.usage.model_dump(mode="json")),
        "elapsed_ms": round((time.perf_counter() - started) * 1000),
    }


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
        if not isinstance(payload, dict):
            raise ValueError("worker payload must be an object")
    except (json.JSONDecodeError, ValueError) as error:
        envelope = {
            "status": "validation_error",
            "error": {"exception_class": type(error).__name__},
            "elapsed_ms": 0,
        }
    else:
        envelope = run_payload(payload)
    sys.stdout.write(json.dumps(sanitize_for_trace(envelope)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
