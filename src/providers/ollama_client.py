from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import httpx

from common import extract_json_object
from providers.base import ModelResponseError, aggregate_attempts, attempt_record


def _validate_scalar(value: Any, spec: dict[str, Any], field: str) -> None:
    expected_type = spec.get("type")
    if expected_type == "string" and not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    if expected_type == "integer" and (not isinstance(value, int) or isinstance(value, bool)):
        raise ValueError(f"{field} must be an integer")
    if expected_type == "number" and (
        not isinstance(value, (int, float)) or isinstance(value, bool)
    ):
        raise ValueError(f"{field} must be a number")
    if expected_type == "boolean" and not isinstance(value, bool):
        raise ValueError(f"{field} must be a boolean")
    if "enum" in spec and value not in spec["enum"]:
        raise ValueError(f"{field} is not in the allowed enum")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in spec and value < spec["minimum"]:
            raise ValueError(f"{field} is below its minimum")
        if "maximum" in spec and value > spec["maximum"]:
            raise ValueError(f"{field} is above its maximum")


def validate_json_schema_payload(payload: dict[str, Any], schema: dict[str, Any]) -> None:
    """Validate the object subset used by this project without another dependency."""
    if schema.get("type") != "object":
        raise ValueError("Ollama client currently requires a top-level object schema")
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    missing = [field for field in required if field not in payload]
    if missing:
        raise ValueError(f"Structured response is missing required fields: {missing}")
    if schema.get("additionalProperties") is False:
        extra = sorted(set(payload) - set(properties))
        if extra:
            raise ValueError(f"Structured response has unexpected fields: {extra}")
    for field, value in payload.items():
        if field in properties:
            _validate_scalar(value, properties[field], field)


class OllamaJSONClient:
    provider = "ollama"

    def __init__(self, spec: dict[str, Any], root: Path) -> None:
        del root
        self.model = str(spec["model"])
        self.base_url = str(spec.get("base_url", "http://127.0.0.1:11434")).rstrip("/")
        self.temperature = float(spec.get("temperature", 0.2))
        self.timeout_seconds = float(spec.get("timeout_seconds", 600.0))
        self.num_ctx = int(spec.get("num_ctx", 8192))
        self.num_predict = int(spec.get("num_predict", 700))
        self.think = bool(spec.get("think", False))
        self.keep_alive = str(spec.get("keep_alive", "15m"))
        seed = spec.get("seed")
        self.seed = int(seed) if seed is not None else None
        self.client = httpx.Client(timeout=self.timeout_seconds)

    def json(
        self,
        prompt: str,
        *,
        schema: dict[str, Any],
        schema_name: str,
        retries: int = 3,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        attempts: list[dict[str, Any]] = []
        last_error: Exception | None = None
        for attempt in range(1, retries + 1):
            started = time.perf_counter()
            try:
                options: dict[str, Any] = {
                    "temperature": self.temperature,
                    "num_ctx": self.num_ctx,
                    "num_predict": self.num_predict,
                }
                if self.seed is not None:
                    options["seed"] = self.seed
                response = self.client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False,
                        "format": schema,
                        "think": self.think,
                        "keep_alive": self.keep_alive,
                        "options": options,
                    },
                )
                response.raise_for_status()
                body = response.json()
                if not body.get("done", False):
                    raise ValueError("Ollama response was not marked done")
                content = str((body.get("message") or {}).get("content") or "")
                payload = extract_json_object(content)
                validate_json_schema_payload(payload, schema)
                input_tokens = body.get("prompt_eval_count")
                output_tokens = body.get("eval_count")
                total_tokens = (
                    int(input_tokens) + int(output_tokens)
                    if isinstance(input_tokens, int) and isinstance(output_tokens, int)
                    else None
                )
                attempts.append(attempt_record(
                    attempt,
                    "success",
                    time.perf_counter() - started,
                    input_tokens=input_tokens if isinstance(input_tokens, int) else None,
                    output_tokens=output_tokens if isinstance(output_tokens, int) else None,
                    reasoning_tokens=None,
                    total_tokens=total_tokens,
                    detail=str(body.get("done_reason") or ""),
                ))
                eval_duration = body.get("eval_duration")
                return payload, {
                    **self._base_metadata(schema_name),
                    "response_model": str(body.get("model") or self.model),
                    **aggregate_attempts(attempts),
                    "response_status": "ok",
                    "safety_reason": "",
                    "raw_response": content,
                    "pure_model_inference_seconds": (
                        round(float(eval_duration) / 1_000_000_000, 4)
                        if isinstance(eval_duration, (int, float))
                        else None
                    ),
                    "ollama_total_duration_seconds": (
                        round(float(body["total_duration"]) / 1_000_000_000, 4)
                        if isinstance(body.get("total_duration"), (int, float))
                        else None
                    ),
                    "ollama_load_duration_seconds": (
                        round(float(body["load_duration"]) / 1_000_000_000, 4)
                        if isinstance(body.get("load_duration"), (int, float))
                        else None
                    ),
                }
            except Exception as exc:
                last_error = exc
                attempts.append(attempt_record(
                    attempt,
                    "request_error",
                    time.perf_counter() - started,
                    detail=f"{type(exc).__name__}: {exc}",
                ))
                if attempt < retries:
                    time.sleep(min(2**attempt, 8))
        metadata = {
            **self._base_metadata(schema_name),
            **aggregate_attempts(attempts),
            "response_status": "error",
            "safety_reason": "",
            "raw_response": "",
        }
        raise ModelResponseError(
            f"Ollama request failed after {retries} attempts: {last_error}",
            category="request_failed",
            metadata=metadata,
        ) from last_error

    def _base_metadata(self, schema_name: str) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "project": "",
            "requested_model": self.model,
            "response_model": self.model,
            "location": "local_laptop",
            "response_schema": schema_name,
            "structured_output": "ollama_json_schema",
            "execution_backend": "local_ollama_on_pipeline_host",
            "timing_scope": "end_to_end_local_ollama_wall_clock",
            "pure_model_inference_seconds": None,
            "billing_mode": "local_compute_no_per_call_api_fee",
            "temperature": self.temperature,
            "seed": self.seed,
            "thinking_enabled": self.think,
        }

