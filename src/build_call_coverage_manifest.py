"""Build a compact coverage table from recorded open-weight outputs."""

from __future__ import annotations

import csv
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "experiments" / "epistemic_update_feasibility_v1" / "records" / "model_outputs"
TARGET = ROOT / "results" / "final_naacl" / "call_coverage_manifest.csv"

# GPT records are stored in the provider-specific predictions directory rather
# than under records/model_outputs. Keep their paper-facing coverage explicit.
RECORDED_EXTRA_ROWS = [
    {
        "model_package": "gpt_5_5/primary_10_family",
        "model_id": "openai/gpt-5.5",
        "revision": "",
        "planned_calls": 330,
        "predictions": 330,
        "errors": 0,
        "reported_scope": "primary",
    },
    {
        "model_package": "gpt_5_5/prompt_robustness_40",
        "model_id": "openai/gpt-5.5",
        "revision": "",
        "planned_calls": 40,
        "predictions": 40,
        "errors": 0,
        "reported_scope": "secondary",
    },
    {
        "model_package": "gpt_5_5/lineage_overlap_4",
        "model_id": "openai/gpt-5.5",
        "revision": "",
        "planned_calls": 20,
        "predictions": 20,
        "errors": 0,
        "reported_scope": "exploratory",
    },
]


def line_count(path: Path) -> int:
    if not path.is_file():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def package_scope(package_key: str) -> str:
    if "primary_10_family" in package_key:
        return "primary"
    if "prompt_robustness" in package_key:
        return "secondary"
    if "lineage_overlap" in package_key:
        return "exploratory"
    if "p6r_repair" in package_key or "diagnostic" in package_key:
        return "diagnostic"
    if "later_220" in package_key:
        return "later"
    return ""


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a call-coverage CSV.")
    parser.add_argument("--output", type=Path, default=TARGET)
    args = parser.parse_args()
    rows_by_package: dict[str, dict[str, object]] = {}
    if TARGET.is_file():
        with TARGET.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                rows_by_package[row["model_package"]] = row
    for manifest_path in sorted(SOURCE.rglob("run_manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        package = manifest_path.parent
        model = manifest.get("model", {})
        package_key = str(package.relative_to(SOURCE)).replace("\\", "/")
        rows_by_package[package_key] = {
                "model_package": package_key,
                "model_id": model.get("repo_id", ""),
                "revision": model.get("revision", ""),
                "planned_calls": manifest.get("planned_calls", ""),
                "predictions": line_count(package / "predictions.jsonl"),
                "errors": line_count(package / "errors.jsonl"),
                "reported_scope": package_scope(package_key),
        }
    for row in RECORDED_EXTRA_ROWS:
        rows_by_package[row["model_package"]] = row
    rows = [rows_by_package[key] for key in sorted(rows_by_package)]
    target = args.output if args.output.is_absolute() else ROOT / args.output
    target.parent.mkdir(parents=True, exist_ok=True)
    fields = ["model_package", "model_id", "revision", "planned_calls", "predictions", "errors", "reported_scope"]
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {target}")


if __name__ == "__main__":
    main()
