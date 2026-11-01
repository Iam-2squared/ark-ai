# Run527 — Disconnected registered READ, Context, and Memory witness custody

**Free-only, disconnected, reversible safety hardening.** No actual ToolBackend, personal Context export, write replay, authenticated consent, hardware action, notification, camera/microphone input, protected V2 evaluation or model training.

## Work basis and source/test packages

- Starting PR #8 Draft/unmerged HEAD: `1e9da4620c743b400e7eb55e4bfcf295cbe9875f`.
- **Registered READ parent digest check, 9 new cases.** `src/ark/agency/disconnected_registered_batch_receipt_set.py` now independently recomputes the domain-separated child receipt SHA-256 from the ten child fields excluding its digest, instead of accepting any syntactically valid 64-hex string. It also requires exact string scalar types. Existing single/multi-step DAG fixtures remain diagnostic-only. Source correction HEAD `b887a0e5c4b5f2bb8935d3a182a50a94d76fd242` (corrected domain byte `\\0` to Python's single-escape NUL); tests added to `tests/test_registered_batch_receipt_set_run524.py`, source+test HEAD `1692632b56cee858f80258e05543e152041cce54`.
- **Context property descriptor epoch, 6 new cases.** `src/ark/offline_context_membership_guard.py` pins the exact four no-authority property descriptors before result construction. After a final false-valued getter, an attacker cannot replace an earlier descriptor (even with another False-returning descriptor) and have the review accepted. Input metadata/counters remain independently rechecked. Source HEAD `352e6ec0248420d110dd3e33c774141f85a0aa26`; tests HEAD `4ab73b15a65328dd3682c0503a3bf2284b809343`.
- **Memory retained capture witness, 4 new cases.** `src/ark/memory/sqlite_retained_row_delta_review.py` now verifies the original witness event count, tail, event-prefix digest and row tuple after the last no-authority getter; it also pins the four witness authority descriptors. This closes a reflected post-validation field/property mutation before returning a baseline. Source HEAD `d612f37a5f88d69bec9a9109622f6d574c0c4892`; tests HEAD `fdec9059a147e3f3155a9385ccf878e18aebbf13`.

**19 newly authored pytest cases = 9 + 6 + 4.** This counts new test parameterizations, not standalone pytest PASS. Exact-head source+test GitHub Actions run [41299441373](https://github.com/Iam-2squared/ark-ai/actions/runs/41299441373) began queued; verify all six jobs and any intervening fixes before claiming full GREEN.

## Threat and non-claims

Each protection is local integrity defense against synthetic callback/class mutation, not a secure process-tamper barrier. Parent receipts do NOT demonstrate real execution, historical identity, authentic consent, dependency completion, or multi-connection SQLite atomicity. Context metadata does NOT grant retention/disclosure. Memory witness capture does NOT authenticate a writer or permit personal data export. Frozen v1 Memory DDL, V1/V2/Local UI/Launcher evidence, PermissionGate contracts and protected V3 contract were not intentionally modified.

Keep PR #8 Draft/unmerged. Next focus: exact-head GREEN matrix, cross-step READ persistence/recovery, Memory event/row CAS and expiry in one SQLite read epoch, then Trusted Clock audit-before-action and proactive occurrence deduplication, all detached from real effects.
