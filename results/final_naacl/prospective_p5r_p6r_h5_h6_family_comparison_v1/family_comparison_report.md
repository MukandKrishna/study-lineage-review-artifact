# Prospective Family-Level Comparison

Scope: P5R, P6R, H5, and H6; five repetitions per condition.
Validity is computed against all planned calls. Recognition accuracy is computed only on valid recognition outputs. Verifier labels are counted only for valid outputs; rejected outputs remain in the validity denominator.

## Overall

| Model | Planned | Valid | Invalid | Validity | Invalid output |
|---|---:|---:|---:|---:|---:|
| GPT-5.5 | 220 | 220 | 0 | 100.0% | 0.0% |
| Qwen3-4B | 220 | 210 | 10 | 95.5% | 4.5% |
| Gemma3-4B | 220 | 195 | 25 | 88.6% | 11.4% |

## Files

- `family_summary.csv`: requested family-level metrics.
- `condition_summary.csv`: condition-level audit trail.
- `model_task_summary.csv`: model/task validity totals.
- `comparison_summary.json`: machine-readable totals.

Invalid outputs are not treated as semantic successes or failures. They are reported separately as contract/validity outcomes.
