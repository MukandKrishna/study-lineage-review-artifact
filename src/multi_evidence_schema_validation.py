from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from common import ROOT


SCHEMA_DIR = ROOT / "schemas"
MODEL_INPUT_SCHEMA_PATH = SCHEMA_DIR / "model_input_multi_evidence_v1.schema.json"
JUDGE_OUTPUT_SCHEMA_PATH = SCHEMA_DIR / "model_output_multi_evidence_judge_v1.schema.json"
AUTHORING_RECORD_SCHEMA_PATH = SCHEMA_DIR / "authoring_record_multi_evidence_v1.schema.json"

PER_EVIDENCE_RELATIONS = {
    "supports",
    "conflicts",
    "insufficient",
    "out_of_scope",
}
COMBINED_LABELS = {
    "supported",
    "contradicted",
    "unsupported",
    "not_enough_evidence",
    "mixed_evidence",
}
COMBINATION_FLAGS = {
    "single_evidence",
    "independent_corroboration",
    "duplicate_evidence",
    "conflicting_evidence",
    "out_of_scope_evidence",
    "insufficient_evidence",
    "none",
}


def load_schema(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Schema must be a JSON object: {path}")
    return value


EPISTEMIC_MULTI_EVIDENCE_INPUT_SCHEMA = load_schema(MODEL_INPUT_SCHEMA_PATH)
EPISTEMIC_MULTI_EVIDENCE_JUDGE_SCHEMA = load_schema(JUDGE_OUTPUT_SCHEMA_PATH)
EPISTEMIC_MULTI_EVIDENCE_RECORD_SCHEMA = load_schema(AUTHORING_RECORD_SCHEMA_PATH)


def _without_unique_items(value: Any) -> Any:
    """Build an OpenAI Structured Outputs-compatible view of the frozen schema.

    OpenAI's supported JSON Schema subset rejects ``uniqueItems``. The project-level
    semantic validator still enforces occurrence consistency after every response, so
    this transport compatibility view does not change the accepted output contract.
    """
    if isinstance(value, dict):
        return {
            key: _without_unique_items(item)
            for key, item in value.items()
            if key != "uniqueItems"
        }
    if isinstance(value, list):
        return [_without_unique_items(item) for item in value]
    return value


EPISTEMIC_MULTI_EVIDENCE_JUDGE_OPENAI_SCHEMA = _without_unique_items(
    EPISTEMIC_MULTI_EVIDENCE_JUDGE_SCHEMA
)
EPISTEMIC_MULTI_EVIDENCE_JUDGE_SCHEMAS = {
    "epistemic_multi_evidence_judge_v1": EPISTEMIC_MULTI_EVIDENCE_JUDGE_SCHEMA,
    "epistemic_multi_evidence_judge_openai_v1": (
        EPISTEMIC_MULTI_EVIDENCE_JUDGE_OPENAI_SCHEMA
    ),
}


def _score_error(value: Any, field: str) -> str | None:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100:
        return f"{field} must be an integer from 0 to 100"
    return None


def validate_model_input(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {"schema_version", "item_id", "claim_id", "claim_text", "evidence_bundle"}
    if set(payload) != required:
        errors.append(f"model input keys must be exactly: {', '.join(sorted(required))}")
    if payload.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")
    for field in ("item_id", "claim_id", "claim_text"):
        if not isinstance(payload.get(field), str) or not payload.get(field, "").strip():
            errors.append(f"{field} must be a non-empty string")

    bundle = payload.get("evidence_bundle")
    if not isinstance(bundle, list) or not bundle:
        return errors + ["evidence_bundle must be a non-empty list"]

    expected_positions = list(range(1, len(bundle) + 1))
    actual_positions: list[Any] = []
    evidence_text: dict[str, str] = {}
    evidence_source: dict[str, str] = {}
    for index, item in enumerate(bundle):
        prefix = f"evidence_bundle[{index}]"
        required_item = {
            "bundle_position",
            "evidence_id",
            "source_group_id",
            "passage_text",
        }
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if set(item) != required_item:
            errors.append(f"{prefix} has unexpected or missing fields")
        actual_positions.append(item.get("bundle_position"))
        for field in ("evidence_id", "source_group_id", "passage_text"):
            if not isinstance(item.get(field), str) or not item.get(field, "").strip():
                errors.append(f"{prefix}.{field} must be a non-empty string")

        evidence_id = item.get("evidence_id")
        if isinstance(evidence_id, str) and evidence_id:
            passage_text = item.get("passage_text")
            source_group_id = item.get("source_group_id")
            if evidence_id in evidence_text and evidence_text[evidence_id] != passage_text:
                errors.append(f"{evidence_id} is repeated with different passage_text")
            if evidence_id in evidence_source and evidence_source[evidence_id] != source_group_id:
                errors.append(f"{evidence_id} is repeated with different source_group_id")
            evidence_text[evidence_id] = passage_text
            evidence_source[evidence_id] = source_group_id

    if actual_positions != expected_positions:
        errors.append(
            f"bundle_position values must be consecutive and ordered: {expected_positions}"
        )
    return errors


def validate_judge_output(
    payload: dict[str, Any], model_input: dict[str, Any]
) -> list[str]:
    errors = validate_model_input(model_input)
    if errors:
        return [f"invalid model input: {error}" for error in errors]

    required = {"item_id", "per_evidence_assessments", "combined_assessment"}
    if set(payload) != required:
        errors.append(f"judge output keys must be exactly: {', '.join(sorted(required))}")
    if payload.get("item_id") != model_input["item_id"]:
        errors.append("output item_id does not match input item_id")

    bundle = model_input["evidence_bundle"]
    expected_occurrences = [
        (item["bundle_position"], item["evidence_id"]) for item in bundle
    ]
    passages = {
        (item["bundle_position"], item["evidence_id"]): item["passage_text"]
        for item in bundle
    }
    assessments = payload.get("per_evidence_assessments")
    if not isinstance(assessments, list):
        errors.append("per_evidence_assessments must be a list")
        assessments = []

    actual_occurrences: list[tuple[Any, Any]] = []
    assessment_relations: list[str] = []
    required_assessment = {
        "bundle_position",
        "evidence_id",
        "relation_to_claim",
        "semantic_support_score",
        "warrant_strength_score",
        "confidence",
        "evidence_quote",
        "reason",
    }
    for index, assessment in enumerate(assessments):
        prefix = f"per_evidence_assessments[{index}]"
        if not isinstance(assessment, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if set(assessment) != required_assessment:
            errors.append(f"{prefix} has unexpected or missing fields")
        occurrence = (assessment.get("bundle_position"), assessment.get("evidence_id"))
        actual_occurrences.append(occurrence)
        relation = assessment.get("relation_to_claim")
        if relation not in PER_EVIDENCE_RELATIONS:
            errors.append(f"{prefix}.relation_to_claim is invalid")
        else:
            assessment_relations.append(relation)
        for field in ("semantic_support_score", "warrant_strength_score", "confidence"):
            error = _score_error(assessment.get(field), f"{prefix}.{field}")
            if error:
                errors.append(error)
        quote = assessment.get("evidence_quote")
        if not isinstance(quote, str) or not quote:
            errors.append(f"{prefix}.evidence_quote must be non-empty")
        elif occurrence in passages and quote not in passages[occurrence]:
            errors.append(f"{prefix}.evidence_quote is not an exact passage substring")
        if not isinstance(assessment.get("reason"), str) or not assessment.get("reason", "").strip():
            errors.append(f"{prefix}.reason must be non-empty")

    if actual_occurrences != expected_occurrences:
        errors.append("per-evidence assessments must match every bundle position in input order")

    combined = payload.get("combined_assessment")
    if not isinstance(combined, dict):
        return errors + ["combined_assessment must be an object"]
    required_combined = {
        "label",
        "combined_support_score",
        "combined_conflict_score",
        "warrant_strength_score",
        "confidence",
        "conflict_present",
        "used_evidence_ids",
        "ignored_evidence_ids",
        "used_bundle_positions",
        "ignored_bundle_positions",
        "combination_flags",
        "reason",
    }
    if set(combined) != required_combined:
        errors.append("combined_assessment has unexpected or missing fields")
    if combined.get("label") not in COMBINED_LABELS:
        errors.append("combined_assessment.label is invalid")
    for field in (
        "combined_support_score",
        "combined_conflict_score",
        "warrant_strength_score",
        "confidence",
    ):
        error = _score_error(combined.get(field), f"combined_assessment.{field}")
        if error:
            errors.append(error)
    if not isinstance(combined.get("conflict_present"), bool):
        errors.append("combined_assessment.conflict_present must be boolean")

    unique_ids = {item["evidence_id"] for item in bundle}
    valid_positions = {item["bundle_position"] for item in bundle}
    for field in ("used_evidence_ids", "ignored_evidence_ids"):
        values = combined.get(field)
        if not isinstance(values, list):
            errors.append(f"combined_assessment.{field} must be a list")
        elif not set(values) <= unique_ids:
            errors.append(f"combined_assessment.{field} contains an unknown evidence ID")
    for field in ("used_bundle_positions", "ignored_bundle_positions"):
        values = combined.get(field)
        if not isinstance(values, list) or len(values) != len(set(values)):
            errors.append(f"combined_assessment.{field} must be a unique list")
        elif not set(values) <= valid_positions:
            errors.append(f"combined_assessment.{field} contains an unknown position")

    used_positions = combined.get("used_bundle_positions", [])
    ignored_positions = combined.get("ignored_bundle_positions", [])
    if isinstance(used_positions, list) and isinstance(ignored_positions, list):
        if set(used_positions) & set(ignored_positions):
            errors.append("used and ignored bundle positions must not overlap")
        if set(used_positions) | set(ignored_positions) != valid_positions:
            errors.append("used and ignored bundle positions must partition the input bundle")
        position_to_id = {
            item["bundle_position"]: item["evidence_id"] for item in bundle
        }
        expected_used_ids = [position_to_id[position] for position in used_positions]
        expected_ignored_ids = [position_to_id[position] for position in ignored_positions]
        if combined.get("used_evidence_ids") != expected_used_ids:
            errors.append(
                "used_evidence_ids must match used_bundle_positions in the same order"
            )
        if combined.get("ignored_evidence_ids") != expected_ignored_ids:
            errors.append(
                "ignored_evidence_ids must match ignored_bundle_positions in the same order"
            )

    flags = combined.get("combination_flags")
    if not isinstance(flags, list) or not flags or len(flags) != len(set(flags)):
        errors.append("combined_assessment.combination_flags must be a non-empty unique list")
    elif not set(flags) <= COMBINATION_FLAGS:
        errors.append("combined_assessment.combination_flags contains an invalid flag")
    elif "none" in flags and len(flags) > 1:
        errors.append("combination flag none cannot be combined with another flag")

    expected_conflict = "conflicts" in assessment_relations
    if combined.get("conflict_present") is not expected_conflict:
        errors.append("conflict_present must agree with per-evidence conflict assessments")
    if combined.get("label") == "mixed_evidence":
        if not {"supports", "conflicts"} <= set(assessment_relations):
            errors.append("mixed_evidence requires both support and conflict assessments")
    if not isinstance(combined.get("reason"), str) or not combined.get("reason", "").strip():
        errors.append("combined_assessment.reason must be non-empty")
    return errors


def build_leak_free_model_input(record: dict[str, Any]) -> dict[str, Any]:
    catalog = {
        item["evidence_id"]: item for item in record["evidence_catalog"]
    }
    bundle = []
    for position, evidence_id in enumerate(record["ordered_evidence_ids"], start=1):
        evidence = catalog[evidence_id]
        bundle.append(
            {
                "bundle_position": position,
                "evidence_id": evidence_id,
                "source_group_id": evidence["source_group_id"],
                "passage_text": evidence["passage_text"],
            }
        )
    return {
        "schema_version": "1.0",
        "item_id": record["item_id"],
        "claim_id": record["claim"]["claim_id"],
        "claim_text": record["claim"]["text"],
        "evidence_bundle": bundle,
    }


def validate_authoring_record(record: dict[str, Any]) -> list[str]:
    """Validate integrity rules that the JSON schema cannot express by itself."""

    errors: list[str] = []
    required_pico = {
        "population",
        "intervention_or_exposure",
        "comparator",
        "outcome",
        "direction",
        "dose",
        "time_point",
    }

    def validate_pico(value: Any, prefix: str) -> None:
        if not isinstance(value, dict) or set(value) != required_pico:
            errors.append(f"{prefix} must contain exactly the frozen PICO/time fields")
            return
        for field, item in value.items():
            if not isinstance(item, str):
                errors.append(f"{prefix}.{field} must be a string")
    required_top_level = {
        "schema_version",
        "ruleset_id",
        "item_id",
        "family_id",
        "topic_id",
        "comparison_id",
        "relation_id",
        "condition_role",
        "split",
        "claim",
        "evidence_catalog",
        "ordered_evidence_ids",
        "gold",
        "transformation_log",
        "record_status",
    }
    if set(record) != required_top_level:
        errors.append("authoring record has unexpected or missing top-level fields")
    if record.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")
    if record.get("ruleset_id") != "epistemic_relation_rules_v1":
        errors.append("ruleset_id must be epistemic_relation_rules_v1")
    for field in ("item_id", "family_id", "topic_id", "comparison_id"):
        if not isinstance(record.get(field), str) or not record.get(field, "").strip():
            errors.append(f"{field} must be a non-empty string")
    if record.get("condition_role") not in {"reference", "intervention", "order_variant"}:
        errors.append("condition_role is invalid")
    if record.get("split") not in {"construction", "dev", "test"}:
        errors.append("split is invalid")
    if record.get("record_status") not in {"pending", "approved", "rejected"}:
        errors.append("record_status is invalid")

    claim = record.get("claim")
    if not isinstance(claim, dict):
        errors.append("claim must be an object")
    else:
        required_claim = {"claim_id", "text", "variant_role", "pico"}
        if set(claim) != required_claim:
            errors.append("claim has unexpected or missing fields")
        if not isinstance(claim.get("claim_id"), str) or not claim.get("claim_id", "").strip():
            errors.append("claim.claim_id must be non-empty")
        if not isinstance(claim.get("text"), str) or not claim.get("text", "").strip():
            errors.append("claim.text must be non-empty")
        if claim.get("variant_role") not in {"fixed", "stronger", "weaker"}:
            errors.append("claim.variant_role is invalid")
        validate_pico(claim.get("pico"), "claim.pico")

    catalog = record.get("evidence_catalog")
    if not isinstance(catalog, list) or not catalog:
        return errors + ["evidence_catalog must be a non-empty list"]

    evidence_by_id: dict[str, dict[str, Any]] = {}
    required_evidence = {
        "evidence_id",
        "source_group_id",
        "passage_text",
        "passage_sha256",
        "provenance",
        "pico",
        "construction_role",
        "independence_status",
        "human_review_status",
    }
    for index, evidence in enumerate(catalog):
        prefix = f"evidence_catalog[{index}]"
        if not isinstance(evidence, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if set(evidence) != required_evidence:
            errors.append(f"{prefix} has unexpected or missing fields")
        evidence_id = evidence.get("evidence_id")
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            errors.append(f"{prefix}.evidence_id must be non-empty")
            continue
        if evidence_id in evidence_by_id:
            errors.append(f"duplicate evidence_catalog ID: {evidence_id}")
        evidence_by_id[evidence_id] = evidence
        passage = evidence.get("passage_text")
        expected_hash = evidence.get("passage_sha256")
        if not isinstance(passage, str) or not passage:
            errors.append(f"{prefix}.passage_text must be non-empty")
        elif hashlib.sha256(passage.encode("utf-8")).hexdigest() != expected_hash:
            errors.append(f"{prefix}.passage_sha256 does not match UTF-8 passage text")
        provenance = evidence.get("provenance")
        required_provenance = {
            "source_title",
            "source_url",
            "pmid",
            "doi",
            "nct_id",
            "source_locator",
            "license_or_access_note",
            "exact_text_verified",
        }
        if not isinstance(provenance, dict) or set(provenance) != required_provenance:
            errors.append(f"{prefix}.provenance has unexpected or missing fields")
        elif provenance.get("exact_text_verified") is not True:
            errors.append(f"{prefix}.provenance must confirm exact_text_verified")
        validate_pico(evidence.get("pico"), f"{prefix}.pico")
        if evidence.get("construction_role") not in {
            "base_support",
            "independent_support",
            "matched_conflict",
            "scope_mismatch",
            "insufficient",
        }:
            errors.append(f"{prefix}.construction_role is invalid")
        if evidence.get("independence_status") not in {
            "base",
            "verified_independent",
            "same_source",
            "not_applicable",
            "unclear",
        }:
            errors.append(f"{prefix}.independence_status is invalid")
        if evidence.get("human_review_status") not in {"pending", "approved", "rejected"}:
            errors.append(f"{prefix}.human_review_status is invalid")
        if record.get("record_status") == "approved" and evidence.get(
            "human_review_status"
        ) != "approved":
            errors.append(f"{prefix} is not approved in an approved record")

    ordered_ids = record.get("ordered_evidence_ids")
    if not isinstance(ordered_ids, list) or not ordered_ids:
        errors.append("ordered_evidence_ids must be a non-empty list")
        ordered_ids = []
    unknown_ordered = set(ordered_ids) - set(evidence_by_id)
    if unknown_ordered:
        errors.append(f"ordered_evidence_ids contains unknown IDs: {sorted(unknown_ordered)}")
    unused_catalog = set(evidence_by_id) - set(ordered_ids)
    if unused_catalog:
        errors.append(f"evidence_catalog contains unused IDs: {sorted(unused_catalog)}")

    gold = record.get("gold")
    if not isinstance(gold, dict) or set(gold) != {"per_evidence", "combined"}:
        return errors + ["gold must contain exactly per_evidence and combined"]
    per_evidence = gold.get("per_evidence")
    if not isinstance(per_evidence, list) or not per_evidence:
        errors.append("gold.per_evidence must be a non-empty list")
        per_evidence = []
    gold_ids: list[str] = []
    gold_relations: list[str] = []
    for index, assessment in enumerate(per_evidence):
        prefix = f"gold.per_evidence[{index}]"
        if not isinstance(assessment, dict):
            errors.append(f"{prefix} must be an object")
            continue
        required_gold_item = {
            "evidence_id",
            "relation_to_claim",
            "decisive_quote",
            "rationale",
            "human_review_status",
        }
        if set(assessment) != required_gold_item:
            errors.append(f"{prefix} has unexpected or missing fields")
        evidence_id = assessment.get("evidence_id")
        gold_ids.append(evidence_id)
        relation = assessment.get("relation_to_claim")
        gold_relations.append(relation)
        if relation not in PER_EVIDENCE_RELATIONS:
            errors.append(f"{prefix}.relation_to_claim is invalid")
        evidence = evidence_by_id.get(evidence_id)
        quote = assessment.get("decisive_quote")
        if evidence is None:
            errors.append(f"{prefix} refers to unknown evidence ID")
        elif not isinstance(quote, str) or not quote or quote not in evidence["passage_text"]:
            errors.append(f"{prefix}.decisive_quote is not an exact passage substring")
        if record.get("record_status") == "approved" and assessment.get(
            "human_review_status"
        ) != "approved":
            errors.append(f"{prefix} is not approved in an approved record")
    if len(gold_ids) != len(set(gold_ids)):
        errors.append("gold.per_evidence contains duplicate evidence IDs")
    if set(gold_ids) != set(ordered_ids):
        errors.append("gold.per_evidence must cover every unique ordered evidence ID")

    combined = gold.get("combined")
    if not isinstance(combined, dict):
        return errors + ["gold.combined must be an object"]
    required_combined = {
        "acceptable_labels",
        "conflict_expected",
        "score_relation_to_reference",
        "expected_used_evidence_ids",
        "rationale",
        "human_review_status",
    }
    if set(combined) != required_combined:
        errors.append("gold.combined has unexpected or missing fields")
    acceptable_labels = combined.get("acceptable_labels")
    if not isinstance(acceptable_labels, list) or not acceptable_labels:
        errors.append("gold.combined.acceptable_labels must be non-empty")
    elif not set(acceptable_labels) <= COMBINED_LABELS:
        errors.append("gold.combined.acceptable_labels contains an invalid label")
    expected_used = combined.get("expected_used_evidence_ids")
    if not isinstance(expected_used, list) or not set(expected_used) <= set(ordered_ids):
        errors.append("gold.combined.expected_used_evidence_ids contains unknown IDs")
    conflict_expected = combined.get("conflict_expected")
    if not isinstance(conflict_expected, bool):
        errors.append("gold.combined.conflict_expected must be boolean")
    elif conflict_expected is not ("conflicts" in gold_relations):
        errors.append("gold.combined.conflict_expected disagrees with source-level gold")
    if "mixed_evidence" in (acceptable_labels or []) and not {
        "supports",
        "conflicts",
    } <= set(gold_relations):
        errors.append("mixed_evidence gold requires both support and conflict")
    if record.get("record_status") == "approved" and combined.get(
        "human_review_status"
    ) != "approved":
        errors.append("gold.combined is not approved in an approved record")
    if combined.get("score_relation_to_reference") not in {
        "higher",
        "equivalent",
        "lower",
        "not_scored",
    }:
        errors.append("gold.combined.score_relation_to_reference is invalid")

    transformation = record.get("transformation_log")
    required_transformation = {"changed_variable", "held_fixed_checks", "reviewer_notes"}
    if not isinstance(transformation, dict) or set(transformation) != required_transformation:
        errors.append("transformation_log has unexpected or missing fields")
    else:
        if not isinstance(transformation.get("changed_variable"), str) or not transformation.get(
            "changed_variable", ""
        ).strip():
            errors.append("transformation_log.changed_variable must be non-empty")
        checks = transformation.get("held_fixed_checks")
        if not isinstance(checks, list) or not checks or not all(
            isinstance(item, str) and item.strip() for item in checks
        ):
            errors.append("transformation_log.held_fixed_checks must be non-empty strings")
        if not isinstance(transformation.get("reviewer_notes"), str):
            errors.append("transformation_log.reviewer_notes must be a string")

    try:
        projected = build_leak_free_model_input(record)
    except (KeyError, TypeError) as exc:
        errors.append(f"leak-free projection failed: {exc}")
    else:
        errors.extend(f"projected input: {error}" for error in validate_model_input(projected))
    return errors


def validate_authoring_family(records: list[dict[str, Any]]) -> list[str]:
    """Validate cross-record pairing, provenance identity, and split isolation."""

    errors: list[str] = []
    if not records:
        return ["authoring family must contain at least one record"]
    item_ids = [record.get("item_id") for record in records]
    if len(item_ids) != len(set(item_ids)):
        errors.append("item_id values must be unique across records")

    evidence_fingerprints: dict[str, tuple[Any, ...]] = {}
    family_splits: dict[str, set[str]] = {}
    comparisons: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        errors.extend(
            f"{record.get('item_id', '<unknown>')}: {error}"
            for error in validate_authoring_record(record)
        )
        family_splits.setdefault(record.get("family_id"), set()).add(record.get("split"))
        comparisons.setdefault(record.get("comparison_id"), []).append(record)
        for evidence in record.get("evidence_catalog", []):
            fingerprint = (
                evidence.get("source_group_id"),
                evidence.get("passage_sha256"),
                json.dumps(evidence.get("provenance"), sort_keys=True),
            )
            evidence_id = evidence.get("evidence_id")
            if evidence_id in evidence_fingerprints and evidence_fingerprints[evidence_id] != fingerprint:
                errors.append(f"{evidence_id} changes text, source group, or provenance across records")
            evidence_fingerprints[evidence_id] = fingerprint
    for family_id, splits in family_splits.items():
        if len(splits) != 1:
            errors.append(f"family {family_id} crosses data splits: {sorted(splits)}")

    comparison_roles: dict[str, dict[str, dict[str, Any]]] = {}
    for comparison_id, pair in comparisons.items():
        roles = {record.get("condition_role"): record for record in pair}
        relation_id = pair[0].get("relation_id") if pair else None
        expected_roles = (
            {"reference", "order_variant"}
            if relation_id == "evidence_order_reversal_v1"
            else {"reference", "intervention"}
        )
        if len(pair) != 2 or set(roles) != expected_roles:
            errors.append(
                f"comparison {comparison_id} must have exactly roles {sorted(expected_roles)}"
            )
            continue
        comparison_roles[comparison_id] = roles
        reference = roles["reference"]
        intervention = roles.get("intervention", roles.get("order_variant"))
        if intervention is None:
            errors.append(f"comparison {comparison_id} has no comparison condition")
            continue
        for field in ("family_id", "topic_id", "comparison_id", "relation_id", "split"):
            if reference.get(field) != intervention.get(field):
                errors.append(f"comparison {comparison_id} changes held-fixed field {field}")
        if reference.get("claim") != intervention.get("claim"):
            errors.append(f"comparison {comparison_id} changes the fixed claim")
        reference_order = reference.get("ordered_evidence_ids", [])
        intervention_order = intervention.get("ordered_evidence_ids", [])
        reference_catalog = {
            evidence["evidence_id"]: evidence for evidence in reference.get("evidence_catalog", [])
        }
        intervention_catalog = {
            evidence["evidence_id"]: evidence
            for evidence in intervention.get("evidence_catalog", [])
        }
        for evidence_id, evidence in reference_catalog.items():
            if intervention_catalog.get(evidence_id) != evidence:
                errors.append(f"comparison {comparison_id} changes base evidence {evidence_id}")

        added_ids: list[str] = []
        added: dict[str, Any] | None = None
        if relation_id in {
            "evidence_independent_corroboration_v1",
            "evidence_matched_conflict_v1",
            "evidence_exact_duplication_v1",
        }:
            if intervention_order[: len(reference_order)] != reference_order:
                errors.append(
                    f"comparison {comparison_id} does not preserve the reference bundle prefix"
                )
            if len(intervention_order) != len(reference_order) + 1:
                errors.append(f"comparison {comparison_id} must add exactly one bundle item")
            added_ids = intervention_order[len(reference_order) :]
            added = intervention_catalog.get(added_ids[0]) if len(added_ids) == 1 else None
        elif relation_id == "evidence_order_reversal_v1":
            if intervention_catalog != reference_catalog:
                errors.append(f"comparison {comparison_id} changes the evidence catalog under order reversal")
            if sorted(intervention_order) != sorted(reference_order):
                errors.append(f"comparison {comparison_id} changes the evidence-ID multiset")
            if len(reference_order) < 2 or intervention_order != list(reversed(reference_order)):
                errors.append(f"comparison {comparison_id} is not an exact order reversal")

        intervention_gold = {
            item["evidence_id"]: item["relation_to_claim"]
            for item in intervention.get("gold", {}).get("per_evidence", [])
        }
        combined = intervention.get("gold", {}).get("combined", {})
        if relation_id == "evidence_independent_corroboration_v1" and added:
            if added.get("independence_status") != "verified_independent":
                errors.append(f"comparison {comparison_id} added evidence is not verified independent")
            if intervention_gold.get(added["evidence_id"]) != "supports":
                errors.append(f"comparison {comparison_id} corroborating evidence is not gold support")
            if combined.get("conflict_expected") is not False:
                errors.append(f"comparison {comparison_id} unexpectedly expects conflict")
        if relation_id == "evidence_matched_conflict_v1" and added:
            if intervention_gold.get(added["evidence_id"]) != "conflicts":
                errors.append(f"comparison {comparison_id} added evidence is not gold conflict")
            if combined.get("conflict_expected") is not True:
                errors.append(f"comparison {comparison_id} must expect conflict")
            if "mixed_evidence" not in combined.get("acceptable_labels", []):
                errors.append(f"comparison {comparison_id} must allow mixed_evidence")
        if relation_id == "evidence_exact_duplication_v1":
            if len(reference_order) != 1 or intervention_order != [reference_order[0]] * 2:
                errors.append(f"comparison {comparison_id} is not an exact [E1] to [E1, E1] duplicate")
            if intervention_catalog != reference_catalog:
                errors.append(f"comparison {comparison_id} creates a false second source for a duplicate")
            if combined.get("score_relation_to_reference") != "equivalent":
                errors.append(f"comparison {comparison_id} duplicate score relation must be equivalent")
        if relation_id == "evidence_order_reversal_v1":
            if combined.get("score_relation_to_reference") != "equivalent":
                errors.append(f"comparison {comparison_id} order score relation must be equivalent")

    corroboration_pairs = [
        roles
        for roles in comparison_roles.values()
        if roles["reference"].get("relation_id") == "evidence_independent_corroboration_v1"
    ]
    duplication_pairs = [
        roles
        for roles in comparison_roles.values()
        if roles["reference"].get("relation_id") == "evidence_exact_duplication_v1"
    ]
    for corroboration in corroboration_pairs if duplication_pairs else []:
        corr_reference = corroboration["reference"]
        matching_duplicates = [
            duplicate
            for duplicate in duplication_pairs
            if duplicate["reference"].get("claim") == corr_reference.get("claim")
            and duplicate["reference"].get("ordered_evidence_ids")
            == corr_reference.get("ordered_evidence_ids")
            and duplicate["reference"].get("evidence_catalog")
            == corr_reference.get("evidence_catalog")
        ]
        if len(matching_duplicates) != 1:
            errors.append(
                "each corroboration comparison must have exactly one exact-duplication comparison "
                "sharing the same base for the derived marginal-gain contrast"
            )
    return errors
