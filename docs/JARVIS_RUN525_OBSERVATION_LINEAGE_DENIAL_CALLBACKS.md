# ARK JARVIS — Run525: synthetic observation lineage denial callback custody

## Scope and evidence

- Source: `src/ark/observation_lineage_review.py`, updated on commit `3ef2a90debddbea3abd4a9ce74b27f220908aa31`.
- New tests: `tests/test_observation_lineage_late_denial_run525.py`, saved at commit `0058d4b909f3181a87ea7544f0b5673d16df9c9a`.
- Six newly authored pytest parameterizations/tests (two descriptor targets, one disclosure getter, one original-source mutation, one returned digest mutation, one ordinary successful diagnostic).
- The existing lineage result already checks the original source and receipt after the first set of denial getters. This follow-up also re-reads all three denial properties **after** the first complete check, then verifies the original observations and result after each getter. This prevents a false-valued late getter from silently replacing a prior non-authorizing property with an authorizing descriptor.
- Scope is metadata-only and synthetic; no actual media content, model, microphone, camera, network, user identity, permission, or ToolBackend action is accessed.

## Evidence and limits

The tests explicitly inject reflected class descriptor replacement, an original source change during the second denial check, and a returned lineage digest change. The source will refuse these local callback attacks. Running the tests in GitHub CI is separate evidence; **do not claim PASS until the exact source/test-head CI is GREEN**.

This does **not** authenticate content hashes or camera origin; does not provide consent, scope binding to a real account, disclosure permission, historical writer identity, cross-store atomicity, capture authority, notification authority, replay authority or evidence of any external effect.

The branch remains isolated and Draft. No frozen Contract/V1/V2/Launcher evidence was edited. No new paid compute, credentials, external GPU, or real Candidate work was invoked.
