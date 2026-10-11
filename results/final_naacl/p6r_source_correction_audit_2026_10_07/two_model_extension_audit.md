# P6R IMpower130 repair: Llama and Ministral extension audit (2026-10-07)

## Scope and provenance

This is a **later targeted extension**, not part of the prospective ten-family suite or the historical 220-call package. Llama-3.1-8B and Ministral-3-8B each ran four repaired P6R items (recognition A/B, recognition B/A, document-level independent update, grouped independent update) five times: **20 calls per model, 40 total**. H6 and same-trial integration were not rerun here. The original repaired scientific input files and prompts were byte-identical to the audited three-model IMpower130 repair; the extension has its own bundle ID and model-specific result ledgers.

The retained audit checks both ZIPs against the frozen parent bundle, extension manifest, exact model ID/revision, all 40 full resume identities, task and adapted-prompt hashes, raw-to-parsed outputs, frozen schemas, token accounting, and the checkpoint-hash manifest recorded in each run. It does not independently inspect Kaggle's model-weight files. Both archives have `status=complete`, 20/20 terminal predictions, zero rejected rows, and zero runtime errors.

| Model | Recognition A/B | Recognition B/A | Independent document | Independent grouped | Strict JSON | Canonical-valid |
|---|---:|---:|---:|---:|---:|---:|
| Llama-3.1-8B | 5/5 correct | **0/5 correct** (answered B; expected A) | 5/5 independent passage used and corroboration flagged | 5/5 independent passage used and corroboration flagged | 15/20 | 20/20 |
| Ministral-3-8B | 5/5 correct | 5/5 correct | 5/5 independent passage used and corroboration flagged | 5/5 independent passage used and corroboration flagged | 0/20 | 20/20 |

All 20 integration responses label the complete claim `supported`, with warrant score 100. The document and grouped responses for both models include the corrected IMpower130 OS-plus-PFS passage (`P6R_E3_IMPOWER130_PRIMARY_OS_PFS`) in `used_evidence_ids` and mark `independent_corroboration`. Ministral's grouped response also marks `duplicate_evidence` in 5/5 runs, consistent with the two initial KEYNOTE-189 snippets sharing a source; it **does not** drop the independent IMpower130 passage. Llama's B/A recognition error remains an error even though its separate integration responses preserve independent support. These are stateless, separate recognition and integration calls; they do not show that a specific recognition response was consumed by an integration call.

Strict versus canonical validity matters: Llama's five grouped outputs and all 20 Ministral outputs have an outer JSON code fence. They fail strict JSON parsing but pass the pre-existing fence-stripping canonical validator. No failed row was silently converted into a success. Within each model/item, the five greedy-decoding repetitions produced one unique raw output; they measure stability, **not five independent clinical cases**.

## Cross-model boundary

The earlier [three-model repair audit](source_correction_condition_summary.csv) found the corrected independent passage used and independent corroboration preserved in document and grouped calls for GPT-5.5, Qwen3-4B, and Gemma3-4B (5/5 in each mode/model). Together with these two later extension runs, this gives five model-specific P6R checks on the repaired scientific content. It is **not** one simultaneous five-model 220-call experiment. Recognition is not uniformly successful: Llama is correct in only one of the two P6R label orders, and Gemma's earlier B/A recognition outputs were rejected.

| Model | Repaired P6R recognition correct / valid (planned) | Independent document pass / valid | Independent grouped pass / valid |
|---|---:|---:|---:|
| GPT-5.5 | 10/10 (10) | 5/5 | 5/5 |
| Qwen3-4B | 10/10 (10) | 5/5 | 5/5 |
| Gemma3-4B | 5/5 (10); B/A rejected | 5/5 | 5/5 |
| Llama-3.1-8B | 5/10 (10) | 5/5 | 5/5 |
| Ministral-3-8B | 10/10 (10) | 5/5 | 5/5 |

These are five model outcomes on **one repaired clinical family**. The three-model rows come from the earlier repair package; only the last two rows are audited in the new extension ZIPs. A `5/5` here is stability across repeats of one execution item, not five source-independent trials.

This extension strengthens the narrower observation that the grouped instruction can **preserve** genuine independent support on repaired P6R input, including for the two additional open-weight models. It does **not** test whether grouping reduces same-trial over-credit for Llama or Ministral, because no same-trial integration condition was run here. It also does not estimate a marginal causal effect of grouping: both document and grouped modes already supported the claim at 5/5 and warrant 100.

## Reproducibility and next use

- Frozen extension bundle ID: `epistemic_update_p6r_impower130_repair_llama_ministral_40_v1`; extension manifest SHA-256: `0b2b25a8c86255032545fbeeb5b2a22c584379facf790030d2fca1010009069b`.
- Shared scientific-input ZIP SHA-256: `614a73ae420110fdcda69759df62181c8ed1c53d014e9838bca829f9173862d3`.
- Llama result archive checksum: `82fa19df824da68f50bc05eed923bcaa5c4dee1885d42885f763a53d03652d30`. The raw archive is not included in the minimum repository.
- Ministral result archive checksum: `975d67650c991f9a184c184834d0dee2dafa99df8d0a3b7057c3650452b3e437`.
- The executed notebooks are archived outside this minimum repository; the audit summaries and checksums above are retained here.
This extension concerns independent-update preservation only. The original family-level same-trial grouping comparison remains reported separately.
