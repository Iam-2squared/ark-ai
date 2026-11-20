# ARK AI Run1017 — startup lease full-review control ordering

**Work basis:** PR #61 exact head `4cce61ec799d5cae8a99c955025d5d73f7fb4751`, branch `research/startup-lease-identifier-controls-run1016`. Parent exact-head CI run [#44698322968](https://github.com/Iam-2squared/ark-ai/actions/runs/44698322968) completed GREEN 6/6. This is an isolated test-only child of PR #61.

## Coverage added

The existing Run1016 tests exercise `SyntheticReadinessRequirement.assert_shape()` directly. This child additionally exercises the full `review_synthetic_startup_lease()` path:

- Both `component_id` and `schema_revision` reject C0/DEL, C1, bidi, zero-width, line/paragraph separators, soft hyphen and BOM/format controls.
- A deliberately corrupted later snapshot digest makes the test sensitive to ordering: the requirement-control denial must occur before snapshot-integrity review.
- An ordinary Japanese identifier remains accepted, while all lease authority flags remain false.

The package changes no production source or startup behavior.

## Evidence and limits

The parameterized test is authored, not a local pytest PASS. Exact-head Windows/Linux × Python 3.11–3.13 CI is required. Synthetic in-memory readiness fixtures only.

A readiness lease remains diagnostic. It is not machine health, trusted time, startup permission, dispatch authority, notification permission, hardware authorization, or an external-effect proof. No live sensors, real backend, paid service, external compute, credentials, Candidate, protected V2 evaluation, frozen-contract change, UI, PR #5, PR #9, or main merge is included. PR #8 remains Draft/unmerged; ARK/JARVIS remains NOT_PASSED.
