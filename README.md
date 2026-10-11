# Study-lineage evidence-update evaluation

This repository accompanies the NAACL paper on study-lineage recognition and evidence aggregation in medical language-model verification. The paper is the primary scientific record; this repository provides the files needed to inspect the reported results and rerun the open-weight experiments.

A complete mapping of calls, experiments, models, configurations, outputs, validation checks, and rerun commands is in [REPRODUCTION.md](REPRODUCTION.md).

## What is included

- `paper/`: anonymized LaTeX source, bibliography, ACL style files, and figures.
- `prompts/`: frozen verifier, recognition, grouping, oracle, and robustness prompts.
- `schemas/`: JSON schemas and validation contracts for model inputs and outputs.
- `configs/final/`: configurations corresponding to the paper-facing records.
- `configs/rerun/`: execution-compatible configurations for the supplied runners.
- `data/experiments/epistemic_update_feasibility_v1/private/`: frozen claim and evidence inputs, source-audit records, and run inputs.
- `data/experiments/epistemic_update_feasibility_v1/records/`: rendered prompts, recorded outputs, validation records, and run manifests.
- `results/final_naacl/`: frozen tables, audit summaries, denominator notes, and call-coverage records.
- `src/`: offline validators, prompt-contract utilities, provider adapters, and the shared Transformers GPU runner.
- `tests/`: tests for schemas, prompt contracts, and input/output validation.
- Dependency and environment records: `requirements.txt`, `requirements-gpu.txt`, `requirements-lock.txt`, `pyproject.toml`, and `uv.lock`.

The file-level hashes for experiment records are in `data/experiments/epistemic_update_feasibility_v1/FILE_MANIFEST.csv`. Paper-level call accounting is in `results/final_naacl/call_coverage_manifest.csv`; the frozen denominator note is in `results/final_naacl/paper_scope_and_denominator.md`.

## Scope of the reported experiments

The selected comparison contains 14 clinical families and 550 recorded calls per model. Five models are represented: GPT-5.5, Qwen3-4B, Gemma3-4B, Llama-3.1-8B, and Ministral-3-8B. Repeated calls are stability repetitions of fixed inputs, not additional clinical cases.

The paper keeps the study components separate:

- original suite: 330 calls per model, 1,650 across five models;
- later P5R/P6R/H5/H6 package: 220 calls per model, 1,100 across five models;
- prompt-order robustness audit: 120 calls across GPT-5.5, Qwen3-4B, and Gemma3-4B;
- oracle and cue diagnostics: 195 planned calls across GPT-5.5, Qwen3-4B, and Gemma3-4B;
- exploratory lineage-by-overlap control: 36 calls.

Rejected outputs remain visible in the records and are not treated as scientific successes or failures. The denominator definitions and exclusions are recorded in the result notes rather than inferred from file counts.

## Reproducibility boundary

The open-weight runs can be rerun with the pinned revisions in `configs/transformers_gpu_models.json` and the shared `src/run_transformers_gpu.py` interface. The recorded runs used Kaggle sessions with two Tesla T4 GPUs, each reporting a maximum of 15 GiB of GPU memory; compatible hardware can be used for a rerun. Exact wall-clock and GPU-hour totals were not recorded.

GPT-5.5 calls were run through Codex with medium reasoning effort. Their prompts, inputs, outputs, validation records, and hashes are archived here for audit. An exact GPT-5.5 rerun requires access to Codex; the repository does not claim that the supplied Transformers runner reproduces those calls.

Model weights, provider credentials, temporary archives, historical notebooks, and excluded recovery ledgers are not part of this repository. They are not needed to inspect the reported tables. The repository contains derived research records and source identifiers, not patient-level personal data. Models and clinical source material remain subject to their original access, publication, and reuse terms.

## Offline checks

The following checks do not make model calls:

```text
python src/validate_result_artifacts.py
python src/44_run_epistemic_update_verifier.py --config configs/rerun/epistemic_update_confirmatory_cf_p1_erenumab_initial_gate_neutral_verifier_gpt55_v1.json --validate-only
python src/46_run_epistemic_update_comparative_recognition.py --config configs/rerun/epistemic_update_confirmatory_cf_p1_erenumab_comparative_recognition_gpt55_v1.json --validate-only
python -m pytest tests
```

The first three checks verify paper artifacts, frozen hashes, prompt contracts, and run plans. The tests cover the schemas and prompt/input validation code. Model calls require the relevant provider access and are never started by these checks.

## Repository status

This is an anonymous review copy. It contains no author names, personal repository links, credentials, model weights, or patient-level data. A permanent public repository and citation information can be added after the review period if the paper is accepted.
