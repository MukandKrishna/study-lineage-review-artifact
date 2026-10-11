from __future__ import annotations

import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from multi_evidence_schema_validation import (
    EPISTEMIC_MULTI_EVIDENCE_JUDGE_OPENAI_SCHEMA,
    EPISTEMIC_MULTI_EVIDENCE_INPUT_SCHEMA,
    EPISTEMIC_MULTI_EVIDENCE_JUDGE_SCHEMA,
    EPISTEMIC_MULTI_EVIDENCE_RECORD_SCHEMA,
    build_leak_free_model_input,
    validate_authoring_family,
    validate_authoring_record,
    validate_judge_output,
    validate_model_input,
)


PASSAGE_1 = "The trial reported fewer events with treatment A than placebo at 12 weeks."
PASSAGE_2 = "A separate trial reported fewer events with treatment A than placebo at 12 weeks."


def model_input() -> dict:
    return {
        "schema_version": "1.0",
        "item_id": "ITEM_001",
        "claim_id": "CLAIM_001",
        "claim_text": "Treatment A reduced events compared with placebo at 12 weeks.",
        "evidence_bundle": [
            {
                "bundle_position": 1,
                "evidence_id": "E1",
                "source_group_id": "SOURCE_GROUP_1",
                "passage_text": PASSAGE_1,
            },
            {
                "bundle_position": 2,
                "evidence_id": "E2",
                "source_group_id": "SOURCE_GROUP_2",
                "passage_text": PASSAGE_2,
            },
        ],
    }


def valid_output() -> dict:
    return {
        "item_id": "ITEM_001",
        "per_evidence_assessments": [
            {
                "bundle_position": 1,
                "evidence_id": "E1",
                "relation_to_claim": "supports",
                "semantic_support_score": 90,
                "warrant_strength_score": 80,
                "confidence": 90,
                "evidence_quote": "fewer events with treatment A than placebo",
                "reason": "The passage directly reports the requested comparison.",
            },
            {
                "bundle_position": 2,
                "evidence_id": "E2",
                "relation_to_claim": "supports",
                "semantic_support_score": 90,
                "warrant_strength_score": 80,
                "confidence": 90,
                "evidence_quote": "fewer events with treatment A than placebo",
                "reason": "The separate passage reports the same comparison.",
            },
        ],
        "combined_assessment": {
            "label": "supported",
            "combined_support_score": 95,
            "combined_conflict_score": 0,
            "warrant_strength_score": 90,
            "confidence": 90,
            "conflict_present": False,
            "used_evidence_ids": ["E1", "E2"],
            "ignored_evidence_ids": [],
            "used_bundle_positions": [1, 2],
            "ignored_bundle_positions": [],
            "combination_flags": ["independent_corroboration"],
            "reason": "Both evidence items support the complete claim.",
        },
    }


def test_three_frozen_schemas_are_closed_objects() -> None:
    for schema in (
        EPISTEMIC_MULTI_EVIDENCE_INPUT_SCHEMA,
        EPISTEMIC_MULTI_EVIDENCE_JUDGE_SCHEMA,
        EPISTEMIC_MULTI_EVIDENCE_RECORD_SCHEMA,
    ):
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False
        assert schema["required"]


def test_model_input_and_output_semantic_validation_pass() -> None:
    input_payload = model_input()
    assert validate_model_input(input_payload) == []
    assert validate_judge_output(valid_output(), input_payload) == []


def test_openai_schema_view_removes_only_transport_unique_items_constraint() -> None:
    assert '"uniqueItems"' in json.dumps(EPISTEMIC_MULTI_EVIDENCE_JUDGE_SCHEMA)
    assert '"uniqueItems"' not in json.dumps(
        EPISTEMIC_MULTI_EVIDENCE_JUDGE_OPENAI_SCHEMA
    )
    output = valid_output()
    output["combined_assessment"]["used_evidence_ids"] = ["E1", "E1"]
    errors = validate_judge_output(output, model_input())
    assert any("must match used_bundle_positions" in error for error in errors)


def test_duplicate_occurrences_can_repeat_the_same_evidence_id() -> None:
    input_payload = model_input()
    input_payload["evidence_bundle"][1] = {
        **input_payload["evidence_bundle"][0],
        "bundle_position": 2,
    }
    output = valid_output()
    output["per_evidence_assessments"][1] = {
        **output["per_evidence_assessments"][0],
        "bundle_position": 2,
    }
    output["combined_assessment"]["used_evidence_ids"] = ["E1", "E1"]
    assert validate_judge_output(output, input_payload) == []


def test_output_requires_every_bundle_occurrence_and_exact_quote() -> None:
    input_payload = model_input()
    output = valid_output()
    output["per_evidence_assessments"].pop()
    output["per_evidence_assessments"][0]["evidence_quote"] = "not an exact quote"
    errors = validate_judge_output(output, input_payload)
    assert any("not an exact passage substring" in error for error in errors)
    assert any("must match every bundle position" in error for error in errors)


def test_duplicate_input_requires_same_text_and_source_group() -> None:
    input_payload = model_input()
    input_payload["evidence_bundle"][1]["evidence_id"] = "E1"
    errors = validate_model_input(input_payload)
    assert any("repeated with different passage_text" in error for error in errors)
    assert any("repeated with different source_group_id" in error for error in errors)


def test_mixed_label_requires_support_and_conflict() -> None:
    output = valid_output()
    output["combined_assessment"]["label"] = "mixed_evidence"
    errors = validate_judge_output(output, model_input())
    assert any("requires both support and conflict" in error for error in errors)


def test_authoring_record_projection_excludes_gold_and_provenance() -> None:
    pico = {
        "population": "Adults in the displayed trial",
        "intervention_or_exposure": "Treatment A",
        "comparator": "Placebo",
        "outcome": "Events",
        "direction": "Lower",
        "dose": "",
        "time_point": "12 weeks",
    }
    evidence = {
        "evidence_id": "E1",
        "source_group_id": "SOURCE_GROUP_1",
        "passage_text": PASSAGE_1,
        "passage_sha256": hashlib.sha256(PASSAGE_1.encode("utf-8")).hexdigest(),
        "provenance": {
            "source_title": "Example source",
            "source_url": "https://example.org/source",
            "pmid": None,
            "doi": None,
            "nct_id": None,
            "source_locator": "abstract",
            "license_or_access_note": "Test fixture only",
            "exact_text_verified": True,
        },
        "pico": pico,
        "construction_role": "base_support",
        "independence_status": "base",
        "human_review_status": "approved",
    }
    record = {
        "schema_version": "1.0",
        "ruleset_id": "epistemic_relation_rules_v1",
        "item_id": "ITEM_001",
        "family_id": "FAMILY_001",
        "topic_id": "TOPIC_001",
        "comparison_id": "COMPARISON_001",
        "relation_id": "evidence_exact_duplication_v1",
        "condition_role": "reference",
        "split": "construction",
        "claim": {
            "claim_id": "CLAIM_001",
            "text": "Treatment A reduced events compared with placebo at 12 weeks.",
            "variant_role": "fixed",
            "pico": pico,
        },
        "evidence_catalog": [evidence],
        "ordered_evidence_ids": ["E1", "E1"],
        "gold": {"secret": "must not be projected"},
        "transformation_log": {},
        "record_status": "approved",
    }
    projected = build_leak_free_model_input(record)
    assert validate_model_input(projected) == []
    assert "gold" not in projected
    assert "relation_id" not in projected
    assert "provenance" not in projected
    assert [item["evidence_id"] for item in projected["evidence_bundle"]] == ["E1", "E1"]


def approved_authoring_record() -> dict:
    pico = {
        "population": "Adults in the displayed trial",
        "intervention_or_exposure": "Treatment A",
        "comparator": "Placebo",
        "outcome": "Events",
        "direction": "Lower",
        "dose": "10 mg daily",
        "time_point": "12 weeks",
    }
    evidence = {
        "evidence_id": "E1",
        "source_group_id": "SOURCE_GROUP_1",
        "passage_text": PASSAGE_1,
        "passage_sha256": hashlib.sha256(PASSAGE_1.encode("utf-8")).hexdigest(),
        "provenance": {
            "source_title": "Example source",
            "source_url": "https://example.org/source",
            "pmid": "1",
            "doi": "10.0/example",
            "nct_id": "NCT00000001",
            "source_locator": "Results paragraph",
            "license_or_access_note": "Test fixture only",
            "exact_text_verified": True,
        },
        "pico": deepcopy(pico),
        "construction_role": "base_support",
        "independence_status": "base",
        "human_review_status": "approved",
    }
    return {
        "schema_version": "1.0",
        "ruleset_id": "epistemic_relation_rules_v1",
        "item_id": "ITEM_REF",
        "family_id": "FAMILY_001",
        "topic_id": "TOPIC_001",
        "comparison_id": "COMPARISON_001",
        "relation_id": "evidence_independent_corroboration_v1",
        "condition_role": "reference",
        "split": "construction",
        "claim": {
            "claim_id": "CLAIM_001",
            "text": "Treatment A reduced events compared with placebo at 12 weeks.",
            "variant_role": "fixed",
            "pico": deepcopy(pico),
        },
        "evidence_catalog": [evidence],
        "ordered_evidence_ids": ["E1"],
        "gold": {
            "per_evidence": [
                {
                    "evidence_id": "E1",
                    "relation_to_claim": "supports",
                    "decisive_quote": "fewer events with treatment A than placebo",
                    "rationale": "The result directly supports the claim.",
                    "human_review_status": "approved",
                }
            ],
            "combined": {
                "acceptable_labels": ["supported"],
                "conflict_expected": False,
                "score_relation_to_reference": "not_scored",
                "expected_used_evidence_ids": ["E1"],
                "rationale": "One direct source supports the claim.",
                "human_review_status": "approved",
            },
        },
        "transformation_log": {
            "changed_variable": "None; reference condition.",
            "held_fixed_checks": ["Claim and evidence are frozen."],
            "reviewer_notes": "Test fixture.",
        },
        "record_status": "approved",
    }


def test_approved_authoring_record_integrity_validation_passes() -> None:
    assert validate_authoring_record(approved_authoring_record()) == []


def test_authoring_record_detects_hash_and_quote_corruption() -> None:
    record = approved_authoring_record()
    record["evidence_catalog"][0]["passage_text"] += " Changed."
    record["gold"]["per_evidence"][0]["decisive_quote"] = "not in the passage"
    errors = validate_authoring_record(record)
    assert any("passage_sha256 does not match" in error for error in errors)
    assert any("decisive_quote is not an exact passage substring" in error for error in errors)


def test_authoring_family_requires_verified_independent_single_addition() -> None:
    reference = approved_authoring_record()
    intervention = deepcopy(reference)
    intervention["item_id"] = "ITEM_INT"
    intervention["condition_role"] = "intervention"
    evidence_2 = deepcopy(reference["evidence_catalog"][0])
    evidence_2.update(
        {
            "evidence_id": "E2",
            "source_group_id": "SOURCE_GROUP_2",
            "passage_text": PASSAGE_2,
            "passage_sha256": hashlib.sha256(PASSAGE_2.encode("utf-8")).hexdigest(),
            "construction_role": "independent_support",
            "independence_status": "verified_independent",
        }
    )
    evidence_2["provenance"] = {
        **evidence_2["provenance"],
        "source_title": "Second example source",
        "source_url": "https://example.org/source-2",
        "pmid": "2",
        "doi": "10.0/example-2",
        "nct_id": "NCT00000002",
    }
    intervention["evidence_catalog"].append(evidence_2)
    intervention["ordered_evidence_ids"].append("E2")
    intervention["gold"]["per_evidence"].append(
        {
            "evidence_id": "E2",
            "relation_to_claim": "supports",
            "decisive_quote": "fewer events with treatment A than placebo",
            "rationale": "The independent source supports the same claim.",
            "human_review_status": "approved",
        }
    )
    intervention["gold"]["combined"].update(
        {
            "score_relation_to_reference": "higher",
            "expected_used_evidence_ids": ["E1", "E2"],
            "rationale": "Two independent sources support the claim.",
        }
    )
    assert validate_authoring_family([reference, intervention]) == []

    intervention["evidence_catalog"][1]["independence_status"] = "unclear"
    errors = validate_authoring_family([reference, intervention])
    assert any("not verified independent" in error for error in errors)


def test_authoring_family_validates_exact_duplicate_without_false_source() -> None:
    reference = approved_authoring_record()
    reference["relation_id"] = "evidence_exact_duplication_v1"
    intervention = deepcopy(reference)
    intervention["item_id"] = "ITEM_DUPLICATE"
    intervention["condition_role"] = "intervention"
    intervention["ordered_evidence_ids"] = ["E1", "E1"]
    intervention["gold"]["combined"]["score_relation_to_reference"] = "equivalent"
    assert validate_authoring_family([reference, intervention]) == []

    false_source = deepcopy(reference["evidence_catalog"][0])
    false_source["evidence_id"] = "E1_COPY"
    intervention["evidence_catalog"].append(false_source)
    intervention["ordered_evidence_ids"] = ["E1", "E1_COPY"]
    intervention["gold"]["per_evidence"].append(
        {
            **intervention["gold"]["per_evidence"][0],
            "evidence_id": "E1_COPY",
        }
    )
    intervention["gold"]["combined"]["expected_used_evidence_ids"] = ["E1", "E1_COPY"]
    errors = validate_authoring_family([reference, intervention])
    assert any("not an exact [E1] to [E1, E1] duplicate" in error for error in errors)
    assert any("creates a false second source" in error for error in errors)


def test_authoring_family_validates_order_reversal_only() -> None:
    reference = approved_authoring_record()
    reference["relation_id"] = "evidence_order_reversal_v1"
    evidence_2 = deepcopy(reference["evidence_catalog"][0])
    evidence_2.update(
        {
            "evidence_id": "E2",
            "source_group_id": "SOURCE_GROUP_2",
            "passage_text": PASSAGE_2,
            "passage_sha256": hashlib.sha256(PASSAGE_2.encode("utf-8")).hexdigest(),
            "construction_role": "independent_support",
            "independence_status": "verified_independent",
        }
    )
    evidence_2["provenance"] = {
        **evidence_2["provenance"],
        "source_title": "Second example source",
        "source_url": "https://example.org/source-2",
        "pmid": "2",
        "doi": "10.0/example-2",
        "nct_id": "NCT00000002",
    }
    reference["evidence_catalog"].append(evidence_2)
    reference["ordered_evidence_ids"] = ["E1", "E2"]
    reference["gold"]["per_evidence"].append(
        {
            "evidence_id": "E2",
            "relation_to_claim": "supports",
            "decisive_quote": "fewer events with treatment A than placebo",
            "rationale": "The independent source supports the same claim.",
            "human_review_status": "approved",
        }
    )
    reference["gold"]["combined"]["expected_used_evidence_ids"] = ["E1", "E2"]

    order_variant = deepcopy(reference)
    order_variant["item_id"] = "ITEM_ORDER_VARIANT"
    order_variant["condition_role"] = "order_variant"
    order_variant["ordered_evidence_ids"] = ["E2", "E1"]
    order_variant["gold"]["combined"]["score_relation_to_reference"] = "equivalent"
    assert validate_authoring_family([reference, order_variant]) == []

    order_variant["ordered_evidence_ids"] = ["E1", "E2"]
    errors = validate_authoring_family([reference, order_variant])
    assert any("not an exact order reversal" in error for error in errors)
