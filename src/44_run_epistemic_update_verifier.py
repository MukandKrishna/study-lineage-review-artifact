from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common import ROOT, append_jsonl
from epistemic_multi_evidence_schemas import (
    EPISTEMIC_MULTI_EVIDENCE_JUDGE_SCHEMAS,
    JUDGE_OUTPUT_SCHEMA_PATH,
    validate_judge_output,
)
from epistemic_update_prompt_contract import (
    ABLATION_REMOVABLE_EVIDENCE_FIELDS,
    load_prompt,
    validate_update_input,
)
from evidence_calibration import load_jsonl
from providers import create_client
from providers.base import ModelResponseError


DEFAULT_CONFIG = ROOT / "configs" / "epistemic_update_p1_neutral_verifier_gpt55_v1.json"


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def render_prompt(prompt_text: str, model_input: dict[str, Any]) -> str:
    return prompt_text.replace(
        "{model_input_json}",
        json.dumps(model_input, indent=2, ensure_ascii=False),
    )


def as_multi_evidence_input(
    update_input: dict[str, Any],
    *,
    omitted_evidence_fields: frozenset[str] | None = None,
) -> dict[str, Any]:
    omitted_fields = omitted_evidence_fields or frozenset()
    evidence_items = [
        *update_input["initial_evidence"],
        *([] if update_input["added_evidence"] is None else [update_input["added_evidence"]]),
    ]

    def validation_source_group(item: dict[str, Any]) -> str:
        if "source_group_id" in item:
            return str(item["source_group_id"])
        if "source_group_id" not in omitted_fields:
            raise KeyError("source_group_id is absent without a declared input ablation")
        # The legacy output validator requires this field structurally but does not
        # use it to judge model behavior. This value is never rendered to the model.
        return f"VALIDATION_ONLY_{item['evidence_id']}"

    return {
        "schema_version": update_input["schema_version"],
        "item_id": update_input["item_id"],
        "claim_id": update_input["claim_id"],
        "claim_text": update_input["claim_text"],
        "evidence_bundle": [
            {
                "bundle_position": item["bundle_position"],
                "evidence_id": item["evidence_id"],
                "source_group_id": validation_source_group(item),
                "passage_text": item["passage_text"],
            }
            for item in evidence_items
        ],
    }


def validate_judge_output_for_update(
    payload: dict[str, Any],
    update_input: dict[str, Any],
    *,
    omitted_evidence_fields: frozenset[str] | None = None,
) -> list[str]:
    return validate_judge_output(
        payload,
        as_multi_evidence_input(
            update_input,
            omitted_evidence_fields=omitted_evidence_fields,
        ),
    )


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
                unsupported = (
                    omitted_evidence_fields - ABLATION_REMOVABLE_EVIDENCE_FIELDS
                )
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
        expected_prompt_hash = str(config.get("prompt_sha256", ""))
        actual_prompt_hash = sha256_bytes(prompt_path.read_bytes())
        if expected_prompt_hash != actual_prompt_hash:
            errors.append(
                f"prompt_sha256 mismatch: expected {expected_prompt_hash}, got {actual_prompt_hash}"
            )

    response_schema_name = str(config.get("response_schema", ""))
    if response_schema_name not in EPISTEMIC_MULTI_EVIDENCE_JUDGE_SCHEMAS:
        errors.append(
            "response_schema must be one of "
            f"{sorted(EPISTEMIC_MULTI_EVIDENCE_JUDGE_SCHEMAS)}"
        )
    expected_schema_hash = str(config.get("response_schema_sha256", ""))
    actual_schema_hash = sha256_bytes(JUDGE_OUTPUT_SCHEMA_PATH.read_bytes())
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
        if set(spec) != {"condition_id", "execution_item_id", "input_file", "input_sha256"}:
            errors.append(f"{prefix} has unexpected or missing fields")
        condition_id = str(spec.get("condition_id", ""))
        execution_item_id = str(spec.get("execution_item_id", ""))
        condition_ids.append(condition_id)
        execution_ids.append(execution_item_id)
        path = input_dir / str(spec.get("input_file", ""))
        if not path.exists():
            errors.append(f"{prefix}: input does not exist: {path}")
            continue
        payload = load_json_object(path)
        if payload.get("item_id") != execution_item_id:
            errors.append(f"{prefix}: execution_item_id does not match file item_id")
        errors.extend(
            f"{prefix}: {error}"
            for error in validate_update_input(
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
    if design.get("recognition_calls") != 0:
        errors.append("pilot_design.recognition_calls must be 0 for the P1 verifier check")

    model_id = config.get("default_judge_model_id")
    models = config.get("models") or {}
    if model_id not in models:
        errors.append("default_judge_model_id is absent from models")
    else:
        model_spec = models[model_id]
        if model_spec.get("provider") != "codex_cli":
            errors.append("P1 GPT-5.5 sample currently expects provider=codex_cli")
        if model_spec.get("model") != "gpt-5.5":
            errors.append("P1 GPT-5.5 sample currently expects model=gpt-5.5")
        if model_spec.get("reasoning_effort") != "medium":
            errors.append("P1 GPT-5.5 sample currently expects reasoning_effort=medium")
        if model_spec.get("retries_per_repetition") != 1:
            errors.append("retries_per_repetition must be 1 so retries do not hide instability")

    prediction_path = resolve(Path(str(config.get("prediction_path", ""))))
    error_path = resolve(Path(str(config.get("error_path", ""))))
    if prediction_path == error_path:
        errors.append("prediction_path and error_path must be different")

    if errors:
        raise ValueError("EPISTEMIC_UPDATE_VERIFIER_PLAN=failed\n- " + "\n- ".join(errors))
    return config, prompt_text, loaded


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate or run the guarded epistemic-update neutral verifier."
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
    design = config["pilot_design"]
    repetitions = int(design["repetitions_per_input"])
    print(f"PASS  conditions: {design['condition_count']}")
    print(f"PASS  repetitions per condition: {repetitions}")
    print(f"PASS  planned verifier calls: {design['planned_model_calls']}")
    print(f"PASS  recognition calls: {design['recognition_calls']}")
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
        executions = [
            entry for entry in executions if entry["execution_item_id"] in requested
        ]

    selected_call_count = len(executions) * repetitions
    print(f"SELECTED_CONDITIONS={len(executions)}")
    print(f"SELECTED_MODEL_CALLS={selected_call_count}")

    if config.get("model_calls_enabled") is not True:
        raise RuntimeError("MODEL_CALL_GATE=closed: set model_calls_enabled=true only after approval")
    if not args.confirm_model_calls:
        raise RuntimeError("MODEL_CALL_GATE=closed: pass --confirm-model-calls after approval")

    model_id = str(config["default_judge_model_id"])
    model_spec = dict(config["models"][model_id])
    retries = int(model_spec.pop("retries_per_repetition"))
    response_schema_name = str(config["response_schema"])
    response_schema = EPISTEMIC_MULTI_EVIDENCE_JUDGE_SCHEMAS[response_schema_name]
    prediction_path = resolve(Path(config["prediction_path"]))
    error_path = resolve(Path(config["error_path"]))
    existing = load_jsonl(prediction_path) if prediction_path.exists() else []
    completed = {
        (str(row.get("execution_item_id")), int(row.get("repetition", 0)))
        for row in existing
        if row.get("response_status") == "ok"
    }
    pending = [
        (entry, repetition)
        for entry in executions
        for repetition in range(1, repetitions + 1)
        if (entry["execution_item_id"], repetition) not in completed
    ]
    print(f"PENDING_MODEL_CALLS={len(pending)}")
    client = create_client(model_spec, ROOT)
    prompt_path = ROOT / "prompts" / f"{config['prompt_version']}.txt"
    prompt_sha256 = sha256_bytes(prompt_path.read_bytes())
    omitted_evidence_fields = frozenset(
        (config.get("input_ablation") or {}).get("omitted_evidence_fields", [])
    )

    total_pending = len(pending)
    for index, (entry, repetition) in enumerate(pending, start=1):
        model_input = entry["model_input"]
        base = {
            "experiment_id": config["experiment_id"],
            "evaluator_id": f"{model_id}_{config['prompt_version']}",
            "model_id": model_id,
            "prompt_version": config["prompt_version"],
            "prompt_sha256": prompt_sha256,
            "input_sha256": entry["input_sha256"],
            "condition_id": entry["condition_id"],
            "execution_item_id": entry["execution_item_id"],
            "repetition": repetition,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        prompt = render_prompt(prompt_text, model_input)
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

        semantic_errors = validate_judge_output_for_update(
            payload,
            model_input,
            omitted_evidence_fields=omitted_evidence_fields,
        )
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
