# Cross-Model Family-Level Synthesis

This synthesis joins three already completed analyses: prospective recognition, document-level versus provenance-aware grouping-instruction outputs, and the two-prompt robustness audit.
No raw model records were modified and no new model calls were made.

## Interpretation

- Recognition accuracy measures whether the model identifies the relation in the A/B comparison.
- Document/group-instruction labels measure final evidence integration under a neutral prompt versus a prompt that explicitly instructs study-level provenance grouping.
- The grouped condition is a prompting intervention; evidence was not externally pre-aggregated before inference.
- Same-trial over-crediting is the independent-corroboration flag on a same-trial update.
- Prompt semantic pass requires no forbidden same-trial independent flag, or requires independent flag plus use of the added independent evidence.
- Strict and canonical validity are reported separately from semantic outcomes.
- Unavailable means no row exists for the current frozen input hash; it is not a model error and is not replaced with a stale-input row.

## Files

- `family_level_master_summary.csv`: one row per model and prospective family.
- `model_level_master_summary.csv`: compact model-level synthesis.
- `source_tables.json`: source paths and aggregation definitions.

## Important caution

The table supports a condition-specific behavioural claim. It does not establish a universal claim about all language models or an internal mechanism. Repetition numbers across the two stateless modes are not statistical pairs; the family is the scientific unit. Open-model validity and semantic failures remain separate outcomes.
GPT document provenance is complete: all 85/85 document-level rows match the current frozen input hashes.
