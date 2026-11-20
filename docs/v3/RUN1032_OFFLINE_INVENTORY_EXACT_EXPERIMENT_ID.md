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
