# GPU rerun

The open-weight runs use `run_transformers_gpu.py`. It reads the same frozen
configuration and input files used by the paper runs.

The recorded runs used Kaggle GPU sessions with two Tesla T4 GPUs, each showing a
maximum of 15 GiB of GPU memory.
A rerun may use other compatible hardware with enough memory.

Validate a plan without making calls:

```text
python src/run_transformers_gpu.py --config configs/rerun/<config>.json --model-key qwen3_4b --output-dir data/local/qwen3_4b --validate-only
```

After checking the model revision and GPU memory, run the plan with:

```text
python src/run_transformers_gpu.py --config configs/rerun/<config>.json --model-key qwen3_4b --output-dir data/local/qwen3_4b --allow-model-calls
```

Use `gemma3_4b`, `llama3_1_8b`, or `ministral3_8b` for the other recorded
checkpoints. Outputs are `predictions.jsonl`, `errors.jsonl`, and
`run_manifest.json`. Existing records are skipped by execution ID and
repetition, so a stopped run can be resumed.

Model weights, credentials, and GPU caches are external to this repository.
