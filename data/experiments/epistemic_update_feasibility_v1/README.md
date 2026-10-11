# Frozen experiment package

This directory contains the frozen inputs and recorded outputs for the evidence-update experiments.

- `private/confirmatory/` and `private/run_inputs/` contain the JSON inputs.
- `private/gold_review/` contains the protocol review form.
- `predictions/` and `errors/` contain model outputs and validation errors.
- `records/` contains rendered prompts, run manifests, and archived run records.

Run manifests preserve metadata from the original execution environment. Model weights, provider credentials, and external execution environments are not included.

File names are preserved because the configurations and manifests refer to them.
