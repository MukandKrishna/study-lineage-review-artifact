from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from common import ROOT


PROMPT_DIR = ROOT / "prompts"
SCHEMA_DIR = ROOT / "schemas"

NEUTRAL_VERIFIER_PROMPT_PATH = (
    PROMPT_DIR / "epistemic_update_verifier_neutral_v2.txt"
)
RELATION_RECOGNITION_PROMPT_PATH = (
    PROMPT_DIR / "epistemic_update_relation_recognition_v1.txt"
)
COMPARATIVE_RECOGNITION_PROMPT_PATH = (
    PROMPT_DIR / "epistemic_update_relation_comparative_recognition_v2.txt"
)
UPDATE_INPUT_SCHEMA_PATH = SCHEMA_DIR / "model_input_sequential_update_v1.schema.json"
COMPARATIVE_RECOGNITION_INPUT_SCHEMA_PATH = (
    SCHEMA_DIR / "model_input_comparative_recognition_v1.schema.json"
)
VERIFIER_OUTPUT_SCHEMA_PATH = (
    SCHEMA_DIR / "model_output_multi_evidence_judge_v1.schema.json"
)
RECOGNITION_OUTPUT_SCHEMA_PATH = (
    SCHEMA_DIR / "model_output_relation_recognition_v1.schema.json"
)
COMPARATIVE_RECOGNITION_OUTPUT_SCHEMA_PATH = (
    SCHEMA_DIR / "model_output_comparative_recognition_v1.schema.json"
)

INPUT_FIELD_ORDER = (
    "schema_version",
    "item_id",
    "claim_id",
    "claim_text",
    "initial_evidence",
    "added_evidence",
)
EVIDENCE_FIELD_ORDER = (
    "bundle_position",
    "evidence_id",
    "source_group_id",
    "source_title",
    "pmid",
    "doi",
    "trial_id",
    "source_locator",
    "passage_text",
)
ABLATION_REMOVABLE_EVIDENCE_FIELDS = frozenset(
    {"source_group_id", "trial_id", "source_locator"}
)
RECOGNITION_FIELD_ORDER = (
    "item_id",
    "provenance_relation",
    "applicability_relation",
    "direction_relation",
    "confidence",
    "metadata_basis",
    "evidence_basis",
    "reason",
)
COMPARATIVE_INPUT_FIELD_ORDER = (
    "schema_version",
    "item_id",
    "claim_id",
    "claim_text",
    "target_relation",
    "initial_evidence",
    "update_a",
    "update_b",
)
COMPARATIVE_RECOGNITION_FIELD_ORDER = (
    "item_id",
    "target_relation",
    "comparative_answer",
    "confidence",
    "metadata_basis",
    "evidence_basis",
    "reason",
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def load_prompt(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if text.count("{model_input_json}") != 1:
        raise ValueError(f"Prompt must contain one model input placeholder: {path}")
    return text


def render_prompt(prompt_text: str, model_input: dict[str, Any]) -> str:
    return prompt_text.replace(
        "{model_input_json}",
        json.dumps(model_input, indent=2, ensure_ascii=False),
    )


def validate_update_input(
    payload: dict[str, Any],
    *,
    omitted_evidence_fields: frozenset[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    omitted_fields = omitted_evidence_fields or frozenset()
    unsupported_omissions = omitted_fields - ABLATION_REMOVABLE_EVIDENCE_FIELDS
    if unsupported_omissions:
        errors.append(
            "unsupported omitted evidence fields: "
            + ", ".join(sorted(unsupported_omissions))
        )
    omitted_fields &= ABLATION_REMOVABLE_EVIDENCE_FIELDS
    expected_evidence_fields = tuple(
        field for field in EVIDENCE_FIELD_ORDER if field not in omitted_fields
    )
    if tuple(payload) != INPUT_FIELD_ORDER:
        errors.append("input fields are missing, unexpected, or out of frozen order")
    if payload.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")
    for field in ("item_id", "claim_id", "claim_text"):
        if not isinstance(payload.get(field), str) or not payload.get(field, "").strip():
            errors.append(f"{field} must be a non-empty string")

    initial = payload.get("initial_evidence")
    added = payload.get("added_evidence")
    if not isinstance(initial, list) or len(initial) < 2:
        errors.append("initial_evidence must contain at least two items")
        initial = []
    if added is not None and not isinstance(added, dict):
        errors.append("added_evidence must be an evidence object or null")
    items = [*initial, *([] if added is None else [added])]
    positions: list[Any] = []
    for index, item in enumerate(items):
        prefix = f"evidence[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if tuple(item) != expected_evidence_fields:
            errors.append(f"{prefix} fields are missing, unexpected, or out of frozen order")
        positions.append(item.get("bundle_position"))
        for field in ("evidence_id", "source_group_id", "source_title", "source_locator", "passage_text"):
            if field in omitted_fields:
                continue
            if not isinstance(item.get(field), str) or not item.get(field, "").strip():
                errors.append(f"{prefix}.{field} must be a non-empty string")
        for field in ("pmid", "doi", "trial_id"):
            if field in omitted_fields:
                continue
            if item.get(field) is not None and not isinstance(item.get(field), str):
                errors.append(f"{prefix}.{field} must be a string or null")
    expected_positions = list(range(1, len(items) + 1))
    if positions != expected_positions:
        errors.append(
            f"bundle_position values must be consecutive and ordered: {expected_positions}"
        )
    return errors


def validate_comparative_recognition_input(
    payload: dict[str, Any],
    *,
    omitted_evidence_fields: frozenset[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    omitted_fields = omitted_evidence_fields or frozenset()
    unsupported_omissions = omitted_fields - ABLATION_REMOVABLE_EVIDENCE_FIELDS
    if unsupported_omissions:
        errors.append(
            "unsupported omitted evidence fields: "
            + ", ".join(sorted(unsupported_omissions))
        )
    omitted_fields &= ABLATION_REMOVABLE_EVIDENCE_FIELDS
    expected_evidence_fields = tuple(
        field for field in EVIDENCE_FIELD_ORDER if field not in omitted_fields
    )
    if tuple(payload) != COMPARATIVE_INPUT_FIELD_ORDER:
        errors.append("comparative input fields are missing, unexpected, or out of frozen order")
    if payload.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")
    for field in ("item_id", "claim_id", "claim_text"):
        if not isinstance(payload.get(field), str) or not payload.get(field, "").strip():
            errors.append(f"{field} must be a non-empty string")
    if payload.get("target_relation") not in {"provenance", "applicability", "direction"}:
        errors.append("target_relation must be provenance, applicability, or direction")

    initial = payload.get("initial_evidence")
    if not isinstance(initial, list) or len(initial) < 2:
        errors.append("initial_evidence must contain at least two items")
        initial = []

    update_a = payload.get("update_a")
    update_b = payload.get("update_b")
    for field, value in (("update_a", update_a), ("update_b", update_b)):
        if not isinstance(value, dict):
            errors.append(f"{field} must be an evidence object")

    items = [
        *initial,
        *([] if not isinstance(update_a, dict) else [update_a]),
        *([] if not isinstance(update_b, dict) else [update_b]),
    ]
    positions: list[Any] = []
    for index, item in enumerate(items):
        prefix = f"evidence[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if tuple(item) != expected_evidence_fields:
            errors.append(f"{prefix} fields are missing, unexpected, or out of frozen order")
        positions.append(item.get("bundle_position"))
        for field in ("evidence_id", "source_group_id", "source_title", "source_locator", "passage_text"):
            if field in omitted_fields:
                continue
            if not isinstance(item.get(field), str) or not item.get(field, "").strip():
                errors.append(f"{prefix}.{field} must be a non-empty string")
        for field in ("pmid", "doi", "trial_id"):
            if field in omitted_fields:
                continue
            if item.get(field) is not None and not isinstance(item.get(field), str):
                errors.append(f"{prefix}.{field} must be a string or null")
    expected_positions = list(range(1, len(items) + 1))
    if positions != expected_positions:
        errors.append(
            f"bundle_position values must be consecutive and ordered: {expected_positions}"
        )
    return errors


def model_input_json(
    model_input: dict[str, Any],
    *,
    omitted_evidence_fields: frozenset[str] | None = None,
) -> str:
    errors = validate_update_input(
        model_input,
        omitted_evidence_fields=omitted_evidence_fields,
    )
    if errors:
        raise ValueError("; ".join(errors))
    return json.dumps(model_input, indent=2, ensure_ascii=False)


def comparative_model_input_json(
    model_input: dict[str, Any],
    *,
    omitted_evidence_fields: frozenset[str] | None = None,
) -> str:
    errors = validate_comparative_recognition_input(
        model_input,
        omitted_evidence_fields=omitted_evidence_fields,
    )
    if errors:
        raise ValueError("; ".join(errors))
    return json.dumps(model_input, indent=2, ensure_ascii=False)
