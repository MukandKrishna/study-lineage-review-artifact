# CF-P3 Provenance Policy-Oracle Result

Date: 2026-09-25

The corresponding configuration and prediction records are archived outside this minimum package; this file retains the paper-facing audit summary.

## Run Status

- Planned calls: 15
- Completed calls: 15
- Error rows: 0
## Results

| Condition | Label | Combination flags | Support min/median/max | Warrant min/median/max |
|---|---|---|---:|---:|
| exact repeat control | supported 5/5 | duplicate_evidence 1/5; single_evidence+duplicate_evidence 4/5 | 92/95/95 | 88/90/92 |
| same-trial secondary analysis | supported 5/5 | single_evidence 3/5; single_evidence+duplicate_evidence 2/5 | 94/95/98 | 90/90/95 |
| independent DAPA-CKD trial | supported 5/5 | independent_corroboration 5/5 | 96/96/98 | 93/94/96 |

## Interpretation

The policy-oracle diagnostic passed.

With a general marginal-evidence rule, GPT-5.5 medium did not treat the EMPA-KIDNEY same-trial
secondary analysis as independent corroboration, while it did treat DAPA-CKD as independent
corroboration in all five repetitions.

This strengthens the interpretation that the original neutral CF-P3 failure was a default
update-policy/prompt-policy failure. The model can apply the correct marginal-evidence policy when
the policy is stated explicitly, even without item-specific oracle labels.

## What This Rules Out

- The model is unable to apply same-trial versus independent-trial marginal-evidence logic when the
  rule is explicit.
- Correct behaviour requires item-specific relation labels.

## Scope and limitations

These diagnostics cover one provenance family and one model condition. They show sensitivity to explicit provenance information or a stated marginal-evidence rule; they do not establish a universal repair or an internal mechanism.
