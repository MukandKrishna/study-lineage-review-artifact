"""Run a frozen verifier or recognition plan with a local Transformers model.

The JSON configuration remains the source of truth for inputs, prompts, schemas,
and repetitions.  This runner only replaces the remote provider with a pinned
local model checkpoint.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

MODEL_REGISTRY: dict[str, dict[str, str]] = {
    "qwen3_4b": {
        "model_id": "Qwen/Qwen3-4B-Instruct-2507",
        "revision": "cdbee75f17c01a7cc42f958dc650907174af0554",
    },
    "gemma3_4b": {
        "model_id": "google/gemma-3-4b-it",
        "revision": "093f9f388b31de276ce2de164bdc2081324b9767",
    },
    "llama3_1_8b": {
        "model_id": "meta-llama/Llama-3.1-8B-Instruct",
        "revision": "0e9e39f249a16976918f6564b8830bc894c89659",
    },
    "ministral3_8b": {
        "model_id": "mistralai/Ministral-3-8B-Instruct-2512-BF16",
        "revision": "f6fae9795746f63c9be8344932f01275f3c63734",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve(path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else ROOT / candidate


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def load_plan(config_path: Path) -> tuple[dict[str, Any], str, list[dict[str, Any]], str]:
    config = read_json(config_path)
    prompt_path = ROOT / "prompts" / f"{config['prompt_version']}.txt"
    if not prompt_path.is_file():
        raise FileNotFoundError(prompt_path)
    prompt_text = prompt_path.read_text(encoding="utf-8")

    input_dir = resolve(config["input_directory"])
    executions = config.get("executions")
    if not isinstance(executions, list) or not executions:
        raise ValueError("config.executions must be a non-empty list")

    loaded: list[dict[str, Any]] = []
    for spec in executions:
        if not isinstance(spec, dict):
            raise ValueError("Each execution must be an object")
        path = input_dir / str(spec["input_file"])
        if not path.is_file():
            raise FileNotFoundError(path)
        actual_hash = sha256(path)
        if actual_hash != spec.get("input_sha256"):
            raise ValueError(f"Input hash mismatch: {path}")
        loaded.append(
            {
                "condition_id": str(spec["condition_id"]),
                "execution_item_id": str(spec["execution_item_id"]),
                "input_sha256": actual_hash,
                "model_input": read_json(path),
            }
        )

    response_schema = str(config.get("response_schema", ""))
    task = "recognition" if "comparative_recognition" in response_schema else "verifier"
    return config, prompt_text, loaded, task


def parse_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].rstrip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("Model output did not contain a JSON object")
    value = json.loads(cleaned[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("Model output JSON was not an object")
    return value


def render_prompt(prompt_text: str, model_input: dict[str, Any], task: str, config: dict[str, Any]) -> str:
    omitted = frozenset((config.get("input_ablation") or {}).get("omitted_evidence_fields", []))
    if task == "verifier":
        module = importlib.import_module("44_run_epistemic_update_verifier")
        visible = module.as_multi_evidence_input(model_input, omitted_evidence_fields=omitted)
    else:
        module = importlib.import_module("46_run_epistemic_update_comparative_recognition")
        visible = module.comparative_model_input_json(
            model_input, omitted_evidence_fields=omitted
        )
        return prompt_text.replace("{model_input_json}", visible)
    return prompt_text.replace(
        "{model_input_json}", json.dumps(visible, indent=2, ensure_ascii=False)
    )


def validate_payload(payload: dict[str, Any], model_input: dict[str, Any], task: str, config: dict[str, Any]) -> list[str]:
    omitted = frozenset((config.get("input_ablation") or {}).get("omitted_evidence_fields", []))
    if task == "verifier":
        module = importlib.import_module("44_run_epistemic_update_verifier")
        return module.validate_judge_output_for_update(
            payload, model_input, omitted_evidence_fields=omitted
        )
    module = importlib.import_module("46_run_epistemic_update_comparative_recognition")
    return module.validate_comparative_output(payload, model_input)


def make_model(model_id: str, revision: str, device: str) -> tuple[Any, Any]:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision)
    kwargs: dict[str, Any] = {"revision": revision, "device_map": device}
    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    try:
        model = AutoModelForCausalLM.from_pretrained(model_id, dtype=dtype, **kwargs)
    except TypeError:
        model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=dtype, **kwargs)
    model.eval()
    return tokenizer, model


def generate(model: Any, tokenizer: Any, prompt: str, max_new_tokens: int) -> str:
    import torch

    if hasattr(tokenizer, "apply_chat_template"):
        encoded = tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            add_generation_prompt=True,
            return_tensors="pt",
        )
        inputs = {"input_ids": encoded}
        if hasattr(encoded, "attention_mask"):
            inputs["attention_mask"] = encoded.attention_mask
    else:
        inputs = tokenizer(prompt, return_tensors="pt")
    device = next(model.parameters()).device
    inputs = {key: value.to(device) for key, value in inputs.items()}
    with torch.inference_mode():
        output = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    prompt_length = inputs["input_ids"].shape[-1]
    return tokenizer.decode(output[0][prompt_length:], skip_special_tokens=True)


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a frozen plan with a pinned Transformers model.")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--model-key", choices=sorted(MODEL_REGISTRY), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--max-new-tokens", type=int, default=2048)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--allow-model-calls", action="store_true")
    args = parser.parse_args()

    config, prompt_text, executions, task = load_plan(resolve(args.config))
    design = config.get("pilot_design", {})
    repetitions = int(design.get("repetitions_per_input", 5))
    model_spec = MODEL_REGISTRY[args.model_key]
    print(f"PASS task={task} conditions={len(executions)} repetitions={repetitions}")
    print(f"PASS model={model_spec['model_id']} revision={model_spec['revision']}")
    print(f"PASS planned_calls={len(executions) * repetitions}")
    if args.validate_only:
        print("MODEL_CALLS=0")
        return
    if not args.allow_model_calls:
        raise RuntimeError("Model calls are disabled. Add --allow-model-calls after local approval.")

    output_dir = resolve(args.output_dir)
    prediction_path = output_dir / "predictions.jsonl"
    error_path = output_dir / "errors.jsonl"
    completed: set[tuple[str, int]] = set()
    if prediction_path.is_file():
        for line in prediction_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                completed.add((str(row["execution_item_id"]), int(row["repetition"])))
    tokenizer, model = make_model(model_spec["model_id"], model_spec["revision"], args.device)
    selected = executions if args.limit is None else executions[: args.limit]
    total = len(selected) * repetitions
    done = 0
    for entry in selected:
        for repetition in range(1, repetitions + 1):
            key = (entry["execution_item_id"], repetition)
            if key in completed:
                continue
            base = {
                "experiment_id": config.get("experiment_id"),
                "task": task,
                "model_key": args.model_key,
                "model_id": model_spec["model_id"],
                "model_revision": model_spec["revision"],
                "condition_id": entry["condition_id"],
                "execution_item_id": entry["execution_item_id"],
                "input_sha256": entry["input_sha256"],
                "prompt_version": config.get("prompt_version"),
                "repetition": repetition,
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
            }
            try:
                raw = generate(model, tokenizer, render_prompt(prompt_text, entry["model_input"], task, config), args.max_new_tokens)
                payload = parse_json(raw)
                errors = validate_payload(payload, entry["model_input"], task, config)
                if errors:
                    raise ValueError("; ".join(errors))
                append_jsonl(prediction_path, {**base, "response_status": "ok", **payload})
            except Exception as exc:  # record a failed call and continue the plan
                append_jsonl(error_path, {**base, "response_status": "error", "error": str(exc)})
            done += 1
            print(f"CALL_PROGRESS {done}/{total} {entry['execution_item_id']} rep={repetition}", flush=True)

    manifest = {
        "experiment_id": config.get("experiment_id"),
        "task": task,
        "model_key": args.model_key,
        "model_id": model_spec["model_id"],
        "model_revision": model_spec["revision"],
        "config": str(resolve(args.config).relative_to(ROOT)),
        "planned_calls": len(executions) * repetitions,
        "output_directory": str(output_dir.relative_to(ROOT)),
    }
    (output_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"RESULTS={output_dir}")


if __name__ == "__main__":
    main()
