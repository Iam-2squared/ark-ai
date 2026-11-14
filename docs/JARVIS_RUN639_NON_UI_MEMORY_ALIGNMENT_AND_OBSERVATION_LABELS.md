# ARK AI — Run639 non-UI memory alignment and disconnected observation label ingress

Work basis: `7c8c5686df8d4df94f447b5b959769ab20c8b62e`, Draft PR #8 (`research/jarvis-foundations`). Source/test changes are isolated to pre-existing optional local review APIs. **No frozen v1/v2/Local UI/Launcher/V3 Contract 1 change, real action, device read, consent attestation, paid service, or main merge.**

## Package 1 — inert Memory row/event alignment report

- Source `src/ark/memory/sqlite_event_alignment.py` commit `aec1fb3674604ef54b26d00b1da9cb6c90ff5648`.
- New `tests/test_memory_alignment_report_preaccess_run639.py` commit `cffd06ef481907fbc8f20ca803fd861c46f30dee`.
- Preserve import-original result field-slot descriptors and lookup/constructor hooks before opening any SQLite read transaction; check again before interpreting the detached digest/authority flags. A forged field getter or constructor cannot become a supposedly content-free report merely because it returns a plausible value.
- **8 regression cases authored**: seven pre-access substitutions (exported class, initializer, two slots, two attribute hooks, authority getter), plus clean repeatable digest-only audit. No test patches the existing Python class's `__new__` (prior CPython `tp_new` mutation contaminated later tests). No Memory schema, CAS mutation, deletion, or reconciliation writes.

## Package 2 — bounded UTF-8 observation review labels

- Source `src/ark/observation_fixture_chain_review.py` commit `8470347c7f54622d0dec1ab61c1ba4dcb7080d77`.
- New `tests/test_observation_fixture_label_ingress_run639.py` commit `72abd1cdfa1ff6aecd36fb8a646d8a0f48e20f06`; literal-surrogate fixture correction `3030ce79e53355ee1a7492a2a54f0bdc38c092fb`.
- Reject blank, over-1024-character, or non-UTF-8 caller labels before examining any caller-provided observation envelope fields, while retaining valid multilingual labels. This mirrors existing `ObservationEnvelope` label bounds without changing its constructor or broader DAG semantics.
- **7 regression cases authored**: six invalid labels with an impossible-envelope-read sentinel, plus a Japanese source/scope success case. All observation inputs are synthetic text. No microphone, camera, real media, retention, network, notification or tool dispatch.

## Validation and evidence integrity

- Previous work-basis exact-head [CI #42070083473](https://github.com/Iam-2squared/ark-ai/actions/runs/42070083473) was inspected: Ubuntu and Windows × Python 3.11, 3.12, 3.13 **6/6 GREEN**.
- Run639 source/test CI starts automatically after every normal GitHub Contents write; no duplicate manual CI dispatch. [Memory source/test #42078463914](https://github.com/Iam-2squared/ark-ai/actions/runs/42078463914) was Ubuntu 3/3 GREEN, Windows in progress at last inspection; [newest observation test correction #42078860946](https://github.com/Iam-2squared/ark-ai/actions/runs/42078860946) was queued at first read. **Latest exact-head 6/6 GREEN not yet verified.**
- 15 means *authored test cases*, not fifteen observed pytest PASS. Local `git ls-remote` returned `Could not resolve host: github.com`; no local checkout, Ruff, or pytest proof. GitHub CI results are the validation authority, with exact commit/run IDs; green results from older HEADs cannot certify newer commits.
- The local alignment digest is **not independently authenticated custody**. It cannot prove an attacker did not rewrite both Memory rows and event history. A fixture content hash is **not capture provenance, user consent, or dispatch authority**. All denied authority properties remain False-only.

## Preserved gates and next work / 今後の方針

1. Verify the final source/test HEAD and checkpoint HEAD Ubuntu/Windows 3.11–3.13 CI; inspect actual job logs for any failure before a minimal semantics-preserving Contents API correction. No duplicate CI runs.
2. After exact-head GREEN, prioritize Memory CAS row/event/expiry coherent history, Planner journal terminal/crash recovery, and registry-bound PermissionGate, audit-before-action and one-shot mock-only integration.
3. Continue independent privacy-safe Personal Context, proactive/observation fixture contracts, and free-only V3 identity/path/provenance guard audits. Frozen V3 real-training and protected V2 final-evaluation gates remain unopened.
4. PR #5 remains Draft/unmerged; PR #9 remains Draft/unmerged and **ALL NEW UI/FRONTEND WORK PAUSED**. PR #8 remains Draft/unmerged. No real ToolBackend, external GPU/compute, paid API, Candidate/weights, credential/account connection, hardware action, human decision, irreversible erasure, automatic replay, or approval-required main merge. **ARK/JARVIS/V3 NOT_PASSED**.
