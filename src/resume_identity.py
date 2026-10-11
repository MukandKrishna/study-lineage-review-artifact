"""Hash- and provenance-aware identities for safely resuming model calls."""

from __future__ import annotations

from typing import Any


ResumeIdentity = tuple[str, str, str, str, int]


def effective_bundle_id(config: dict[str, Any]) -> str:
    """Return the explicit bundle ID, with experiment ID as a legacy fallback."""

    bundle_id = str(config.get("bundle_id") or config.get("experiment_id") or "")
    if not bundle_id:
        raise ValueError("A bundle_id or experiment_id is required for safe resume identity")
    return bundle_id


def planned_resume_identity(
    entry: dict[str, Any],
    repetition: int,
    *,
    bundle_id: str,
    model_id: str,
) -> ResumeIdentity:
    return (
        str(entry["input_sha256"]),
        bundle_id,
        model_id,
        str(entry["execution_item_id"]),
        repetition,
    )


def completed_resume_identities(rows: list[dict[str, Any]]) -> set[ResumeIdentity]:
    """Load only complete identities; legacy rows cannot hide repaired inputs."""

    completed: set[ResumeIdentity] = set()
    for row in rows:
        if row.get("response_status") != "ok":
            continue
        input_sha256 = row.get("input_sha256")
        bundle_id = row.get("bundle_id")
        model_id = row.get("model_id")
        execution_item_id = row.get("execution_item_id")
        repetition = row.get("repetition")
        if not all(
            isinstance(value, str) and value
            for value in (input_sha256, bundle_id, model_id, execution_item_id)
        ):
            continue
        if isinstance(repetition, bool) or not isinstance(repetition, int) or repetition < 1:
            continue
        completed.add(
            (input_sha256, bundle_id, model_id, execution_item_id, repetition)
        )
    return completed


def pending_calls(
    executions: list[dict[str, Any]],
    repetitions: int,
    existing_rows: list[dict[str, Any]],
    *,
    bundle_id: str,
    model_id: str,
) -> list[tuple[dict[str, Any], int]]:
    completed = completed_resume_identities(existing_rows)
    return [
        (entry, repetition)
        for entry in executions
        for repetition in range(1, repetitions + 1)
        if planned_resume_identity(
            entry,
            repetition,
            bundle_id=bundle_id,
            model_id=model_id,
        )
        not in completed
    ]
