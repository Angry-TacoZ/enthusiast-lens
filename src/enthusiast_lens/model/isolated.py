"""Parent-owned subprocess deadline for a synchronous Gemini model call."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Callable

from .base import ModelExecution, ModelProviderError, ProviderDiagnostic, StructuredModelRequest, sanitize_for_trace
from .gemini import GEMINI_PROVIDER, GeminiSettings


class WorkerDeadlineExceededError(ModelProviderError):
    """The parent terminated a worker that exceeded the hard wall-clock limit."""


class IsolatedGeminiWorkerProvider:
    """Run one synchronous Gemini Generate Content call in a killable child process."""

    def __init__(
        self,
        settings: GeminiSettings,
        *,
        worker_module: str = "enthusiast_lens.model.sync_worker",
        popen: Callable[..., subprocess.Popen[str]] = subprocess.Popen,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._settings = settings
        self._worker_module = worker_module
        self._popen = popen
        self._monotonic = monotonic

    def execute(self, request: StructuredModelRequest) -> ModelExecution:
        """Start exactly one worker; no worker or model retry is performed."""

        payload = json.dumps(
            {
                "settings": self._settings.model_dump(mode="json"),
                "request": request.model_dump(mode="json"),
            }
        )
        command = [sys.executable, "-m", self._worker_module]
        started = self._monotonic()
        process = self._popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            # Environment inheritance lets the child read the key at the trusted boundary.
            # It is intentionally absent from the command line and payload.
            env=os.environ.copy(),
        )
        try:
            stdout, _stderr = process.communicate(
                payload, timeout=self._settings.wall_clock_deadline_seconds
            )
        except subprocess.TimeoutExpired:
            self._terminate_worker(process)
            elapsed_ms = round((self._monotonic() - started) * 1000)
            diagnostic = ProviderDiagnostic(
                request_stage="worker_deadline",
                exception_class="WorkerDeadlineExceededError",
                elapsed_ms=elapsed_ms,
                interaction_id_issued=False,
            )
            raise WorkerDeadlineExceededError("Gemini worker exceeded the parent deadline", diagnostic)
        elapsed_ms = round((self._monotonic() - started) * 1000)
        return self._decode_envelope(stdout, elapsed_ms)

    @staticmethod
    def _terminate_worker(process: subprocess.Popen[str]) -> None:
        """Terminate, then kill if needed, so a timed-out worker cannot be orphaned."""

        process.terminate()
        try:
            process.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate(timeout=2)

    @staticmethod
    def _decode_envelope(stdout: str, elapsed_ms: int) -> ModelExecution:
        try:
            envelope = json.loads(stdout)
        except json.JSONDecodeError as error:
            diagnostic = ProviderDiagnostic(
                request_stage="worker_protocol",
                exception_class=type(error).__name__,
                provider_message="worker returned malformed JSON",
                elapsed_ms=elapsed_ms,
                interaction_id_issued=False,
            )
            raise ModelProviderError("Gemini worker returned malformed JSON", diagnostic) from error
        if not isinstance(envelope, dict):
            raise ModelProviderError("Gemini worker returned a non-object envelope")
        status = envelope.get("status")
        if status == "completed":
            try:
                execution = ModelExecution.model_validate(envelope["execution"])
                return execution.model_copy(
                    update={
                        "provider_latency_ms": execution.latency_ms,
                        "latency_ms": elapsed_ms,
                    }
                )
            except (KeyError, ValueError) as error:
                raise ModelProviderError("Gemini worker returned an invalid model-call envelope") from error
        error_details = envelope.get("error")
        safe_error = sanitize_for_trace(error_details) if error_details is not None else {}
        diagnostic_payload = safe_error.get("provider_diagnostic") if isinstance(safe_error, dict) else None
        diagnostic = ProviderDiagnostic.model_validate(diagnostic_payload) if diagnostic_payload else None
        if status in {"provider_error", "validation_error"}:
            raise ModelProviderError(f"Gemini worker {status}", diagnostic)
        raise ModelProviderError("Gemini worker returned an unknown envelope status")
