# Run1096 — Observation-window diagnostic label admission

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`
- Work-basis HEAD: `d7de07d4d5d1239d3748b43d590dd102a2547c1c`
- Child branch: `research/run1096-observation-window-label-admission`
- Source: `src/ark/observation_window_review.py`
- Tests: `tests/test_observation_window_diagnostic_label_admission_run1096.py`

## Change

The optional offline `ObservationWindowReview` now rejects diagnostic labels containing NUL, C0/DEL/C1 controls, bidi/line-separator controls, and default-ignorable formatting scalars. It applies to the privacy-scope header and each envelope's source, adapter and privacy-scope labels before observation identity hashing.

The frozen `ObservationEnvelope` v1 constructor and schema are unchanged. Seven synthetic cases cover ASCII controls, C1, bidi, zero-width formatting and NUL; an ordinary multilingual-label control remains accepted.

## Scope and limits

This is a stricter opt-in metadata review, not media authenticity, camera/microphone capture, consent, retention, trusted time, disclosure or Tool dispatch authority. No raw media is introduced. V1/V2, Memory v1, Local UI/Launcher evidence and V3 frozen contracts are unchanged. UI/frontend development remains paused; no paid/external compute, Candidate generation, protected V2 evaluation, credentials, hardware action or main merge is involved.

## Validation

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS or CI GREEN is claimed.