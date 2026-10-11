# Extended family-level grouping audit (2026-10-05)

Raw ZIPs were read without modification. Rejected rows are retained as explicit counts; semantic rates use canonical-valid rows only.

## New-model family results

| Model | Family | Same-trial document | Same-trial grouped | Independent document support | Independent grouped support | Grouping direction |
|---|---|---:|---:|---:|---:|---|
| Llama-3.1-8B | P5R | 0/5 (rej 0) | 0/5 (rej 0) | 5/5 | 5/5 | no_change |
| Llama-3.1-8B | P6R | 5/5 (rej 0) | 0/0 (rej 5) | 5/5 | 0/0 | not_comparable |
| Llama-3.1-8B | H5 | 5/5 (rej 0) | 0/0 (rej 5) | 0/0 | 0/0 | not_comparable |
| Llama-3.1-8B | H6 | 5/5 (rej 0) | 0/0 (rej 5) | 0/0 | 0/0 | not_comparable |
| Ministral-3-8B | P5R | 0/0 (rej 5) | 0/0 (rej 5) | 5/5 | 0/0 | not_comparable |
| Ministral-3-8B | P6R | 5/5 (rej 0) | 0/5 (rej 0) | 5/5 | 5/5 | lower |
| Ministral-3-8B | H5 | 0/0 (rej 5) | 0/0 (rej 5) | 0/0 | 0/0 | not_comparable |
| Ministral-3-8B | H6 | 5/5 (rej 0) | 5/5 (rej 0) | 0/0 | 0/0 | no_change |

## Interpretation

- A lower same-trial rate means fewer `independent_corroboration` flags under the grouping instruction.
- Independent-support preservation is checked separately as supported + `independent_corroboration`.
- Rejected rows are not treated as successes or failures of the scientific label.
- Repetitions are stability checks, not independent clinical cases; the family is the reporting unit.

## New-model run ledger totals

- Llama-3.1-8B: 220 planned, 180 canonical predictions, 40 rejected, 0 runtime errors.
- Ministral-3-8B: 220 planned, 145 canonical predictions, 75 rejected, 0 runtime errors.
