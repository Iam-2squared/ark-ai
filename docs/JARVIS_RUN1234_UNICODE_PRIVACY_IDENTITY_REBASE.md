# JARVIS Run1234 — Unicode format-control admission across privacy identities

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `e3ab3b4a33ff2414bc978158898a2eed71ef79f5`.
- Combines the non-overlapping Personal Context/Observation changes from Draft PR #376 and proactive-state changes from Draft PR #377.
- PR #377 predecessor exact-head CI [45198187575] was GREEN on an older base. PR #376 predecessor exact-head CI [45198050561] failed Ruff F401 for an unused `SimpleNamespace` import; that unused import is deliberately omitted here. Fresh exact-head CI is required.
- New child branch: `research/run1234-unicode-privacy-identity-rebase`.

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
