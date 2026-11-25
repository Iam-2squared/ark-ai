# Run1032 — exact V3 experiment identity in passive readiness inventory

## Finding

The passive readiness inventory already requires an exact integer schema version, exact dictionaries for the snapshot sections, exact boolean authorization flags, and exact strings for placeholder values. The top-level `experiment_id` comparison did not require an exact built-in string. A hostile `str` subclass can override equality and claim to match the frozen experiment identifier.

## Change

- Snapshot the top-level experiment identifier once.
- Require `type(experiment_id) is str` before comparing it with the frozen experiment ID.
- Add a hostile equality-subclass regression and retain a valid built-in-string control that checks the unchanged passive inventory and false-only authority fields.

## Boundaries

Free-only local validation. No model, tokenizer, converter, quantizer, subprocess, GPU, paid service, external compute, Candidate, protected V2 evaluation, promotion, or V3 Contract 1 change. This remains a passive inventory; it does not authorize preflight or training. PR #5 remains Draft/unmerged, and no UI or main-branch change is included.

**Work basis:** gated Draft PR #5 exact HEAD `15cb19af1ffb044d47e921d81c7495e5d3ce6163`. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no local pytest/Ruff PASS is claimed.


## Run1032 rebase onto the latest gated V3 branch

- Exact work basis: Draft PR #5 branch `research/v3-learning-evaluation`, HEAD `9da32fa5c16813726e29875cd3ccf65ae298188a` (after the exact-head-green preflight text-carrier guard integration).
- Re-applied the same narrow source/test package; V3 Contract 1, authorization fields and training/export behavior remain unchanged.
- Previous child head `5c566a4a0a9dea0b3c08482d7d38b747c59f59da` had CI #44823452871 observed as: success, in_progress, in_progress, success, in_progress, success. That result is not transferred to this rebase.
- Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed.
