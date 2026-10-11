# P6R/H6 IMpower130 Repair: Three-Model Results

All 180 planned execution identities have completed results and passed exact bundle/model/input-hash/execution/repetition checks before analysis. Any earlier failed attempts are retained in the audit table, not counted as additional independent cases.

P6R is the primary clean provenance control. H6 is reported only as a secondary compositional diagnostic because its initial bundle already contains a genuinely independent trial. Therefore, a global `independent_corroboration` flag in H6 cannot be attributed specifically to the newly added same-trial report and is not scored as same-trial over-crediting.

| Model | Task | Condition | Valid | Recognition correct | P6R independent semantic pass |
|---|---|---|---:|---:|---:|
| GPT-5.5 | document_level | H6_EXACT_REPEAT | 5/5 | 0/5 | 0/5 |
| GPT-5.5 | document_level | H6_INITIAL | 5/5 | 0/5 | 0/5 |
| GPT-5.5 | document_level | H6_QUALIFICATION | 5/5 | 0/5 | 0/5 |
| GPT-5.5 | document_level | H6_SAME_TRIAL_UPDATE | 5/5 | 0/5 | 0/5 |
| GPT-5.5 | document_level | P6R_INDEPENDENT_UPDATE | 5/5 | 0/5 | 5/5 |
| GPT-5.5 | grouped | H6_EXACT_REPEAT | 5/5 | 0/5 | 0/5 |
| GPT-5.5 | grouped | H6_INITIAL | 5/5 | 0/5 | 0/5 |
| GPT-5.5 | grouped | H6_QUALIFICATION | 5/5 | 0/5 | 0/5 |
| GPT-5.5 | grouped | H6_SAME_TRIAL_UPDATE | 5/5 | 0/5 | 0/5 |
| GPT-5.5 | grouped | P6R_INDEPENDENT_UPDATE | 5/5 | 0/5 | 5/5 |
| GPT-5.5 | recognition | P6R_PROVENANCE_AB | 5/5 | 5/5 | 0/5 |
| GPT-5.5 | recognition | P6R_PROVENANCE_BA | 5/5 | 5/5 | 0/5 |
| Gemma3-4B | document_level | H6_EXACT_REPEAT | 5/5 | 0/5 | 0/5 |
| Gemma3-4B | document_level | H6_INITIAL | 5/5 | 0/5 | 0/5 |
| Gemma3-4B | document_level | H6_QUALIFICATION | 5/5 | 0/5 | 0/5 |
| Gemma3-4B | document_level | H6_SAME_TRIAL_UPDATE | 5/5 | 0/5 | 0/5 |
| Gemma3-4B | document_level | P6R_INDEPENDENT_UPDATE | 5/5 | 0/5 | 5/5 |
| Gemma3-4B | grouped | H6_EXACT_REPEAT | 5/5 | 0/5 | 0/5 |
| Gemma3-4B | grouped | H6_INITIAL | 5/5 | 0/5 | 0/5 |
| Gemma3-4B | grouped | H6_QUALIFICATION | 0/5 | 0/5 | 0/5 |
| Gemma3-4B | grouped | H6_SAME_TRIAL_UPDATE | 0/5 | 0/5 | 0/5 |
| Gemma3-4B | grouped | P6R_INDEPENDENT_UPDATE | 5/5 | 0/5 | 5/5 |
| Gemma3-4B | recognition | P6R_PROVENANCE_AB | 5/5 | 5/5 | 0/5 |
| Gemma3-4B | recognition | P6R_PROVENANCE_BA | 0/5 | 0/5 | 0/5 |
| Qwen3-4B | document_level | H6_EXACT_REPEAT | 5/5 | 0/5 | 0/5 |
| Qwen3-4B | document_level | H6_INITIAL | 5/5 | 0/5 | 0/5 |
| Qwen3-4B | document_level | H6_QUALIFICATION | 0/5 | 0/5 | 0/5 |
| Qwen3-4B | document_level | H6_SAME_TRIAL_UPDATE | 5/5 | 0/5 | 0/5 |
| Qwen3-4B | document_level | P6R_INDEPENDENT_UPDATE | 5/5 | 0/5 | 5/5 |
| Qwen3-4B | grouped | H6_EXACT_REPEAT | 5/5 | 0/5 | 0/5 |
| Qwen3-4B | grouped | H6_INITIAL | 5/5 | 0/5 | 0/5 |
| Qwen3-4B | grouped | H6_QUALIFICATION | 5/5 | 0/5 | 0/5 |
| Qwen3-4B | grouped | H6_SAME_TRIAL_UPDATE | 5/5 | 0/5 | 0/5 |
| Qwen3-4B | grouped | P6R_INDEPENDENT_UPDATE | 5/5 | 0/5 | 5/5 |
| Qwen3-4B | recognition | P6R_PROVENANCE_AB | 5/5 | 5/5 | 0/5 |
| Qwen3-4B | recognition | P6R_PROVENANCE_BA | 5/5 | 5/5 | 0/5 |
