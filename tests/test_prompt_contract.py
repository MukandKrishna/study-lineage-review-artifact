from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from update_prompt_contract import (
    COMPARATIVE_INPUT_FIELD_ORDER,
    COMPARATIVE_RECOGNITION_FIELD_ORDER,
    COMPARATIVE_RECOGNITION_INPUT_SCHEMA_PATH,
    COMPARATIVE_RECOGNITION_OUTPUT_SCHEMA_PATH,
    COMPARATIVE_RECOGNITION_PROMPT_PATH,
    EVIDENCE_FIELD_ORDER,
    INPUT_FIELD_ORDER,
    NEUTRAL_VERIFIER_PROMPT_PATH,
    RECOGNITION_FIELD_ORDER,
    RECOGNITION_OUTPUT_SCHEMA_PATH,
    RELATION_RECOGNITION_PROMPT_PATH,
    UPDATE_INPUT_SCHEMA_PATH,
    VERIFIER_OUTPUT_SCHEMA_PATH,
    comparative_model_input_json,
    load_json,
    load_prompt,
    model_input_json,
    render_prompt,
    validate_comparative_recognition_input,
    validate_update_input,
)


def evidence(bundle_position: int, evidence_id: str, trial_id: str) -> dict:
    return {
        "bundle_position": bundle_position,
        "evidence_id": evidence_id,
        "source_group_id": f"SOURCE_{evidence_id}",
        "source_title": f"Source {evidence_id}",
        "pmid": evidence_id.removeprefix("E"),
        "doi": f"10.0/{evidence_id.lower()}",
        "trial_id": trial_id,
        "source_locator": "Results paragraph",
        "passage_text": f"Preserved result passage for {evidence_id}.",
    }


def update_input() -> dict:
    return {
        "schema_version": "1.0",
        "item_id": "UPDATE_001",
        "claim_id": "CLAIM_001",
        "claim_text": "Treatment A reduced outcome B in population C.",
        "initial_evidence": [
            evidence(1, "E1", "TRIAL_1"),
            evidence(2, "E2", "TRIAL_2"),
        ],
        "added_evidence": evidence(3, "E3", "TRIAL_3"),
    }


def comparative_input() -> dict:
    return {
        "schema_version": "1.0",
        "item_id": "COMPARATIVE_001",
        "claim_id": "CLAIM_001",
        "claim_text": "Treatment A reduced outcome B in population C.",
        "target_relation": "provenance",
        "initial_evidence": [
            evidence(1, "E1", "TRIAL_1"),
            evidence(2, "E2", "TRIAL_2"),
        ],
        "update_a": evidence(3, "E3", "TRIAL_3"),
        "update_b": evidence(4, "E4", "TRIAL_1"),
    }


def test_schema_property_and_required_orders_are_frozen() -> None:
    input_schema = load_json(UPDATE_INPUT_SCHEMA_PATH)
    comparative_input_schema = load_json(COMPARATIVE_RECOGNITION_INPUT_SCHEMA_PATH)
    recognition_schema = load_json(RECOGNITION_OUTPUT_SCHEMA_PATH)
    comparative_schema = load_json(COMPARATIVE_RECOGNITION_OUTPUT_SCHEMA_PATH)
    verifier_schema = load_json(VERIFIER_OUTPUT_SCHEMA_PATH)

    assert tuple(input_schema["required"]) == INPUT_FIELD_ORDER
    assert tuple(input_schema["properties"]) == INPUT_FIELD_ORDER
    evidence_schema = input_schema["$defs"]["evidence_item"]
    assert tuple(evidence_schema["required"]) == EVIDENCE_FIELD_ORDER
    assert tuple(evidence_schema["properties"]) == EVIDENCE_FIELD_ORDER
    assert tuple(recognition_schema["required"]) == RECOGNITION_FIELD_ORDER
    assert tuple(recognition_schema["properties"]) == RECOGNITION_FIELD_ORDER
    assert tuple(comparative_input_schema["required"]) == COMPARATIVE_INPUT_FIELD_ORDER
    assert tuple(comparative_input_schema["properties"]) == COMPARATIVE_INPUT_FIELD_ORDER
    assert tuple(comparative_schema["required"]) == COMPARATIVE_RECOGNITION_FIELD_ORDER
    assert tuple(comparative_schema["properties"]) == COMPARATIVE_RECOGNITION_FIELD_ORDER
    assert tuple(verifier_schema["required"]) == (
        "item_id",
        "per_evidence_assessments",
        "combined_assessment",
    )


def test_update_input_requires_two_initial_items_and_frozen_order() -> None:
    payload = update_input()
    assert validate_update_input(payload) == []

    too_small = deepcopy(payload)
    too_small["initial_evidence"] = too_small["initial_evidence"][:1]
    assert "initial_evidence must contain at least two items" in validate_update_input(too_small)

    reordered = {key: payload[key] for key in reversed(payload)}
    assert any("frozen order" in error for error in validate_update_input(reordered))

    initial_only = deepcopy(payload)
    initial_only["added_evidence"] = None
    assert validate_update_input(initial_only) == []


def test_update_input_supports_declared_metadata_ablation_only() -> None:
    payload = update_input()
    for item in [*payload["initial_evidence"], payload["added_evidence"]]:
        del item["source_group_id"]
        del item["trial_id"]

    assert validate_update_input(
        payload,
        omitted_evidence_fields=frozenset({"source_group_id", "trial_id"}),
    ) == []
    assert any("frozen order" in error for error in validate_update_input(payload))
    assert any(
        "unsupported omitted evidence fields" in error
        for error in validate_update_input(
            payload,
            omitted_evidence_fields=frozenset({"passage_text"}),
        )
    )


def test_comparative_input_requires_two_updates_and_frozen_order() -> None:
    payload = comparative_input()
    assert validate_comparative_recognition_input(payload) == []

    bad_relation = deepcopy(payload)
    bad_relation["target_relation"] = "gold_relation"
    assert any("target_relation" in error for error in validate_comparative_recognition_input(bad_relation))

    missing_update = deepcopy(payload)
    missing_update["update_b"] = None
    assert "update_b must be an evidence object" in validate_comparative_recognition_input(missing_update)

    reordered = {key: payload[key] for key in reversed(payload)}
    assert any("frozen order" in error for error in validate_comparative_recognition_input(reordered))


def test_comparative_input_supports_declared_metadata_ablation_only() -> None:
    payload = comparative_input()
    for item in [*payload["initial_evidence"], payload["update_a"], payload["update_b"]]:
        del item["source_group_id"]

    assert validate_comparative_recognition_input(
        payload,
        omitted_evidence_fields=frozenset({"source_group_id"}),
    ) == []
    assert any(
        "frozen order" in error
        for error in validate_comparative_recognition_input(payload)
    )
    assert any(
        "unsupported omitted evidence fields" in error
        for error in validate_comparative_recognition_input(
            payload,
            omitted_evidence_fields=frozenset({"passage_text"}),
        )
    )


def test_both_prompts_receive_byte_identical_model_input_json() -> None:
    payload = update_input()
    serialized = model_input_json(payload)
    neutral = render_prompt(load_prompt(NEUTRAL_VERIFIER_PROMPT_PATH), payload)
    recognition = render_prompt(load_prompt(RELATION_RECOGNITION_PROMPT_PATH), payload)

    assert neutral.count(serialized) == 1
    assert recognition.count(serialized) == 1
    assert "{model_input_json}" not in neutral
    assert "{model_input_json}" not in recognition


def test_comparative_prompt_receives_two_update_arms() -> None:
    payload = comparative_input()
    serialized = comparative_model_input_json(payload)
    prompt = render_prompt(load_prompt(COMPARATIVE_RECOGNITION_PROMPT_PATH), payload)

    assert prompt.count(serialized) == 1
    assert '"update_a"' in prompt
    assert '"update_b"' in prompt
    assert '"target_relation": "provenance"' in prompt
    assert "which update adds genuinely independent evidence" in prompt.lower()
    assert "{model_input_json}" not in prompt


def test_model_input_has_no_gold_or_construction_leakage() -> None:
    serialized = json.dumps(update_input()).lower()
    forbidden_keys = (
        "gold",
        "expected_label",
        "expected_update",
        "condition_role",
        "relation_id",
        "judgement_call",
        "construction_role",
    )
    for key in forbidden_keys:
        assert f'"{key}"' not in serialized


def test_neutral_verifier_contains_no_explicit_aggregation_rule() -> None:
    prompt = load_prompt(NEUTRAL_VERIFIER_PROMPT_PATH).lower()
    forbidden_instructions = (
        "apply this mapping",
        "if at least one used occurrence",
        "exact duplicate must not",
        "duplicates should not",
        "out-of-scope evidence must be ignored",
        "conflict should produce",
        "not counted as independent corroboration",
    )
    for instruction in forbidden_instructions:
        assert instruction not in prompt
    assert "use these combined labels" in prompt
    assert "warrant_strength_score" in prompt
    assert "do not weaken, strengthen, or reinterpret the claim" in prompt


def test_neutral_verifier_out_of_scope_does_not_route_direction_away_from_conflict() -> None:
    prompt = load_prompt(NEUTRAL_VERIFIER_PROMPT_PATH).lower()
    normalized = " ".join(prompt.split())
    out_of_scope_definition = normalized.split("- out_of_scope:", 1)[1].split(
        "use these combined labels:", 1
    )
    assert "direction" not in out_of_scope_definition[0]
    assert "population" not in out_of_scope_definition[0]
    assert "intervention" not in out_of_scope_definition[0]
    assert "comparator" not in out_of_scope_definition[0]
    assert "outcome" not in out_of_scope_definition[0]
    assert "time frame" not in out_of_scope_definition[0]
    assert "setting" not in out_of_scope_definition[0]
    assert "supports or conflicts" in out_of_scope_definition[0]


def test_recognition_prompt_does_not_prescribe_final_verdict() -> None:
    prompt = load_prompt(RELATION_RECOGNITION_PROMPT_PATH).lower()
    normalized = " ".join(prompt.split())
    assert "without deciding how the final claim verdict should change" in normalized
    assert "do not recommend or reveal a final verifier label or score" in normalized
    assert "provenance_relation" in prompt
    assert "applicability_relation" in prompt
    assert "direction_relation" in prompt
    assert "requires a non-null added_evidence item" in normalized


def test_comparative_recognition_prompt_does_not_prescribe_final_verdict() -> None:
    prompt = load_prompt(COMPARATIVE_RECOGNITION_PROMPT_PATH).lower()
    normalized = " ".join(prompt.split())
    assert "matched comparison is between update a and update b" in normalized
    assert "do not decide how the final claim verdict should change" in normalized
    assert "do not recommend or reveal a final verifier label or score" in normalized
    assert "more genuinely independent" not in normalized
    assert "more applicable" not in normalized
    assert "more opposing" not in normalized
    assert "comparative_answer" in prompt
    assert "no_meaningful_difference" in prompt
