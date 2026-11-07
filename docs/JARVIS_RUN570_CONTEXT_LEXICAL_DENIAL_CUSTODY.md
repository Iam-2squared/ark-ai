# ARK AI — Run570 Context and Local Search Denial Custody

Scope: free-only, isolated/reversible source/test groundwork on Draft PR #8. No live data, real user permission, model inference, physical PC, external account, hardware, billing or protected evaluation was accessed.

## Work packages

1. **Offline lexical index original-denial pinning** — `src/ark/offline_text_index.py` now pins the original result and hit carrier classes and three deny-only properties at import. Each search rejects a counterfeit False-valued authority definition before reading synthetic private fixture text, and rechecks original definitions, source epoch and nested hit carriers after every returned getter callback. This is a no-disclosure lookup only.
2. **Context membership original-denial pinning** — `src/ark/offline_context_membership_guard.py` now pins the four original consent/disclosure/retention/clock-denial descriptors at import and verifies their identities before parsing Context metadata, at every epoch, and after result callbacks. Same-valued but substituted properties are rejected instead of being baselined after potential callbacks.
3. **Detached Context → chunk search join** — `src/ark/offline_context_chunk_review.py` links exact synthetic Context record/scope/expiry/veto metadata with one independently asserted chunk bundle and a bounded no-text lexical search. It requires caller-retained membership and chunk digests, complete expected record ID membership, exact owner/scope/content SHA match, original deny-only authority properties, bounded time claims and result epoch checks. Output contains hashes and positional hit descriptors, never text or permission.

New tests: `tests/test_offline_original_denials_run570.py` (11 parameter-expanded cases), `tests/test_offline_context_chunk_review_run570.py` (23 parameter-expanded cases), **34 authored cases** total, **NOT locally verified PASS counts**. CI must be independently checked at each exact HEAD, including all Ubuntu/Windows Python 3.11–3.13 jobs. The prior Run569 checkpoint HEAD `244af2daf9f21aa968a4f8169f964d8585fd1cc9` has [CI #41563410874](https://github.com/Iam-2squared/ark-ai/actions/runs/41563410874) completed SUCCESS 6/6.

## Authority limits and follow-up

All owner hashes, record IDs, consent/veto continuity digests, clocks, retained hashes and chunk contents are caller-controlled synthetic fixtures. A syntactically correct veto claim is not actual fresh consent or identity; the join never reads a durable store, authenticates a trusted clock, performs a Memory read, discloses text, schedules notifications, dispatches tools or authorizes an external operation. The result must stay review-only until independent source custody, private retention, revocation freshness, trusted-clock audit-before-action and exactly-once authorization are separately proven. Do not use this module as a policy gate.

Frozen V1/V2/Local UI/Launcher evidence, `src/ark/memory/contracts.py`, `src/ark/agency/contracts.py`, and PR #5 `docs/v3/CONTRACT.md` are not changed here. PR #5 and #8 remain Draft/unmerged. No full JARVIS/V3 PASS, paid compute, Candidate training/weights, protected V2 evaluation opening, promotion or main merge.
