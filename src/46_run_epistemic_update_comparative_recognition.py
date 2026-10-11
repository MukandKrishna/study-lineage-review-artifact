from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common import ROOT, append_jsonl
from epistemic_update_prompt_contract import (
    ABLATION_REMOVABLE_EVIDENCE_FIELDS,
    COMPARATIVE_RECOGNITION_FIELD_ORDER,
    COMPARATIVE_RECOGNITION_OUTPUT_SCHEMA_PATH,
    comparative_model_input_json,
    load_prompt,
    validate_comparative_recognition_input,
)
from evidence_calibration import load_jsonl
from providers import create_client
from providers.base import ModelResponseError
from resume_identity import effective_bundle_id, pending_calls


DEFAULT_CONFIG = (
    ROOT / "configs" / "epistemic_update_p1_comparative_recognition_gpt55_v1.json"
)


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def render_prompt(
    prompt_text: str,
    model_input: dict[str, Any],
    *,
    omitted_evidence_fields: frozenset[str] | None = None,
) -> str:
    return prompt_text.replace(
        "{model_input_json}",
        comparative_model_input_json(
            model_input,
            omitted_evidence_fields=omitted_evidence_fields,
        ),
    )


def validate_comparative_output(
    payload: dict[str, Any], model_input: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    if tuple(payload) != COMPARATIVE_RECOGNITION_FIELD_ORDER:
        errors.append("output fields are missing, unexpected, or out of frozen order")
    if payload.get("item_id") != model_input.get("item_id"):
        errors.append("item_id must match the model input")
    if payload.get("target_relation") != model_input.get("target_relation"):
        errors.append("target_relation must match the model input")
    if payload.get("comparative_answer") not in {"A", "B", "no_meaningful_difference"}:
        errors.append("comparative_answer is invalid")
    confidence = payload.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, int) or not 0 <= confidence <= 100:
        errors.append("confidence must be an integer from 0 to 100")

    metadata_basis = payload.get("metadata_basis")
    if not isinstance(metadata_basis, list) or any(
        not isinstance(item, str) or not item.strip() for item in metadata_basis
    ):
        errors.append("metadata_basis must be a list of non-empty strings")
    elif len(metadata_basis) != len(set(metadata_basis)):
        errors.append("metadata_basis must not contain duplicate strings")

    evidence_basis = payload.get("evidence_basis")
    if not isinstance(evidence_basis, list):
        errors.append("evidence_basis must be a list")
    else:
        update_by_label = {"A": model_input.get("update_a"), "B": model_input.get("update_b")}
        for index, item in enumerate(evidence_basis):
            prefix = f"evidence_basis[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} must be an object")
                continue
            if set(item) != {"update_label", "evidence_id", "evidence_quote"}:
                errors.append(f"{prefix} has unexpected or missing fields")
            update_label = item.get("update_label")
            if update_label not in {"A", "B"}:
                errors.append(f"{prefix}.update_label must be A or B")
                continue
            update_item = update_by_label.get(update_label)
            if not isinstance(update_item, dict):
                errors.append(f"{prefix}.update_label does not map to an update item")
                continue
            if item.get("evidence_id") != update_item.get("evidence_id"):
                errors.append(f"{prefix}.evidence_id must match update_{update_label.lower()}")
            quote = item.get("evidence_quote")
            if not isinstance(quote, str) or not quote.strip():
                errors.append(f"{prefix}.evidence_quote must be a non-empty string")
            elif quote not in str(update_item.get("passage_text", "")):
                errors.append(f"{prefix}.evidence_quote must be an exact quote from its update")

    if not isinstance(payload.get("reason"), str) or not payload.get("reason", "").strip():
        errors.append("reason must be a non-empty string")
    return errors


def is_quota_or_usage_limit_error(message: str) -> bool:
    lowered = message.lower()
    return any(
        phrase in lowered
        for phrase in (
            "usage limit",
            "more credits",
            "try again at",
            "rate limit",
            "quota",
        )
    )


def validate_and_load_plan(config_path: Path) -> tuple[dict[str, Any], str, list[dict[str, Any]]]:
    config = load_json_object(config_path)
    errors: list[str] = []

    input_ablation = config.get("input_ablation")
    omitted_evidence_fields: frozenset[str] = frozenset()
    if input_ablation is not None:
        if not isinstance(input_ablation, dict):
            errors.append("input_ablation must be an object when provided")
        else:
            raw_omissions = input_ablation.get("omitted_evidence_fields")
            if not isinstance(raw_omissions, list) or any(
                not isinstance(field, str) for field in raw_omissions
            ):
                errors.append("input_ablation.omitted_evidence_fields must be a list of strings")
            else:
                omitted_evidence_fields = frozenset(raw_omissions)
                unsupported = omitted_evidence_fields - ABLATION_REMOVABLE_EVIDENCE_FIELDS
                if unsupported:
                    errors.append(
                        "input_ablation has unsupported omitted evidence fields: "
                        + ", ".join(sorted(unsupported))
                    )

    prompt_version = str(config.get("prompt_version", ""))
    prompt_path = ROOT / "prompts" / f"{prompt_version}.txt"
    if not prompt_path.exists():
        errors.append(f"prompt does not exist: {prompt_path}")
        prompt_text = ""
    else:
        prompt_text = load_prompt(prompt_path)
        actual_prompt_hash = sha256_bytes(prompt_path.read_bytes())
        if config.get("prompt_sha256") != actual_prompt_hash:
            errors.append(
                f"prompt_sha256 mismatch: expected {config.get('prompt_sha256')}, "
                f"got {actual_prompt_hash}"
            )

    response_schema_name = str(config.get("response_schema", ""))
    if response_schema_name != "epistemic_update_relation_comparative_recognition_v1":
        errors.append("response_schema must be epistemic_update_relation_comparative_recognition_v1")
    if not COMPARATIVE_RECOGNITION_OUTPUT_SCHEMA_PATH.exists():
        errors.append(f"response schema does not exist: {COMPARATIVE_RECOGNITION_OUTPUT_SCHEMA_PATH}")
    else:
        expected_schema_hash = str(config.get("response_schema_sha256", ""))
        actual_schema_hash = sha256_bytes(COMPARATIVE_RECOGNITION_OUTPUT_SCHEMA_PATH.read_bytes())
        if expected_schema_hash != actual_schema_hash:
            errors.append(
                f"response_schema_sha256 mismatch: expected {expected_schema_hash}, "
                f"got {actual_schema_hash}"
            )

    input_dir = resolve(Path(str(config.get("input_directory", ""))))
    executions = config.get("executions")
    if not isinstance(executions, list) or not executions:
        errors.append("executions must be a non-empty list")
        executions = []

    loaded: list[dict[str, Any]] = []
    execution_ids: list[str] = []
    condition_ids: list[str] = []
    for index, spec in enumerate(executions):
        prefix = f"executions[{index}]"
        if not isinstance(spec, dict):
            errors.append(f"{prefix} must be an object")
            continue
        expected_fields = {
            "condition_id",
            "execution_item_id",
            "input_file",
            "input_sha256",
            "expected_comparative_answer",
        }
        if set(spec) != expected_fields:
            errors.append(f"{prefix} has unexpected or missing fields")
        condition_id = str(spec.get("condition_id", ""))
        execution_item_id = str(spec.get("execution_item_id", ""))
        condition_ids.append(condition_id)
        execution_ids.append(execution_item_id)
        if spec.get("expected_comparative_answer") not in {
            "A",
            "B",
            "no_meaningful_difference",
        }:
            errors.append(f"{prefix}: expected_comparative_answer is invalid")

        path = input_dir / str(spec.get("input_file", ""))
        if not path.exists():
            errors.append(f"{prefix}: input does not exist: {path}")
            continue
        payload = load_json_object(path)
        if payload.get("item_id") != execution_item_id:
            errors.append(f"{prefix}: execution_item_id does not match file item_id")
        errors.extend(
            f"{prefix}: {error}"
            for error in validate_comparative_recognition_input(
                payload,
                omitted_evidence_fields=omitted_evidence_fields,
            )
        )
        actual_hash = sha256_bytes(path.read_bytes())
        if spec.get("input_sha256") != actual_hash:
            errors.append(
                f"{prefix}: input_sha256 mismatch: expected {spec.get('input_sha256')}, "
                f"got {actual_hash}"
            )
        loaded.append(
            {
                "condition_id": condition_id,
                "execution_item_id": execution_item_id,
                "input_sha256": actual_hash,
                "expected_comparative_answer": spec.get("expected_comparative_answer"),
                "model_input": payload,
            }
        )

    if len(execution_ids) != len(set(execution_ids)):
        errors.append("execution_item_id values must be unique")
    if len(condition_ids) != len(set(condition_ids)):
        errors.append("condition_id values must be unique")

    design = config.get("pilot_design") or {}
    repetitions = design.get("repetitions_per_input")
    if isinstance(repetitions, bool) or not isinstance(repetitions, int) or repetitions < 2:
        errors.append("repetitions_per_input must be an integer of at least 2")
        repetitions = 0
    if design.get("condition_count") != len(loaded):
        errors.append(f"pilot_design.condition_count must be {len(loaded)}")
    if design.get("planned_model_calls") != len(loaded) * repetitions:
        errors.append(f"pilot_design.planned_model_calls must be {len(loaded) * repetitions}")
    if design.get("recognition_calls") != design.get("planned_model_calls"):
        errors.append("pilot_design.recognition_calls must equal planned_model_calls")

    model_id = config.get("default_judge_model_id")
    models = config.get("models") or {}
    if model_id not in models:
        errors.append("default_judge_model_id is absent from models")
    else:
        model_spec = models[model_id]
        if model_spec.get("provider") != "codex_cli":
            errors.append("P1 comparative sample currently expects provider=codex_cli")
        if model_spec.get("model") != "gpt-5.5":
            errors.append("P1 comparative sample currently expects model=gpt-5.5")
        if model_spec.get("reasoning_effort") != "medium":
            errors.append("P1 comparative sample currently expects reasoning_effort=medium")
        if model_spec.get("retries_per_repetition") != 1:
            errors.append("retries_per_repetition must be 1 so retries do not hide instability")

    if resolve(Path(str(config.get("prediction_path", "")))) == resolve(
        Path(str(config.get("error_path", "")))
    ):
        errors.append("prediction_path and error_path must be different")

    if errors:
        raise ValueError(
            "EPISTEMIC_UPDATE_COMPARATIVE_RECOGNITION_PLAN=failed\n- "
            + "\n- ".join(errors)
        )
    return config, prompt_text, loaded


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate or run the guarded P1 comparative-recognition diagnostic."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--confirm-model-calls", action="store_true")
    parser.add_argument("--execution-item-id", action="append", default=None)
    return parser.parse_args()


def progress_bar(done: int, total: int, width: int = 20) -> str:
    if total <= 0:
        return "[" + "." * width + "]"
    filled = round(width * done / total)
    return "[" + "#" * filled + "." * (width - filled) + "]"


def main() -> None:
    args = parse_args()
    config_path = resolve(args.config)
    config, prompt_text, executions = validate_and_load_plan(config_path)
    omitted_evidence_fields = frozenset(
        (config.get("input_ablation") or {}).get("omitted_evidence_fields", [])
    )
    design = config["pilot_design"]
    repetitions = int(design["repetitions_per_input"])
    print(f"PASS  comparative conditions: {design['condition_count']}")
    print(f"PASS  repetitions per condition: {repetitions}")
    print(f"PASS  planned recognition calls: {design['planned_model_calls']}")
    print("PASS  prompt, schema, and input hashes: frozen")
    if args.validate_only:
        print("MODEL_CALLS=0")
        return

    if args.execution_item_id:
        requested = {str(item) for item in args.execution_item_id}
        available = {entry["execution_item_id"] for entry in executions}
        missing = sorted(requested - available)
        if missing:
            raise ValueError(f"Unknown execution item IDs: {missing}")
        executions = [entry for entry in executions if entry["execution_item_id"] in requested]

    selected_call_count = len(executions) * repetitions
    print(f"SELECTED_CONDITIONS={len(executions)}")
    print(f"SELECTED_MODEL_CALLS={selected_call_count}")

    if config.get("model_calls_enabled") is not True:
        raise RuntimeError("MODEL_CALL_GATE=closed: set model_calls_enabled=true only after approval")
    if not args.confirm_model_calls:
        raise RuntimeError("MODEL_CALL_GATE=closed: pass --confirm-model-calls after approval")

    model_id = str(config["default_judge_model_id"])
    bundle_id = effective_bundle_id(config)
    model_spec = dict(config["models"][model_id])
    retries = int(model_spec.pop("retries_per_repetition"))
    response_schema_name = str(config["response_schema"])
    response_schema = load_json_object(COMPARATIVE_RECOGNITION_OUTPUT_SCHEMA_PATH)
    prediction_path = resolve(Path(config["prediction_path"]))
    error_path = resolve(Path(config["error_path"]))
    existing = load_jsonl(prediction_path) if prediction_path.exists() else []
    pending = pending_calls(
        executions,
        repetitions,
        existing,
        bundle_id=bundle_id,
        model_id=model_id,
    )
    print(f"PENDING_MODEL_CALLS={len(pending)}")
    client = create_client(model_spec, ROOT)
    prompt_path = ROOT / "prompts" / f"{config['prompt_version']}.txt"
    prompt_sha256 = sha256_bytes(prompt_path.read_bytes())

    total_pending = len(pending)
    for index, (entry, repetition) in enumerate(pending, start=1):
        model_input = entry["model_input"]
        base = {
            "experiment_id": config["experiment_id"],
            "evaluator_id": f"{model_id}_{config['prompt_version']}",
            "model_id": model_id,
            "bundle_id": bundle_id,
            "prompt_version": config["prompt_version"],
            "prompt_sha256": prompt_sha256,
            "input_sha256": entry["input_sha256"],
            "condition_id": entry["condition_id"],
            "execution_item_id": entry["execution_item_id"],
            "expected_comparative_answer": entry["expected_comparative_answer"],
            "repetition": repetition,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        prompt = render_prompt(
            prompt_text,
            model_input,
            omitted_evidence_fields=omitted_evidence_fields,
        )
        print(
            "CALL_PROGRESS "
            f"{index}/{total_pending} {progress_bar(index - 1, total_pending)} "
            f"condition={entry['condition_id']} rep={repetition} status=start",
            flush=True,
        )
        try:
            payload, metadata = client.json(
                prompt,
                schema=response_schema,
                schema_name=response_schema_name,
                retries=retries,
            )
        except ModelResponseError as exc:
            error_message = str(exc)
            append_jsonl(
                error_path,
                {
                    **base,
                    "response_status": "error",
                    "error_category": exc.category,
                    "error_message": error_message,
                    **exc.metadata,
                },
            )
            if is_quota_or_usage_limit_error(error_message):
                raise RuntimeError(
                    "MODEL_CALL_STOPPED=quota_or_usage_limit: recorded the error and "
                    "stopped before attempting later pending calls"
                ) from exc
            print(
                "CALL_PROGRESS "
                f"{index}/{total_pending} {progress_bar(index, total_pending)} "
                f"condition={entry['condition_id']} rep={repetition} status=error",
                flush=True,
            )
            continue

        semantic_errors = validate_comparative_output(payload, model_input)
        if semantic_errors:
            append_jsonl(
                error_path,
                {
                    **base,
                    "response_status": "error",
                    "error_category": "semantic_validation_failed",
                    "error_message": "; ".join(semantic_errors),
                    "invalid_payload": payload,
                    **metadata,
                },
            )
            print(
                "CALL_PROGRESS "
                f"{index}/{total_pending} {progress_bar(index, total_pending)} "
                f"condition={entry['condition_id']} rep={repetition} status=semantic_error",
                flush=True,
            )
            continue
        append_jsonl(prediction_path, {**base, "response_status": "ok", **payload, **metadata})
        print(
            "CALL_PROGRESS "
            f"{index}/{total_pending} {progress_bar(index, total_pending)} "
            f"condition={entry['condition_id']} rep={repetition} status=ok",
            flush=True,
        )

    print(f"Completed {len(pending)} pending calls")
    print(f"Predictions: {prediction_path}")
    print(f"Errors: {error_path}")


if __name__ == "__main__":
    main()
