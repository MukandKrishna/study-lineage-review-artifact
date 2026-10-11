# Paper claim-to-evidence sheet (2026-10-07)

Use the updated [family_level_results.csv](family_level_results.csv) for the 70 model-by-family current-selection rows and [claim_to_evidence.csv](claim_to_evidence.csv) for claim sources and boundaries. P6R remains one of the 14 families: its row selects 30 unchanged and 20 later source-corrected calls per model. The source-corrected P6R details are recorded in `family_level_results.csv`. These are reporting artifacts; raw ledgers and frozen inputs were not changed. The ten-family primary suite and later four-family suite are separate phases. Repetitions show within-input stability; a clinical family is the scientific case.

| Intended paper claim | Family-level evidence | Status and boundary |
|---|---|---|
| Correct lineage recognition can coexist with same-trial over-credit. | GPT-5.5: CF-P1, CF-P2, CF-P3 each have 10/10 correct recognition and 5/5 over-credit in separate aggregation calls. | Main behavioural contrast in 3/3 original provenance families. This is **not** a conditional probability on paired calls or evidence of an internal mechanism. |
| It is not unique to GPT. | Qwen: CF-P1 and CF-P3 each 10/10 recognition and 5/5 over-credit; Ministral: CF-P1 10/10 and 5/5. | Selected family/model conditions only. CF-P2 Qwen aggregation is 0 valid/5 rejected, for example. |
| The later pure-provenance conditions show a similar GPT pattern. | P5R and current-input P6R each have 10/10 correct recognition and 4/5 same-trial over-credit. | P6R recognition uses later source-corrected input; its same-trial integration cells remain from the original combined package. The source versions are explicit in the family CSV. |
| Study-level grouping reduces GPT over-credit in the pure-provenance families. | P5R 4/5→0/5 and P6R 4/5→0/5. GPT's global independent-corroboration flag also falls in H5 (5/5→4/5) and H6 (5/5→1/5). | Only P5R/P6R isolate same-trial over-credit. Both H5 and H6 begin with an independent study, so their global flag cannot attribute credit to the added same-trial report. These are compositional diagnostics, not two more demonstrated mitigations. Grouping is a prompting intervention. |
| Observed independent support is preserved in the source-valid paired runs. | P5R original package: GPT 5/5→5/5. Current-input P6R: GPT, Qwen, Gemma, Llama, and Ministral each 5/5→5/5, document→grouped, for the complete claim. | P6R is one family in the current 70-row table, but its affected calls came from later source-correction runs. Llama's B/A recognition is wrong in 5/5 valid calls; Gemma has five rejected B/A outputs. The old P6R 3/5→3/5 is historical. H5/H6 have no clean independent-update cell in the 220 package. |
| Clean pure-provenance grouping effects are model-dependent. | Comparable P5R/P6R families with lower over-credit: GPT 2/2; Qwen 0/2; Gemma 0/2; Llama 0/1; Ministral 1/1. | H5/H6 global-flag changes are separate compositional diagnostics. Invalid/rejected cells block wider comparisons. See the full per-family validity counts, not pooled repetitions. |
| A lineage × overlap control checks a possible similarity explanation. | ProMISe/ARISE: one family, four cells; GPT produced expected labels in 20/20 policy-instructed calls. Other model details are in the [cross-model table](../final_cross_model_table_2026_10_05/historical_cross_model_summary.md). | **Accepted for exploratory analysis.** This is policy-instructed, not unprompted lineage discovery, and one family cannot establish a causal high-versus-low effect. |

## Reporting boundaries

- Say **“in families where separate recognition calls were correct, separate aggregation calls still over-credited”**. Never imply that a specific recognition response was passed into the aggregation call; the calls were stateless.
- Report model/family numerators, valid denominators, and rejected counts. `0/0` means no valid semantic estimate.
- The results do not establish universal grouping repair, a causal overlap effect, unprompted lineage discovery, or a hidden representation mechanism.
- H5 and H6 global flags cannot isolate marginal same-trial over-credit because both initial states already contain an independent study.
- The P6R current row uses a 30-unchanged/20-source-corrected selection. Historical and selected versions are not pooled, and H6 is compositional rather than pure provenance.

## Source chain

The family sheet is a frozen paper-facing summary of the recorded prediction summaries and audit tables. The per-row `source` column names both P6R source versions where applicable. Overall validity and policy-control summaries are in the [cross-model table](../final_cross_model_table_2026_10_05/historical_cross_model_summary.csv).
