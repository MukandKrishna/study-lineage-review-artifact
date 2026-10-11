# Final cross-model experiment table — 2026-10-05

This is the **2026-10-05 historical snapshot** combining the 330-call primary suite, the original 220-call combined suite, family-level grouping results, and the four-cell policy-defined lineage control. Rejected rows are explicit and remain in denominators. The current P6R source-selected family row is in the [70-row family CSV](../paper_evidence_sheet_2026_10_07/family_level_results.csv); the historical values below are retained for comparison only.

| Model | Primary valid/rejected | Recognition valid/rejected | Document valid/rejected | Grouped valid/rejected | Comparable grouping families | Families improved | Lineage-control status |
|---|---:|---:|---:|---:|---:|---:|---|
| GPT-5.5 | 330/0 | 50/0 | 85/0 | 85/0 | 4/4 | 4 | 20/20 valid; policy labels correct in all four cells (same=duplicate, independent=corroboration) |
| Qwen3-4B | 270/60 | 50/0 | 85/0 | 75/10 | 4/4 | 0 | 4/4 valid; same-high duplicate, same-low mislabelled independent, independent cells correct |
| Gemma3-4B | 210/120 | 50/0 | 70/15 | 75/10 | 3/4 | 0 | 4/4 valid; both same-trial cells mislabelled independent, independent cells correct |
| Llama-3.1-8B | 210/120 | 50/0 | 85/0 | 45/40 | 1/4 | 0 | 4/4 valid; same cells mislabelled independent; independent-high under-credited; independent-low mixed |
| Ministral-3-8B | 265/65 | 50/0 | 45/40 | 50/35 | 2/4 | 1 | 2/4 valid; both same-trial cells rejected; accepted independent cells mixed |

## Family-level grouping detail

| Model | Same-trial document over-credit | Same-trial grouped over-credit | Independent support, document | Independent support, grouped |
|---|---|---|---|---|
| GPT-5.5 | P5R=4/5; P6R=4/5; H5=5/5; H6=5/5 | P5R=0/5; P6R=0/5; H5=4/5; H6=1/5 | P5R=5/5; P6R=3/5 | P5R=5/5; P6R=3/5 |
| Qwen3-4B | P5R=5/5; P6R=5/5; H5=5/5; H6=5/5 | P5R=5/5; P6R=5/5; H5=5/5; H6=5/5 | P5R=5/5; P6R=5/5 | P5R=5/5; P6R=5/5 |
| Gemma3-4B | P5R=5/5; P6R=5/5; H5=0/0; H6=5/5 | P5R=5/5; P6R=5/5; H5=0/0; H6=5/5 | P5R=5/5; P6R=5/5 | P5R=5/5; P6R=5/5 |
| Llama-3.1-8B | P5R=0/5; P6R=5/5; H5=5/5; H6=5/5 | P5R=0/5; P6R=0/0; H5=0/0; H6=0/0 | P5R=5/5; P6R=5/5 | P5R=5/5 |
| Ministral-3-8B | P5R=0/0; P6R=5/5; H5=0/0; H6=5/5 | P5R=0/0; P6R=0/5; H5=0/0; H6=5/5 | P5R=5/5; P6R=5/5 | P6R=5/5 |

## Interpretation

- Valid means canonical-valid output; rejected means a completed call whose output failed the scientific contract.
- Grouping rates use valid rows only, while rejected counts remain visible. A family is marked non-comparable when one mode has no valid rows.
- Independent-support columns apply only to P5R/P6R, where an independent update exists. H5/H6 do not have a clean independent-update cell in the 220 package.
- The grouping intervention is model-condition dependent: GPT shows the clearest reduction; Qwen/Gemma do not; Llama/Ministral have insufficient comparable cells for a broad claim.
- Lineage × overlap is one-family exploratory evidence, not a causal estimate.

## 2026-10-07 P6R repaired-input addendum (separate package)

The table above is the historical primary/combined comparison and is unchanged.
The source-corrected P6R rows are recorded in the [current family-level result sheet](../paper_evidence_sheet_2026_10_07/family_level_results.csv).
added 20/20 canonically valid targeted calls per model on the corrected
IMpower130 OS-plus-PFS passage. Both preserved the independent passage and
`independent_corroboration` in 5/5 document and 5/5 grouped calls. Llama got
only one of two recognition label orders correct; Ministral got both, but all
its outputs needed outer-JSON-fence canonicalization. This addendum does not
replace the original P6R row or estimate same-trial grouping improvement.
