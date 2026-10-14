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

## Existing artifact attribution and citations

The evaluation uses existing model and software artifacts. The following links identify their
original creators and canonical model or technical documentation; the pinned revisions used for
the reported open-weight runs are recorded in `REPRODUCTION.md` and
`configs/transformers_gpu_models.json`.

- [Qwen3-4B-Instruct-2507](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507), released by the Qwen team; see also the [Qwen3 technical report](https://arxiv.org/abs/2505.09388).
- [Gemma 3 4B instruction-tuned model](https://huggingface.co/google/gemma-3-4b-it), released by Google DeepMind/Gemma Team; see the [Gemma 3 technical report](https://goo.gle/Gemma3Report).
- [Llama 3.1 8B Instruct](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct), released by Meta.
- [Ministral 3 8B Instruct 2512 BF16](https://huggingface.co/mistralai/Ministral-3-8B-Instruct-2512-BF16), released by Mistral AI.
- GPT-5.5 was accessed through Codex from OpenAI; its weights and serving details are not redistributed here.
- The open-weight runner uses [Hugging Face Transformers](https://github.com/huggingface/transformers). The exploratory overlap analysis uses the pinned [all-mpnet-base-v2](https://huggingface.co/sentence-transformers/all-mpnet-base-v2) sentence-transformers checkpoint. Package versions and lock data are recorded in the dependency files listed above.

The clinical publications used as source evidence are cited in the paper bibliography and retained
with source identifiers in the audit records. This attribution section identifies the external
artifacts; it does not by itself grant permission to redistribute model weights or copyrighted
source passages. Those permissions and access terms are handled separately under the
reproducibility boundary below.

## Data provenance, PubMed citation, and reuse boundary

The clinical evidence records are source-linked research records. For each selected publication,
the frozen inputs retain bibliographic metadata such as the title, PMID and DOI where available,
and a passage locator. [PubMed](https://pubmed.ncbi.nlm.nih.gov/) and related NCBI services were
used for bibliographic identification and source linking; PubMed is an index and is not the
copyright holder for the articles indexed there.

Public visibility of a PubMed or publisher page is not treated as permission to redistribute an
article's full text, abstract, figures, or selected passages. Reuse status must be checked for each
article using the article or [PMC copyright and licence guidance](https://pmc.ncbi.nlm.nih.gov/about/copyright/)
and, where necessary, the publisher or copyright holder. The audit schema includes
`license_or_access_note` for recording that decision.
If a reuse licence or permission cannot be established, the safe release form is bibliographic
metadata and a link to the source rather than copied article text. This README records the data
provenance and the unresolved rights boundary; it is not a licence grant or a substitute for the
article-by-article release audit.

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

## Generative-AI assistance disclosure

AI-based assistants were used for coding assistance and initial research including candidate-family screening. The authors independently verified the source records, selections, code, analyses, and final text.
