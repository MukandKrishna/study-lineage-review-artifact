# CF-P3 Provenance Relation-Oracle Result

Date: 2026-09-25

The corresponding configuration and prediction records are archived outside this minimum package; this file retains the paper-facing audit summary.

## Run Status

- Planned calls: 15
- Completed calls: 15
- Error rows: 0
## Results

| Condition | Label | Combination flags | Support min/median/max | Warrant min/median/max |
|---|---|---|---:|---:|
| exact repeat control | supported 5/5 | duplicate_evidence 4/5; single_evidence+duplicate_evidence 1/5 | 93/95/95 | 88/90/95 |
| same-trial secondary analysis | supported 5/5 | none 3/5; duplicate_evidence 2/5 | 95/95/98 | 90/92/92 |
| independent DAPA-CKD trial | supported 5/5 | independent_corroboration 5/5 | 96/96/97 | 94/95/96 |

## Interpretation

The relation-oracle diagnostic passed.

When the prompt explicitly stated the provenance relation, GPT-5.5 medium no longer treated the
EMPA-KIDNEY same-trial secondary analysis as independent corroboration. It still credited DAPA-CKD
as independent corroboration in all five repetitions.

This means the earlier neutral CF-P3 failure should not be framed as "the model cannot use
provenance even when explicitly told." A safer interpretation is:

> The neutral verifier recognized provenance in the separate recognition task but did not make the
> correct marginal-evidence use by default. Explicit relation access was sufficient to repair the
> same-trial over-crediting in CF-P3.

## What This Rules Out

- The CF-P3 neutral failure was only because the model was unable to identify the provenance
  relation.
- The oracle caused blanket suppression of all updates.

## Scope and limitations

These diagnostics cover one provenance family and one model condition. They show sensitivity to explicit provenance information or a stated marginal-evidence rule; they do not establish a universal repair or an internal mechanism.
