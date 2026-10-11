from __future__ import annotations

from typing import Any, Protocol


TOKEN_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_tokens",
    "total_tokens",
)


class ModelResponseError(RuntimeError):
    """A model call failed after provider metadata had been collected."""

    def __init__(self, message: str, *, category: str, metadata: dict[str, Any]) -> None:
        super().__init__(message)
        self.category = category
        self.metadata = metadata


class ModelSafetyError(ModelResponseError):
    """A provider explicitly refused or blocked a prompt/response."""


def attempt_record(
    attempt: int,
    status: str,
    latency_seconds: float,
    *,
    input_tokens: int | None = None,
    cached_input_tokens: int | None = None,
    output_tokens: int | None = None,
    reasoning_tokens: int | None = None,
    total_tokens: int | None = None,
    response_id: str | None = None,
    detail: str = "",
) -> dict[str, Any]:
    return {
        "attempt": attempt,
        "status": status,
        "latency_seconds": round(latency_seconds, 4),
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_input_tokens,
        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning_tokens,
        "total_tokens": total_tokens,
        "response_id": response_id,
        "detail": detail,
    }


def aggregate_attempts(attempts: list[dict[str, Any]]) -> dict[str, Any]:
    """Return cost-ready totals across every response-bearing retry attempt."""
    totals: dict[str, int | None] = {}
    for field in TOKEN_FIELDS:
        values = [row[field] for row in attempts if isinstance(row.get(field), int)]
        totals[field] = sum(values) if values else None
    final = attempts[-1] if attempts else {}
    return {
        "request_attempts": len(attempts),
        "retry_count": max(0, len(attempts) - 1),
        "latency_seconds": round(
            sum(float(row.get("latency_seconds") or 0.0) for row in attempts), 4
        ),
        **totals,
        **{f"final_attempt_{field}": final.get(field) for field in TOKEN_FIELDS},
        "attempt_records": attempts,
    }


class JSONModelClient(Protocol):
    provider: str
    model: str

    def json(
        self,
        prompt: str,
        *,
        schema: dict[str, Any],
        schema_name: str,
        retries: int = 3,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        ...
