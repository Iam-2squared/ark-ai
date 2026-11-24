# JARVIS Run1238 — Unicode format-control admission across privacy identities

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `ec91026bae7ae12b7fad924cc2971c5c8c74f351`.
- Reapplies the non-overlapping Personal Context/Observation and proactive-state hardening from Draft PR #417, exact predecessor head `701c7927438c56f1a9e81d36c335e61c15144ac2`.
- Predecessor CI [45292270125](https://github.com/Iam-2squared/ark-ai/actions/runs/45292270125) was GREEN on the older parent; that result does not transfer to this rebase.
- New child branch: `research/run1238-unicode-privacy-identity-rebase`.

## Change

- Personal Context policy revisions pin the import-time `unicodedata` module and exact category classifier, reject every Unicode General Category `Cf` scalar, and recheck classifier identity after scanning.
- The disconnected Observation fixture adapter pins the same classifier in its fixture-budget integrity guard, rejects every `Cf` scalar in source/privacy labels before private fixture hashing, and rechecks the guard after scanning.
- Proactive eligibility identity validation pins the same classifier, rejects every `Cf` scalar in owner, namespace, definition ID and policy revision, and checks the protocol before and after scanning.
- Existing C0/C1, NUL, bidi, separator/default-ignorable, UTF-8 and byte-budget checks remain.
- Observation Envelope v1, Memory v1, proactive SQLite schema/CAS and frozen evaluation contracts are unchanged.

## Regression coverage

Synthetic tests cover U+0600, U+FFF9 and U+E0001 in Personal Context policy revisions, both Observation metadata fields, and all four proactive identity fields. They also verify classifier/module substitution is rejected before replacement callbacks receive caller text or private fixture bytes. Positive Japanese metadata and identity text remain accepted.

## Evidence boundary

This is local in-process input-integrity hardening only. It is not a Python sandbox, authenticated observation provenance, consent, disclosure, notification, Tool authorization, dispatch or trusted-clock authority. No live personal data is used.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, UI/frontend work, destructive action, frozen-contract change or main merge. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
