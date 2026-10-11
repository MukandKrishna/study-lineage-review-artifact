from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any, Iterable, Iterator

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
PROCESSED = DATA / "processed"
ANNOTATIONS = DATA / "annotations"
PROMPTS = ROOT / "prompts"
RESULTS = ROOT / "results"

VALID_LABELS = {
    "supported",
    "unsupported",
    "contradicted",
    "not_enough_evidence",
}


def ensure_directories() -> None:
    for path in (RAW, PROCESSED, ANNOTATIONS, PROMPTS, RESULTS):
        path.mkdir(parents=True, exist_ok=True)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Required input does not exist: {path}")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in {path} at line {line_number}") from exc
    return rows


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def completed_ids(path: Path, key: str) -> set[str]:
    return {str(row[key]) for row in read_jsonl(path)} if path.exists() else set()


def load_prompt(name: str, **values: str) -> str:
    template = (PROMPTS / name).read_text(encoding="utf-8")
    return template.format(**values)


def extract_json_object(text: str) -> dict[str, Any]:
    """Parse a JSON object, tolerating a fenced response around it."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise ValueError("Model response did not contain a JSON object")
        value = json.loads(match.group(0))
    if not isinstance(value, dict):
        raise ValueError("Expected the model response to be a JSON object")
    return value


def evidence_sentences(evidence: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", evidence.strip())
    return [part.strip() for part in parts if part.strip()]


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def iter_missing(rows: Iterable[dict[str, Any]], done: set[str], key: str) -> Iterator[dict[str, Any]]:
    for row in rows:
        if str(row[key]) not in done:
            yield row


def load_split(path: Path) -> dict[str, str]:
    """Load the frozen example_id -> 'dev'/'test' assignment written by the split-assignment utility."""
    if not path.exists():
        raise FileNotFoundError(
            f"No dev/test split found at {path}. Create the required split file before tuning "
            "thresholds or filtering by split."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    invalid = {value for value in data.values() if value not in {"dev", "test"}}
    if invalid:
        raise ValueError(f"Split file has invalid values: {sorted(invalid)}")
    return data

