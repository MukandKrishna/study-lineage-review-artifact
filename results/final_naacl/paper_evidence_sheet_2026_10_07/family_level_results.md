# Family-level results sheet (2026-10-07)

The [CSV](family_level_results.csv) contains all 14 families × five models (70 rows), including controls, validity counts, and exact source paths. P6R is one of the later four families: its current row selects 30 unchanged calls and 20 source-corrected calls per model, with both source versions named. Original ten-family and later four-family phases are separate. Repetitions are stability checks, not independent family cases.

## Source-lineage families and grouping

`R` is correct/valid recognition; `D` and `G` count the independent-corroboration flag in the same-trial-update condition under document-level and grouped prompts. This is attributable over-credit in the pure-provenance families CF-P1--P3 and P5R/P6R, not in compositional H5/H6. `rej` is the rejected same-trial count. A blank cell means no corresponding condition, and `0/0` means no valid semantic estimate.

| Phase | Family | Model | R | D (rej) | G (rej) | Independent support D→G |
|---|---|---|---:|---:|---:|---:|
| original | CF-P1 | GPT-5.5 | 10/10 | 5/5 (0) | — | — |
| original | CF-P2 | GPT-5.5 | 10/10 | 5/5 (0) | — | — |
| original | CF-P3 | GPT-5.5 | 10/10 | 5/5 (0) | — | — |
| original | CF-P1 | Qwen3-4B | 10/10 | 5/5 (0) | — | — |
| original | CF-P2 | Qwen3-4B | 10/10 | 0/0 (5) | — | — |
| original | CF-P3 | Qwen3-4B | 10/10 | 5/5 (0) | — | — |
| original | CF-P1 | Gemma3-4B | 5/10 | 5/5 (0) | — | — |
| original | CF-P2 | Gemma3-4B | 5/10 | 0/0 (5) | — | — |
| original | CF-P3 | Gemma3-4B | 5/10 | 0/0 (5) | — | — |
| original | CF-P1 | Llama-3.1-8B | 5/10 | 0/0 (5) | — | — |
| original | CF-P2 | Llama-3.1-8B | 5/10 | 0/0 (5) | — | — |
| original | CF-P3 | Llama-3.1-8B | 5/10 | 5/5 (0) | — | — |
| original | CF-P1 | Ministral-3-8B | 10/10 | 5/5 (0) | — | — |
| original | CF-P2 | Ministral-3-8B | 5/5 (5 rej) | 0/0 (5) | — | — |
| original | CF-P3 | Ministral-3-8B | 5/5 (5 rej) | 5/5 (0) | — | — |
| later | P5R | GPT-5.5 | 10/10 | 4/5 (0) | 0/5 (0) | 5/5→5/5 |
| later | P6R | GPT-5.5 | 10/10 | 4/5 (0) | 0/5 (0) | 5/5→5/5 |
| later | H5 | GPT-5.5 | 20/20 | 5/5 (0) | 4/5 (0) | — |
| later | H6 | GPT-5.5 | 10/10 | 5/5 (0) | 1/5 (0) | — |
| later | P5R | Qwen3-4B | 10/10 | 5/5 (0) | 5/5 (0) | 5/5→5/5 |
| later | P6R | Qwen3-4B | 10/10 | 5/5 (0) | 5/5 (0) | 5/5→5/5 |
| later | H5 | Qwen3-4B | 15/20 | 5/5 (0) | 5/5 (0) | — |
| later | H6 | Qwen3-4B | 10/10 | 5/5 (0) | 5/5 (0) | — |
| later | P5R | Gemma3-4B | 5/10 | 5/5 (0) | 5/5 (0) | 5/5→5/5 |
| later | P6R | Gemma3-4B | 5/5 (5 rej) | 5/5 (0) | 5/5 (0) | 5/5→5/5 |
| later | H5 | Gemma3-4B | 10/20 | 0/0 (5) | 0/0 (5) | — |
| later | H6 | Gemma3-4B | 5/10 | 5/5 (0) | 5/5 (0) | — |
| later | P5R | Llama-3.1-8B | 5/10 | 0/5 (0) | 0/5 (0) | 5/5→5/5 |
| later | P6R | Llama-3.1-8B | 5/10 | 5/5 (0) | 0/0 (5) | 5/5→5/5 |
| later | H5 | Llama-3.1-8B | 10/20 | 5/5 (0) | 0/0 (5) | 0/0→0/0 |
| later | H6 | Llama-3.1-8B | 5/10 | 5/5 (0) | 0/0 (5) | 0/0→0/0 |
| later | P5R | Ministral-3-8B | 10/10 | 0/0 (5) | 0/0 (5) | 5/5→0/0 |
| later | P6R | Ministral-3-8B | 10/10 | 5/5 (0) | 0/5 (0) | 5/5→5/5 |
| later | H5 | Ministral-3-8B | 20/20 | 0/0 (5) | 0/0 (5) | 0/0→0/0 |
| later | H6 | Ministral-3-8B | 10/10 | 5/5 (0) | 5/5 (0) | 0/0→0/0 |

## Reading rules

- Recognition and aggregation were separate stateless calls. A row shows two family-level outcomes, not a per-call conditional probability.
- H5 recognition contains both provenance and applicability comparisons; H6 is compositional. Their all-axis recognition totals are not pure lineage-recognition counts.
- Both H5 and H6 initial evidence states contain an independent study. Their global independent-corroboration flag cannot isolate credit for the added same-trial report; a lower flag under grouping is not, by itself, demonstrated mitigation.
- The current P6R row uses the OS-plus-PFS IMpower130 passage for the affected recognition and independent-update calls. Independent support is preserved at 5/5 document and 5/5 grouped in all five models; this is one family, not five independent studies. The source versions are recorded in the P6R rows of this file.
- P6R same-trial document/grouped calls are unchanged from the original combined package. The newer P6R recognition/independent calls are later source-correction data, not originally frozen prospective calls. Gemma's corrected B/A recognition has five rejected outputs; Llama's corrected B/A answers are wrong in five valid outputs.
- For GPT-5.5 CF-D3 v2, archived prediction rows carry reversed expected A/B labels. The 10/10 recognition score uses the order-specific targets in the frozen execution config; model outputs and scientific inputs were not changed.
- The CSV also includes CF-A1–A3, CF-D1–D3 and H3, plus every model/family planned, valid and rejected total.
