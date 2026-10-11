from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.oauth2 import service_account

from common import extract_json_object
from providers.base import (
    ModelResponseError,
    ModelSafetyError,
    aggregate_attempts,
    attempt_record,
)


BLOCKED_FINISH_REASONS = {
    "SAFETY",
    "RECITATION",
    "LANGUAGE",
    "BLOCKLIST",
    "PROHIBITED_CONTENT",
    "SPII",
    "IMAGE_SAFETY",
    "IMAGE_PROHIBITED_CONTENT",
    "IMAGE_RECITATION",
}


def _enum_value(value: Any) -> str:
    return str(getattr(value, "value", value) or "")


def _usage_values(response: Any) -> dict[str, int | None]:
    usage = getattr(response, "usage_metadata", None)
    return {
        "input_tokens": getattr(usage, "prompt_token_count", None),
        "output_tokens": getattr(usage, "candidates_token_count", None),
        "reasoning_tokens": getattr(usage, "thoughts_token_count", None),
        "total_tokens": getattr(usage, "total_token_count", None),
    }


def _blocked_reason(response: Any) -> str:
    feedback = getattr(response, "prompt_feedback", None)
    prompt_reason = _enum_value(getattr(feedback, "block_reason", None))
    if prompt_reason and prompt_reason != "BLOCKED_REASON_UNSPECIFIED":
        message = str(getattr(feedback, "block_reason_message", "") or "")
        return f"prompt:{prompt_reason}" + (f": {message}" if message else "")
    candidates = getattr(response, "candidates", None) or []
    if candidates:
        finish_reason = _enum_value(getattr(candidates[0], "finish_reason", None))
        if finish_reason in BLOCKED_FINISH_REASONS:
            message = str(getattr(candidates[0], "finish_message", "") or "")
            return f"response:{finish_reason}" + (f": {message}" if message else "")
    return ""


def _finish_reason(response: Any) -> str:
    candidates = getattr(response, "candidates", None) or []
    return _enum_value(getattr(candidates[0], "finish_reason", None)) if candidates else ""


class VertexJSONClient:
    provider = "vertex"

    def __init__(self, spec: dict[str, Any], root: Path) -> None:
        load_dotenv()
        project = str(spec.get("project") or os.getenv("GOOGLE_CLOUD_PROJECT", ""))
        location = str(spec.get("location") or os.getenv("GOOGLE_CLOUD_LOCATION", "global"))
        credential_value = str(
            spec.get("credentials_file")
            or os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
        )
        credential_path = Path(credential_value)
        if credential_value and not credential_path.is_absolute():
            credential_path = root / credential_path
        if not project:
            raise RuntimeError("GOOGLE_CLOUD_PROJECT is missing from .env/model config")
        if not credential_value or not credential_path.exists():
            raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS does not point to an existing service-account JSON file")
        credentials = service_account.Credentials.from_service_account_file(
            credential_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        self.client = genai.Client(vertexai=True, project=project, location=location, credentials=credentials)
        self.model = str(spec["model"])
        self.project = project
        self.location = location
        self.temperature = float(spec.get("temperature", 0.0))

    def json(
        self,
        prompt: str,
        *,
        schema: dict[str, Any],
        schema_name: str,
        retries: int = 3,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        last_error: Exception | None = None
        attempts: list[dict[str, Any]] = []
        for attempt in range(1, retries + 1):
            started = time.perf_counter()
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=self.temperature,
                        response_mime_type="application/json",
                        response_json_schema=schema,
                    ),
                )
                usage_values = _usage_values(response)
                response_id = getattr(response, "response_id", None)
                blocked = _blocked_reason(response)
                if blocked:
                    attempts.append(attempt_record(
                        attempt,
                        "blocked",
                        time.perf_counter() - started,
                        response_id=response_id,
                        detail=blocked,
                        **usage_values,
                    ))
                    metadata = {
                        **self._base_metadata(schema_name),
                        **aggregate_attempts(attempts),
                        "response_status": "blocked",
                        "safety_reason": blocked,
                        "raw_response": "",
                    }
                    raise ModelSafetyError(
                        "Vertex blocked the prompt or response.",
                        category="blocked",
                        metadata=metadata,
                    )
                finish_reason = _finish_reason(response)
                if finish_reason and finish_reason not in {"STOP", "FINISH_REASON_UNSPECIFIED"}:
                    attempts.append(attempt_record(
                        attempt,
                        "incomplete",
                        time.perf_counter() - started,
                        response_id=response_id,
                        detail=finish_reason,
                        **usage_values,
                    ))
                    raise ValueError(f"Vertex response did not finish normally: {finish_reason}")
                text = response.text or ""
                try:
                    payload = extract_json_object(text)
                except Exception:
                    attempts.append(attempt_record(
                        attempt,
                        "invalid_json",
                        time.perf_counter() - started,
                        response_id=response_id,
                        detail="Response did not match the expected JSON object.",
                        **usage_values,
                    ))
                    raise
                attempts.append(attempt_record(
                    attempt,
                    "success",
                    time.perf_counter() - started,
                    response_id=response_id,
                    **usage_values,
                ))
                return payload, {
                    **self._base_metadata(schema_name),
                    "response_model": getattr(response, "model_version", self.model),
                    **aggregate_attempts(attempts),
                    "response_status": "ok",
                    "safety_reason": "",
                    "raw_response": text,
                }
            except ModelSafetyError:
                raise
            except Exception as exc:
                last_error = exc
                if not attempts or attempts[-1].get("attempt") != attempt:
                    attempts.append(attempt_record(
                        attempt,
                        "request_error",
                        time.perf_counter() - started,
                        detail=f"{type(exc).__name__}: {exc}",
                    ))
                if attempt < retries:
                    time.sleep(2**attempt)
        metadata = {
            **self._base_metadata(schema_name),
            **aggregate_attempts(attempts),
            "response_status": "error",
            "safety_reason": "",
            "raw_response": "",
        }
        raise ModelResponseError(
            f"Vertex request failed after {retries} attempts: {last_error}",
            category="request_failed",
            metadata=metadata,
        ) from last_error

    def _base_metadata(self, schema_name: str) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "project": getattr(self, "project", ""),
            "requested_model": self.model,
            "response_model": self.model,
            "location": self.location,
            "response_schema": schema_name,
            "structured_output": "json_schema",
            "execution_backend": "vertex_api_from_pipeline_host",
            "timing_scope": "end_to_end_vertex_api_wall_clock",
            "pure_model_inference_seconds": None,
            "billing_mode": "google_cloud_api",
        }
