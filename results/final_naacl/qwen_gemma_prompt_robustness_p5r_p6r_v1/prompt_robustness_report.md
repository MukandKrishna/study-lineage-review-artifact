# Qwen and Gemma Prompt-Robustness Check

Date: 2026-10-03

## Run quality

| Model | Planned | Completed | Canonical valid | Strict valid | Invalid/runtime |
|---|---:|---:|---:|---:|---:|
| Qwen3-4B | 40 | 40 | 40 | 40 | 0 |
| Gemma3-4B | 40 | 40 | 40 | 0 | 0 |

Gemma returned one outer Markdown JSON fence on every call. The raw output was
preserved and canonical parsing removed only that one outer fence. Therefore
Gemma is semantically parseable but has a strict format-adherence limitation.

## Main pattern

The two prompt variants produced the same broad pattern in both models:

- Qwen: same-trial conditions carried an `independent_corroboration` flag in
  all 10 calls per family/variant.
- Gemma: same-trial conditions carried an `independent_corroboration` flag in
  all 10 calls per family/variant.
- Independent-trial conditions also retained independent corroboration in both
  models.
- Prompt order did not remove the provenance problem.

## Important model difference

Qwen often ignored the added same-trial report in
`ignored_evidence_ids`, but still emitted `independent_corroboration`. This is
an internally inconsistent output: the model did not use the added report as
evidence, yet its flag suggests independent corroboration. The current schema
validator accepts this because it checks JSON shape, evidence order, quotes,
and basic conflict consistency, but it does not enforce consistency between
`used_evidence_ids`, `ignored_evidence_ids`, and `combination_flags`.

Gemma usually included the same-trial report in `used_evidence_ids` and still
labelled the combination as independent corroboration. That is a clearer
recognition-use failure.

## Scientific interpretation

These runs are useful and meaningful. They show that the broad provenance
failure transfers across Qwen and Gemma and survives a small prompt-order
change. They do not show that the two models fail in exactly the same way:
Gemma over-credits the same-trial report directly, while Qwen combines a
provenance-flag inconsistency with selective evidence omission.

The safe conclusion is:

> Across two prospective provenance families and two equivalent verifier prompt
> orders, Qwen3-4B and Gemma3-4B did not consistently align provenance-aware
> evidence use with their final aggregation outputs. The failure form was
> model-dependent.

This is stronger than a single-model result, but it is not proof for all open
models and not a prompt-invariance theorem. Flag consistency and JSON validity are reported separately; Qwen flags are retained without silent repair or reclassification.
