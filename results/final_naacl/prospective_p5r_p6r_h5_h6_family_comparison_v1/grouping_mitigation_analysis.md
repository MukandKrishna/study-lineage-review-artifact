# Prospective Mitigation Analysis

This is a validity-aware paired comparison of document-level and study-grouped verifier outputs.
Same-trial over-crediting is operationalized as an `independent_corroboration` flag on a same-trial update. Independent support is operationalized as a `supported` label plus an `independent_corroboration` flag on an independent-trial update.

## Family-level paired results

| Model | Family | Same-trial paired | Doc over-credit | Grouped over-credit | Reduced | Independent paired | Independent preserved |
|---|---|---:|---:|---:|---:|---:|---:|
| GPT-5.5 | P5R | 5 | 4 | 0 | 4 | 5 | 5 |
| GPT-5.5 | P6R | 5 | 4 | 0 | 4 | 5 | 2 |
| GPT-5.5 | H5 | 5 | 5 | 4 | 1 | 0 | 0 |
| GPT-5.5 | H6 | 5 | 4 | 1 | 3 | 0 | 0 |
| Qwen3-4B | P5R | 5 | 5 | 5 | 0 | 5 | 5 |
| Qwen3-4B | P6R | 5 | 5 | 5 | 0 | 5 | 5 |
| Qwen3-4B | H5 | 5 | 5 | 5 | 0 | 0 | 0 |
| Qwen3-4B | H6 | 5 | 5 | 5 | 0 | 0 | 0 |
| Gemma3-4B | P5R | 5 | 5 | 5 | 0 | 5 | 5 |
| Gemma3-4B | P6R | 5 | 5 | 5 | 0 | 5 | 5 |
| Gemma3-4B | H5 | 0 | 0 | 0 | 0 | 0 | 0 |
| Gemma3-4B | H6 | 5 | 5 | 5 | 0 | 0 | 0 |

Invalid outputs are excluded from paired semantic rates but remain visible in `mitigation_condition_summary.csv`.
This artifact is analysis only; it does not change prompts, inputs, schemas, or model ledgers.
