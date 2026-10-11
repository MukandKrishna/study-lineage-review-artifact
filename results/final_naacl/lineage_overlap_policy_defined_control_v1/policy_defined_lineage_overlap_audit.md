# GPT policy-defined lineage x overlap run audit - 2026-10-04

## Scope

This exploratory policy-defined control is outside the primary denominator. It uses 20 recorded GPT calls and does not establish unprompted lineage discovery or a causal overlap effect.

## Provenance

- Bundle ID: `epistemic_update_lineage_overlap_policy_defined_28_v1_promise_arise_draft`
- Model: `gpt-5.5`, medium reasoning effort
- Policy: same-trial reports are duplicates; distinct trials may provide independent corroboration.

The policy specifies that a different underlying trial/study is required for
`independent_corroboration`; another report from the same underlying trial is
`duplicate_evidence`. The project-created `source_group_id` was not exposed to
the model.

## Integrity checks

| Check | Result |
|---|---:|
| Planned calls | 20 |
| Saved prediction rows | 20 |
| Error rows | 0 |
| Response status | 20 `ok` |
| Unique five-part resume identities | 20/20 |
| Conditions | 4, with 5 repetitions each |
| Frozen input hashes | Exact match, 20/20 rows |
| Prompt version/hash | Exact match, 20/20 rows |
| Post-run validation with calls disabled | Pass (`MODEL_CALLS=0`) |

| Condition | Input SHA-256 |
|---|---|
| `replacement_same_high` | `ff47f2b81e50f225b846f23707b12239641e16c3671018de2156785ecf452964` |
| `replacement_same_low` | `4a55e1b5d16dc53ef404f57f1a8b05ed79f9da3a4d3da1c0393b2fcf8804de3a` |
| `replacement_independent_high` | `1f2b8d72888e1b782a7cc77a09644592013a107ac075014b29f59e4afb4b092d` |
| `replacement_independent_low` | `a1428a7a5079d60f0ef64b191217966d505bf350fbbf43c22292e9611c4d386f` |

## Descriptive outcome

All 20 outputs labelled the clinical claim `supported`. The predeclared
lineage-policy check is the model's `combination_flags` output:

| Cell | Expected lineage | `duplicate_evidence` | `independent_corroboration` |
|---|---|---:|---:|
| Same trial / high overlap | Same trial | 5/5 | 0/5 |
| Same trial / low overlap | Same trial | 5/5 | 0/5 |
| Independent trial / high overlap | Independent trial | 0/5 | 5/5 |
| Independent trial / low overlap | Independent trial | 0/5 | 5/5 |

Within this one frozen ProMISe/ARISE family, GPT applied the stated same-trial
versus independent-trial policy correctly in both overlap strata. This is a
policy-application result, not proof that the model would discover study
lineage without the policy instruction; it is a one-family policy-application result.
