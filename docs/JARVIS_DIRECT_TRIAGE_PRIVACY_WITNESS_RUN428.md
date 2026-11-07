# ARK AI — Run428 direct-recovery and privacy veto-witness custody

**Work basis:** Run427 checkpoint `c77329caaef2594b44091b8a591378b75200846c`, branch `research/jarvis-foundations`, Draft PR #8. This document covers local, disconnected READ-only review functions and does **not** authorize real ToolBackend dispatch, human approval, persistent exactly-once external effects, new paid services, protected V2 evaluation, or model/Candidate training.

## Package 1 — final direct WRITE triage result integrity (+6 pytest cases)

**Source:** `src/ark/agency/synthetic_recovery_triage.py` source commit `3a5b96f91e7666770f1b4f48ff83a146862df204`; tests `tests/test_triage_result_epoch_run428.py`, test commit `8b762562d9e8da195cfe0bdfaa015055fa94f9e9`.

The single-WRITE recovery reader already rejects mismatched persisted local Plan/Occurrence/ActionAudit/Link identities and never dispatches a backend. Its **final returned dataclass constructor** was a separate reentrant/reflectively mutable boundary. The new guard retains the original bound action, recovered plan and plan-tail field carriers throughout the independent SQLite readers; validates an exact returned diagnostic type and every constructor-provided field after the constructor runs; then checks the full original input epoch again. Constructor injection can no longer return a fabricated SUCCEEDED step, a forged non-review object, an equal-text-but-replaced PlanTail digest, or a mutated caller/BoundAction carrier as if recovery evidence remained unchanged.

The tests use a strictly non-executing backend and local SQLite fixtures. Existing request-id derivation, approved effect classification, frozen schemas and no-replay policy are unchanged.

## Package 2 — retained privacy veto witness across separate checks (+4 pytest cases)

**Source:** `src/ark/personal_context_revocation_review.py` source commit `702fc81c622e945e9fd05013e96688312baaff57`; tests `tests/test_context_initial_revocation_witness_epoch_run428.py`, test commit `045a8aa9f56a05fba3f8f78d92ba6aba1e867ff9`.

The Personal Context read performs independent revocation-prefix replay, pre-Memory veto, Memory projection, post-Memory veto and a final retained-history replay. Previously a callback could reflectively substitute the **first** returned witness rows/digest with value-equal new carriers before the last replay, effectively altering the original continuity reference without changing hashes or consent. The new guard pins the original witness, its tuple-of-rows carrier, every constituent row carrier, and the original digest; rechecks those original objects at every existing epoch fence across the subsequent privacy/Memory checks. A non-exact initial witness and inconsistent witness integrity now fail closed. It remains a local content-free diagnostic, **not** a real authenticated consent, deletion or usage decision.

New tests inject equal-valued witness/digest substitutions during the first veto, second veto and last retained replay; a normal, unrelated revocation case must remain a deny-only context projection. No Memory V1 schema or real private data changes.

## Validation / evidence interpretation

At initial implementation, existing last verified checkpoint `c77329caaef2594b44091b8a591378b75200846c` had CI **#1183 / 40205112719 SUCCESS**, and preceding corrected executable HEAD `f00b6f852e728f1d1e199c4a1ffd1fe2860125c5` had **#1182 / 40204720625 SUCCESS**. The unrelated historical engineering-document CI **#1181 / 40204600499 FAILED** remains an actual failed run. **New commits must be judged by their exact-head CI**, not the prior checkpoint, and may still have Windows jobs in progress. New source/test runs: **#1184 / 40208630060**, **#1185 / 40208701338**, **#1186 / 40208854355**, **#1187 / 40208913492**; consult each run before making GREEN claims. No manual duplicate workflow runs were triggered.

## Limits and following safe work

These guards address direct local mutable-object and callback integrity; they cannot authenticate a malicious OS, secure a real cross-file atomic snapshot, prevent arbitrary privileged in-process tampering, attest real-world WRITE outcomes or grant external exactly-once execution. UNKNOWN/RUNNING and reserved PENDING WRITE stay quarantined and never automatically replayed. Follow up with read-only multi-WRITE/orphan audit fault injection and true multiprocess CAS/expiry/snapshot tests when exact-head CI and frozen contracts permit; keep V3 PR #5 Draft/unmerged/NOT_PASSED and all financial/hardware/model gates closed. Frozen V1/V2/Local UI/Launcher, Memory V1 SQL, ActionAudit V1 SQL and V3 Contract 1 remain untouched.
