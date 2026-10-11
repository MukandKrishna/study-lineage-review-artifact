# Prompt-Robustness Family-Level Audit

This is a secondary semantic audit. It does not repair, delete, or reclassify raw model records.
Primary validity remains the recorded strict/canonical validity.

## Qwen flag audit

For `same_trial_update`, `independent_corroboration` is a failure. For `independent_update`, the flag is required and the added evidence must be used.
The row-level CSV preserves the exact audit outcome for every repetition.

## Combined family table

See `prompt_family_summary.csv`. It reports GPT-5.5, Qwen3-4B, and Gemma3-4B separately by family, condition, and prompt variant.
It separates strict validity, canonical validity, added-evidence use, flag behaviour, and semantic audit rate.

## Interpretation rule

A model can be JSON-valid while failing the provenance semantic audit. Conversely, a Markdown fence affects strict validity but not necessarily substantive semantic validity after the predeclared canonicalization rule.
