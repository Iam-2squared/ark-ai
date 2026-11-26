# Run805 — Non-UI Core: SQLite Schema, Proposal, V3 Packet, Memory Privacy

**Scope:** Only `research/jarvis-foundations`, Draft PR #8, reversible detached/local core. **Work-basis HEAD:** `462ca29c63310f6febc7385f595b2ecf7f2ec23d` (Run804 checkpoint). **Report-write-basis HEAD:** `92067d5a3efb38e6d0fde7d034f7cea463333811`; the report commit itself will have a different SHA. No claim of end-to-end JARVIS PASS, authenticated provenance or real-device measurement.

## Four independent source-and-regression packages

1. **SQLite synthetic schema snapshot descriptor/codec custody.** Source commit `cea668a731ac32967993aaf13898a23a1cc7b25c` (`src/ark/disconnected_sqlite_schema_probe.py`) pins the original seal slots, lookup/initializer hooks, deny-only flags, schema query, digest/JSON implementations and scan budgets *before* reading private SQLite schema metadata. Checks again after codec calls; still does not authenticate source or WAL custody. Test commit `c318ffee3d637b8a9fd0b963ba34438b6ffa5795`, corrected test-safety commit `99d34650cd5b7ffafdaa2163c97377356c73e47b`, `tests/test_disconnected_schema_probe_preaccess_run805.py`: **34 parameterized cases**, avoiding monkeypatch of inherited `__new__` and restoring originally inherited lookup hooks by deletion.

2. **Proposal SQLite witness/snapshot lookup guard.** Source commit `156978d194d49b101c2ce294d6ae88f0f45092bd` (`src/ark/agency/disconnected_proposal_store.py`) rejects class-level swapped `__new__`, `__getattribute__` or `__getattr__` before accessing stored synthetic proposal witness or snapshot. Test commit `b7b878ff5789c52e01cc8166f70d8a95ed068963`, Ruff UP035 import-only fix `92067d5a3efb38e6d0fde7d034f7cea463333811` (`tests/test_disconnected_proposal_lookup_hooks_run805.py`): **5 cases**. Tests do not patch inherited `__new__`. This neither proves human approval nor authorizes automatic retry, code edits or promotion.

3. **V3 packet exponent overflow.** Source commit `f4dd9a2d5fa110378a0aadba902410ec4db02d11` (`src/ark/v3_detached_packet_review.py`) catches strict JSON canonicalization failures after an exponent such as `1e999` decodes to nonfinite Python float; reports a domain-specific `DetachedV3PacketRejected`, not an unhandled serializer `ValueError`. Test commit `d0ab0b1cb6d0220338529578925484818e8f82ff`, `tests/test_v3_packet_overflow_run805.py`: **14 cases**, including positive/negative overflow, alternate numeric serialization and denial-only valid control. No GPU invoked; no change to PR #5's protected contract.

4. **Memory retained-row-delta private digest preaccess.** Source commit `1d16aee8f30c3bcd48fa43e55784c75d8e971b4b` (`src/ark/memory/sqlite_retained_row_delta_review.py`) pins imported JSON/SHA-256 modules/functions and two digest domains before SQLite row scans and digest construction; rechecks across digest boundaries. Existing `_commitment` and `_scan` fault-injection seams remain, preserving legacy snapshot-interleaving tests. Test commit `f07397caede4bfe56a8deae59d7e8a5011bbeabd`, `tests/test_memory_row_delta_digest_preaccess_run805.py`: **9 cases**. Neither witness nor digest independently authenticates writers or permits private content disclosure.

**Total newly submitted Run805 regression cases: 62** (34 + 5 + 14 + 9). Submission is NOT a claim of passing tests. No local repository checkout or full local pytest/Ruff execution was available; GitHub Actions is the authoritative observable CI, pending exact-head verification.

## Exact CI evidence and known failure

- Prior Run804 checkpoint `462ca29c63310f6febc7385f595b2ecf7f2ec23d`, [Actions #43127438154](https://github.com/Iam-2squared/ark-ai/actions/runs/43127438154): **GREEN six of six** (Ubuntu/Windows Python 3.11–3.13), observed during Run805. This is a *prior HEAD*, not Run805 validation.
- Intermediate Run805 [#43129756257](https://github.com/Iam-2squared/ark-ai/actions/runs/43129756257): **FAIL six of six on Ruff check**, job `130890659060` concretely reported `UP035` for `from typing import Iterator` in the new proposal test. Import-only correction `92067d5a3efb38e6d0fde7d034f7cea463333811` imports from `collections.abc`, leaving behavior and assertions unchanged. Failures on earlier commits with the same new test are not independent semantic regressions.
- Post-import correction [#43130299031](https://github.com/Iam-2squared/ark-ai/actions/runs/43130299031): **IN PROGRESS** at last inspected state, associated with `92067d5a3efb38e6d0fde7d034f7cea463333811`. All six GREEN, if eventually obtained, is specific to that commit only; report and checkpoint commits will require their own exact-head observation. Do not reuse earlier GREEN.

## Authorization, isolation and limitations

- PRs #5/#8/#9 remain Draft/unmerged at report preparation; PR #9's UI branch is not modified and **new UI/frontend work remains paused**.
- Frozen V1/V2/Local UI/Launcher evidence, V3 Contract 1 and protected V2 evaluation are unchanged. No new credentials, paid GPU/API/service, Candidate/weights, real tool dispatch, human approval, automatic WRITE/COMMIT-UNKNOWN retry, destructive privacy erasure, protected evaluation or main merge.
- Python runtime descriptor/codec fences detect selected *in-process* substitutions; they are not a general-purpose sandbox, signature, independent storage provenance, trusted audit clock, human consent or file-race guarantee.
- Branch-level CI is a necessary code-integrity signal, not physical-PC GGUF evidence or a gate override.

## Prioritized follow-up

1. Inspect exact-head CI six-job outcomes for the final checkpoint commit. If any FAIL, diagnose concrete logs and make the smallest semantics-preserving repair through normal GitHub Contents API; switch to an independent non-UI module while CI is in flight.
2. Continue Memory CAS/ABA/expiry/COMMIT-UNKNOWN and Planner persistence/UNKNOWN quarantine. Preserve deliberately fault-injected concurrency tests; do not weaken them to force GREEN.
3. Link immutable registry identity, exact-type PermissionGate, durable occurrence and audit-before-action solely to mock/disconnected execution after lower-level head-specific evidence.
4. Advance privacy-safe Personal Context, scheduler readiness, observation fixtures and free V3 identity guards. Preserve Draft #5 gate and paused Draft #9/UI. **ARK/JARVIS remains NOT_PASSED.**
