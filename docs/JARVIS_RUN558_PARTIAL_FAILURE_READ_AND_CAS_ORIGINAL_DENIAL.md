# Run558 — partial registered READ / failed DAG and manual CAS-denial custody

**Scope:** reversible, local-only JARVIS foundations on Draft PR #8. This note is
technical evidence about source and synthetic fixtures, **not a PASS gate**,
human review, trusted clock, real action, independent custody, or cross-store
atomicity. No V1/V2/Local UI/Launcher frozen contract changed.

## 1. Partial success and FAILED/BLOCKED reconciliation

New \`src/ark/agency/disconnected_partial_registered_failure_join.py\`
offers \`review_partial_registered_failure_archive\`, a read-only, bounded
reconciliation between (a) a create-only detached failure archive bound to
**separately retained** plan SHA, failure-step IDs and file SHA, and (b) an
ordered set of registered READ journal receipts **only for synthetic
SUCCEEDED steps**. Failed or dependency-blocked steps cannot supply successful
READ receipts; they are not assumed to have executed. This review checks the
immutable ToolRegistry/PermissionGate-bound per-step receipts and request-
bound mock result digest, recomputes the domain-separated child fingerprint,
and compares independent passes. It does **not** execute ToolBackend.

Test fixture: \`tests/test_partial_registered_failure_join_run558.py\`.
16 newly authored pytest cases cover 1 success + 1 failed + 1 blocked,
missing/extraneous/misordered evidence, incorrect retained failure/file/plan
pins, changed file bytes, bad clock, journal tamper, wrong synthetic request
binding, original-denial substitution and clean denial-only review.

**Important limits:** detached failure masks are caller assertions rather
than authenticated outcomes. File and journal receipts are read separately,
so a matching aggregate SHA does not establish atomicity or a real history.
Absence of a READ receipt is not proof that no execution occurred. No
automatic retry or replay, actual effect, user consent or live tool call.

## 2. Ambiguous Memory generation-CAS COMMIT

\`src/ark/memory/generation_cas_outcome_review.py\` now retains original
deny-only report property descriptors at import. It rejects substituted
False-returning callbacks **before** opening the read-only SQLite snapshot,
and rechecks originals across callback boundaries. The existing manual-only
outcome categories remain descriptive, never permission to retry.

\`tests/test_memory_cas_outcome_original_denials_run558.py\` adds 7 cases:
five preinstalled false-only getters which must not open SQLite, one
mid-snapshot swap which must be rejected and one clean unchanged report.
Inherited concurrent-writer tests were adjusted to inject a writer at a
separate snapshot callback, retaining drift/tamper detection without
requiring the newly prohibited malicious authority getter to execute.
Other inherited tests now expect an earlier refusal rather than trusting a
replaced denial method.

## Evidence and status

- Invocation work-basis PR #8 HEAD:
  \`ec463b4b1cbbbca0e94de8acda4e5c1e62b71927\`
- First partial join source/test commits: \`1105963b06680f784f42b1bd4b28facbe67a804e\`,
  \`072ca9b78e6ab9a214da3060d1b2e7d092e7280a\`;
  initial CI [41471790714](https://github.com/Iam-2squared/ark-ai/actions/runs/41471790714)
  failed Ruff import order; normal correction
  \`74fe80fe85d8f7bc11e6d1d59eedc96941d29af8\` started
  [41472085618](https://github.com/Iam-2squared/ark-ai/actions/runs/41472085618).
- CAS source \`971e1a3d696486d471735fe7dfd26ca1812259a0\`,
  tests \`b3584935331c6deaadcf4f31068b6e24082af2ce\`.
  Initial source/test CI [41472375091](https://github.com/Iam-2squared/ark-ai/actions/runs/41472375091)
  failed inherited expectations of malicious getter side effects; corrected
  inherited tests through \`9ee40e96cd4e3d7c7cd773f9068418874f56a339\`
  and \`0645c06be34aa69b57c39c261fd8f540daca0bd1\`.
  [41473410548](https://github.com/Iam-2squared/ark-ai/actions/runs/41473410548)
  had one Ubuntu failure (new mid-snapshot test asserted a specific diagnostic
  rather than the actual manual-only wrapped error); corrected expectation at
  \`8d810e016b7c1b3c3f22ad79440235eb35ef7d4e\`.
  Latest exact HEAD full six-job result remains **unverified in this note**;
  consult CI before any GREEN claim.

Neither an unchanged local row nor one matching post-COMMIT update proves
who committed it; never auto-retry an ambiguous write. All sources remain
local synthetic fixtures without training, spending, protected V2 opening,
real ToolBackend effects, promotion or merge.
