# Reproduction guide

This document describes how the repository maps to the experiments reported in the paper. It is a record of the artifact layout and call accounting.

## 1. Experimental unit

One call is one model invocation on one frozen task input. The task input contains a fixed medical claim, an initial evidence set, and, where applicable, one added evidence item or two matched update arms. Each exact input was invoked five times. Those repetitions measure within-input response stability. They are not five independent clinical cases.

The paper keeps these tasks separate:

- **Neutral integration:** assess the complete evidence set and return per-evidence and combined judgements.
- **Comparative recognition:** compare Update A and Update B for one target relation: provenance, applicability, or direction.
- **Study-grouped integration:** repeat neutral integration with an explicit study-grouping instruction.
- **Oracle diagnostics:** provide an item-specific relation or a general marginal-evidence policy in a separate verifier prompt.
- **Cue ablation:** remove `source_group_id` while retaining the other displayed source metadata.
- **Prompt robustness:** repeat selected P5R/P6R document-level and independent-update conditions with a reordered verifier prompt.
- **Lineage-by-overlap control:** a one-family, policy-instructed exploratory control with four overlap/lineage cells.

Recognition and integration are separate stateless calls. A recognition answer is never passed to a later integration call.

## 2. Paper denominators

The selected paper comparison contains 14 clinical families and 110 exact inputs. Five repetitions give 550 calls per model and 2,750 calls across five model conditions.

| Package                                                |     Calls per model | Across five models | Role            |
| ------------------------------------------------------ | ------------------: | -----------------: | --------------- |
| Original CF-P1--P3, CF-A1--A3, CF-D1--D3, and H3 suite |                 330 |              1,650 | primary         |
| Later P5R, P6R, H5, and H6 package                     |                 220 |              1,100 | later follow-up |
| Prompt-order robustness audit                          | 40 per tested model |          120 total | secondary       |
| CF-P3 oracle and H3-M1 cue diagnostics                 | 65 per tested model |        195 planned | diagnostic      |
| Lineage-by-overlap control                             |     model-dependent |           36 total | exploratory     |

The 2,750-call denominator excludes the robustness, oracle, cue-ablation, and overlap packages. The exact definitions are frozen in `results/final_naacl/paper_scope_and_denominator.md`.

The repository coverage CSV also lists auxiliary P6R repair records for Qwen3-4B, Gemma3-4B, Llama-3.1-8B, and Ministral-3-8B. These records are retained for audit and are not silently added to the paper's primary denominator.

## 3. Models and recorded conditions

| Model key         | Model                                       | Pinned revision                              | Recorded setting               |
| ----------------- | ------------------------------------------- | -------------------------------------------- | ------------------------------ |
| `qwen3_4b`      | Qwen/Qwen3-4B-Instruct-2507                 | `cdbee75f17c01a7cc42f958dc650907174af0554` | open-weight Transformers       |
| `gemma3_4b`     | google/gemma-3-4b-it                        | `093f9f388b31de276ce2de164bdc2081324b9767` | open-weight Transformers       |
| `llama3_1_8b`   | meta-llama/Llama-3.1-8B-Instruct            | `0e9e39f249a16976918f6564b8830bc894c89659` | open-weight Transformers       |
| `ministral3_8b` | mistralai/Ministral-3-8B-Instruct-2512-BF16 | `f6fae9795746f63c9be8344932f01275f3c63734` | open-weight Transformers       |
| `gpt_5_5`       | GPT-5.5                                     | not applicable                               | Codex, medium reasoning effort |

The open-weight manifest is `configs/transformers_gpu_models.json`. Its recorded decoding settings are greedy decoding (`do_sample=false`) with `max_new_tokens=2048`. The recorded Kaggle sessions used two Tesla T4 GPUs, each reporting a maximum of 15 GiB of GPU memory. Exact wall-clock and GPU-hour totals were not recorded.

GPT-5.5 prompts, inputs, outputs, validation records, and hashes are archived. Exact GPT-5.5 reruns require Codex access; the Transformers runner is not a GPT runner.

## 4. Repository layout

`paper/` contains `main.tex`, the bibliography, ACL style files, and the paper figures.
`prompts/` contains the frozen prompt templates, including neutral, comparative-recognition, grouped, oracle, and robustness variants.
`schemas/` contains the input and output JSON schemas.
`configs/final/` records the paper-facing configurations.
`configs/rerun/` contains execution-compatible plans.
`data/experiments/epistemic_update_feasibility_v1/private/` contains frozen claims, evidence, and source-audit inputs.
`data/experiments/epistemic_update_feasibility_v1/records/` contains rendered prompts, outputs, validation records, and manifests.
`results/final_naacl/` contains the frozen paper tables, denominator note, audit summaries, and call-coverage CSV.
`src/` contains the two guarded Codex runners, the shared Transformers runner, prompt/schema utilities, and offline validators.
`tests/` contains schema and prompt-contract tests.

`data/experiments/epistemic_update_feasibility_v1/FILE_MANIFEST.csv` records the byte size and SHA-256 hash of the archived experiment records.

## 5. Traceability map

| Need                                   | Repository location                                                                                           | What it contains                                                                           |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Paper claims, tables, and appendix     | `paper/main.tex`                                                                                            | The anonymized paper and its cross-references to the reported tables                       |
| Frozen denominator and call accounting | `results/final_naacl/paper_scope_and_denominator.md` and `results/final_naacl/call_coverage_manifest.csv` | The paper scope, package boundaries, planned calls, recorded outputs, and rejection counts |
| Claim and evidence inputs              | `data/experiments/epistemic_update_feasibility_v1/private/run_inputs/`                                      | The exact JSON inputs used by the recorded conditions                                      |
| Rendered prompts and run records       | `data/experiments/epistemic_update_feasibility_v1/records/`                                                 | Prompt text, run manifests, validation records, and archived call outputs                  |
| Cross-model output bundles             | `data/experiments/epistemic_update_feasibility_v1/records/model_outputs/`                                   | Per-model predictions, errors, manifests, and model-file hashes where available            |
| Paper-facing audit tables              | `results/final_naacl/`                                                                                      | Family summaries, source manifests, audit reports, and evidence sheets                     |
| Prompt and response contracts          | `prompts/` and `schemas/`                                                                                 | Frozen prompt templates and JSON schemas used for validation                               |
| Rerun plans                            | `configs/rerun/` and `configs/transformers_gpu_models.json`                                               | Input paths, repetition counts, model revisions, decoding settings, and output plans       |
| Reusable code and checks               | `src/` and `tests/`                                                                                       | Model runners, validators, prompt utilities, and offline tests                             |

A configuration's input paths must resolve inside this checkout. Its prediction and error paths are output locations for a rerun or references to recorded archives; they are not additional input requirements.

## 6. Offline validation

These commands read local files only and make no model calls:

```text
python src/validate_result_artifacts.py
python src/44_run_epistemic_update_verifier.py --config configs/rerun/epistemic_update_confirmatory_cf_p1_erenumab_initial_gate_neutral_verifier_gpt55_v1.json --validate-only
python src/46_run_epistemic_update_comparative_recognition.py --config configs/rerun/epistemic_update_confirmatory_cf_p1_erenumab_comparative_recognition_gpt55_v1.json --validate-only
python -m pytest tests
```

The first command checks the paper artifacts, figures, denominator note, and coverage manifest. The guarded verifier and recognition commands check prompt, schema, input, and hash consistency. The test suite checks the schema and prompt contracts.

## 7. Open-weight reruns

The shared runner is `src/run_transformers_gpu.py`. It accepts a frozen configuration, a model key from `configs/transformers_gpu_models.json`, and a separate output directory.

Plan validation:

```text
python src/run_transformers_gpu.py --config configs/rerun/<config>.json --model-key qwen3_4b --output-dir data/local/qwen3_4b --validate-only
```

The same interface applies to `gemma3_4b`, `llama3_1_8b`, and `ministral3_8b`. A real run requires the model weights, a compatible CUDA/PyTorch environment, and the model's access terms:

```text
python src/run_transformers_gpu.py --config configs/rerun/<config>.json --model-key qwen3_4b --output-dir data/local/qwen3_4b --allow-model-calls
```

The runner writes `predictions.jsonl`, `errors.jsonl`, and `run_manifest.json`. Existing execution IDs and repetitions are skipped, so an interrupted run can be resumed in the same output directory. `--limit` can be used for a small smoke run before a full plan.

The exact model-specific configuration names are listed in `configs/rerun/`. The configuration records the input path, prompt version, schema, revision, repetitions, and output locations. The runner does not create clinical inputs or infer gold labels.

## 8. Recorded outputs and paper tables

Raw recorded responses are stored as JSONL records under `data/experiments/epistemic_update_feasibility_v1/records/`. Rendered prompts and run manifests sit beside the corresponding records. The compact tables used by the paper are under `results/final_naacl/`.

The coverage CSV reports, for each model package, planned calls, recorded predictions, recorded errors, model revision, and reporting scope. A missing or rejected output is not counted as a correct scientific judgement. The paper tables apply their stated valid-output rules separately.

## 9. What is not reproduced by this checkout

Model weights, provider credentials, temporary archives, historical notebooks, and excluded recovery ledgers are external to the repository. The repository contains derived research records and source identifiers, not patient-level personal data. Models and clinical source material remain subject to their original access, publication, and reuse terms.

This is an anonymous review copy. It does not contain author identity, a personal repository link, or a claim that every recorded GPT call can be rerun locally.
