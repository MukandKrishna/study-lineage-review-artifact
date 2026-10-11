from __future__ import annotations

import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


EXPERIMENT_ID = "evidence_calibration_pilot_v1"
AXES = ("study_design", "effect_precision", "pico_directness", "risk_of_bias")
CONDITIONS = ("stronger", "weaker")
VALID_LABELS = {
    "supported",
    "unsupported",
    "contradicted",
    "not_enough_evidence",
}
APPROVED_REVIEW_STATUSES = {"approved", "corrected"}


def build_pilot_scaffold(pairs_per_axis: int = 8) -> list[dict[str, Any]]:
    """Build a balanced, empty pilot scaffold without inventing clinical content."""
    if pairs_per_axis < 1:
        raise ValueError("pairs_per_axis must be positive")
    rows: list[dict[str, Any]] = []
    pair_number = 0
    for axis in AXES:
        for _ in range(pairs_per_axis):
            pair_number += 1
            pair_id = f"ECAL_P{pair_number:03d}"
            claim_id = f"ECAL_C{pair_number:03d}"
            for condition in CONDITIONS:
                rows.append({
                    "experiment_id": EXPERIMENT_ID,
                    "item_id": f"{pair_id}_{condition.upper()}",
                    "pair_id": pair_id,
                    "claim_id": claim_id,
                    "split": "pilot_dev",
                    "medical_topic": "",
                    "evidence_axis": axis,
                    "evidence_condition": condition,
                    "claim_text": "",
                    "evidence_text": "",
                    "source_dataset": "",
                    "source_document_id": "",
                    "source_url_or_doi": "",
                    "source_exact_quote": "",
                    "is_real_source_passage": None,
                    "transformation_type": "pending",
                    "transformation_description": "",
                    "lexical_cue_condition": "pending",
                    "gold_support_label": "",
                    "gold_evidence_strength": None,
                    "expected_order": "stronger>weaker",
                    "expected_label_transition": None,
                    "human_review_status": "pending",
                    "clinical_validity_flag": "unreviewed",
                    "reviewer_notes": "",
                })
    return rows


def validate_pilot_rows(
    rows: Iterable[dict[str, Any]],
    *,
    pairs_per_axis: int = 8,
    require_model_ready: bool = False,
) -> list[str]:
    """Return human-readable validation errors for dataset and paid-call gates."""
    materialized = list(rows)
    errors: list[str] = []
    expected_pairs = len(AXES) * pairs_per_axis
    expected_rows = expected_pairs * len(CONDITIONS)
    if len(materialized) != expected_rows:
        errors.append(f"expected {expected_rows} rows, found {len(materialized)}")

    item_ids = [str(row.get("item_id", "")) for row in materialized]
    duplicate_items = sorted(item for item, count in Counter(item_ids).items() if count > 1)
    if duplicate_items:
        errors.append(f"duplicate item_id values: {duplicate_items}")

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in materialized:
        grouped[str(row.get("pair_id", ""))].append(row)
        if row.get("experiment_id") != EXPERIMENT_ID:
            errors.append(f"{row.get('item_id')}: wrong experiment_id")
        if row.get("split") != "pilot_dev":
            errors.append(f"{row.get('item_id')}: split must be pilot_dev")
        if row.get("evidence_axis") not in AXES:
            errors.append(f"{row.get('item_id')}: invalid evidence_axis")
        if row.get("evidence_condition") not in CONDITIONS:
            errors.append(f"{row.get('item_id')}: invalid evidence_condition")
        if row.get("expected_order") != "stronger>weaker":
            errors.append(f"{row.get('item_id')}: expected_order must be stronger>weaker")

    if len(grouped) != expected_pairs:
        errors.append(f"expected {expected_pairs} pair_id values, found {len(grouped)}")

    axis_pair_counts: Counter[str] = Counter()
    for pair_id, pair_rows in sorted(grouped.items()):
        conditions = Counter(str(row.get("evidence_condition", "")) for row in pair_rows)
        if conditions != Counter(CONDITIONS):
            errors.append(f"{pair_id}: expected exactly one stronger and one weaker row")
            continue
        axes = {str(row.get("evidence_axis", "")) for row in pair_rows}
        if len(axes) != 1:
            errors.append(f"{pair_id}: evidence_axis differs within pair")
        else:
            axis_pair_counts[next(iter(axes))] += 1
        claims = {str(row.get("claim_text", "")) for row in pair_rows}
        if len(claims) != 1:
            errors.append(f"{pair_id}: claim_text differs within pair")
        transitions = {row.get("expected_label_transition") for row in pair_rows}
        if len(transitions) != 1:
            errors.append(f"{pair_id}: expected_label_transition differs within pair")

    for axis in AXES:
        if axis_pair_counts[axis] != pairs_per_axis:
            errors.append(
                f"{axis}: expected {pairs_per_axis} pairs, found {axis_pair_counts[axis]}"
            )

    if require_model_ready:
        for row in materialized:
            item_id = str(row.get("item_id", "<missing>"))
            required_text = (
                "claim_text",
                "evidence_text",
                "source_document_id",
                "source_url_or_doi",
                "transformation_description",
            )
            for field in required_text:
                if not str(row.get(field, "")).strip():
                    errors.append(f"{item_id}: {field} is required before model calls")
            if row.get("human_review_status") not in APPROVED_REVIEW_STATUSES:
                errors.append(f"{item_id}: human review is not approved")
            if row.get("clinical_validity_flag") != "clear":
                errors.append(f"{item_id}: clinical validity is not clear")
            if row.get("gold_support_label") not in VALID_LABELS:
                errors.append(f"{item_id}: gold_support_label is missing or invalid")
            strength = row.get("gold_evidence_strength")
            if not isinstance(strength, int) or not 0 <= strength <= 3:
                errors.append(f"{item_id}: gold_evidence_strength must be an integer 0..3")
            quote = str(row.get("source_exact_quote", ""))
            evidence = str(row.get("evidence_text", ""))
            if quote and quote not in evidence:
                errors.append(f"{item_id}: source_exact_quote is not an evidence substring")

    return errors


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON at {path}:{line_number}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"expected JSON object at {path}:{line_number}")
            rows.append(value)
    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def median_score(values: Iterable[float]) -> float:
    numeric = [float(value) for value in values]
    if not numeric:
        raise ValueError("at least one score is required")
    return float(statistics.median(numeric))
