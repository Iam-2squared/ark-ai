# Run887 — non-UI constructor-slot CI repair, reentrant Personal Context metadata custody and revocation race instrumentation

**Authored at (JST, observed wall clock only): 2026-11-15T12:54:10.664+09:00.** This timestamp is NOT a trusted-clock attestation, user consent, provenance or verified action authority. Scope is opt-in, free-only Draft PR #8 JARVIS foundations. No frontend/UI, real tools, new services, model training, GPU compute, protected evaluation, secrets or merges.

## 1. CI regression: adversarial `__new__` monkeypatch polluted the entire Python test process

Previous checkpoint [CI #43669317602](https://github.com/Iam-2squared/ark-ai/actions/runs/43669317602) **FAIL on all 6 environments**. The inspected Ubuntu 3.13 log reported **420 failed, 15,483 passed, 1 skipped**, with the common cause `TypeError: object.__new__() takes exactly one argument (the type to instantiate)` in `src/ark/agency/disconnected_fixture_binding.py:179`. These failures were downstream test contamination, not evidence that 420 distinct production invariants had independently failed.

The Run886 test `test_replaced_exact_class_constructor_never_executes` used `pytest.monkeypatch.setattr(DisconnectedFixtureBinding, "__new__", adversarial, raising=False)`. Even after monkeypatch teardown deletes the overridden class attribute, the CPython constructor slot can remain altered for subsequent dataclass construction. This reproduces in a minimal local `dataclass(frozen=True, slots=True)` plus `pytest.MonkeyPatch` experiment. The production guard correctly refuses a replaced constructor before execution; the fault was a **test's process-level side effect**.

The normal GitHub Contents API repair commit **`6ed53c6b2e2a4acd2c13c5f32654f89d913749d4`** changes only `tests/test_disconnected_binding_constructor_slot_custody_run886.py`. The `__init__` tamper case stays in the parent pytest interpreter; the `__new__` tamper denial runs in a bounded local disposable Python subprocess (`sys.executable -c`, `timeout=20`, no networking or ToolBackend). Both still assert that an adversarial constructor never executes. This restores test isolation instead of weakening the production guard. [Post-repair CI #43674038645](https://github.com/Iam-2squared/ark-ai/actions/runs/43674038645) was **2/6 GREEN, 4 IN PROGRESS** at last observed job snapshot, NOT exact-head final GREEN.

## 2. Reentrant mutable-backed metadata validation, before sorting

`MappingProxyType` is read-only only through that proxy; its underlying dict can be changed through an independent alias while the Personal Context reviewer is hashing selected synthetic Memory records. Initial bounded UTF-8 admission alone does not guarantee safe later `tuple(sorted(record.metadata.items()))` inside `assert_snapshot_epoch`.

Normal source commit **`bdba8c85e701ada5fc4737b0f04939c48292d22e`** factors the existing projection-only shape/UTF-8 metadata checks into `_validated_context_metadata`, and reuses it at the exact later epoch comparison **before metadata sorting**. Reentrant changes cause the existing `context input changed during selection` denial; no Memory v1 storage/DDL or frozen contract changes. New tests in **`c5a5d16e8a5105bb14108a35b93d74b170acee13`**, `tests/test_personal_context_late_metadata_alias_run887.py`, cover **4 synthetic cases**: 65+ entries, 4097-codepoint value, 4097+ multibyte UTF-8 bytes, and invalid surrogate Unicode. Each injects mutation during an in-memory digest callback and asserts that no later metadata sort runs. No live personal data or external action. [Source CI #43674144037](https://github.com/Iam-2squared/ark-ai/actions/runs/43674144037) and [source+test CI #43674180062](https://github.com/Iam-2squared/ark-ai/actions/runs/43674180062) were **IN PROGRESS** at latest observed snapshot; new 4 tests are authored, not yet certified PASS.

## 3. Privacy Revocation multi-process race: safer evidence, NOT an unsafe retry

The historical [CI #43634279883](https://github.com/Iam-2squared/ark-ai/actions/runs/43634279883) showed a strict contender rejecting an `unsafe revocation SQLite sidecar`, despite another process durably committing one synthetic veto. This is an ambiguous response vs persistent ledger outcome; it does not justify replay, consent, deletion or a blanket retry.

Normal test-only instrumentation commit **`f5562a29d389a36b0f6779861fadc98cffd0237d`** updates `tests/test_privacy_revocation_cross_process_run425.py` to print **failure-only post-exception** classification of the disposable fixture SQLite main file and `-wal`/`-shm`/`-journal` names: missing/regular/symlink/directory/other, link count and inode. The parent prints a bounded diagnostic label. No full path, owner ID, digest, file content, private data or credentials are logged. This is a **post-failure pathname observation**, NOT proof of the inode that caused a rejected lstat. The strict winner/ALREADY assertions, link/orphan/symlink vetoes and no automatic WRITE retry are unchanged. Actual underlying race remains open.

## 4. Custody, evidence and limitations

- Work-basis Run886 checkpoint HEAD: `206255c9b10f8279696a7c7fe2634d37d2340a2c`.
- Four normal Contents API source/test commits in chronological order: `6ed53c6` (test-isolation repair), `bdba8c8` (Personal Context validation), `c5a5d16` (4-case test), `f5562a2` (revocation failure diagnostics). No UI/frontend/PR #5/PR #9 modification.
- Latest code/test HEAD before this report: `f5562a29d389a36b0f6779861fadc98cffd0237d`. Each source/test write reread PR #8 HEAD, and no force or hidden Git object bypass occurred.
- CI is GitHub Actions Windows/Ubuntu Python 3.11/3.12/3.13; previous exact checkpoint FAIL 6/6. Intermediate post-repair CI partially GREEN; **the latest exact HEAD full six-job result is NOT YET ESTABLISHED**. Do not claim completed JARVIS integration or advance a frozen gate based on partial observations.
- No full local repository checkout/pytest; only a minimal local CPython/pytest reproduction of the constructor-slot behavior. All synthetic adapter hashes are not independent provenance or user permission.

## Next plan / 今後の方針

1. Confirm final exact-head six-job CI for the repair, context alias regression and new diagnostic. For any FAIL, inspect the specific job log and repair semantics without weakening a frozen contract.
2. Use the bounded failure-only sidecar observations to differentiate last-close unlink windows from alias/orphan/unsafe-file cases across Windows and POSIX; never treat the observed persistent veto as consent to retry an ambiguous write.
3. Resume Memory generation-fenced CAS/coherent expiry and Planner crash UNKNOWN/terminal recovery on exact-head GREEN evidence, while keeping disconnected ToolRegistry/PermissionGate/Preaction authorization and synthetic fixture work isolated.
4. Preserve frozen V1/V2/Local UI/Launcher evidence, protected Draft PR #5, UI-paused Draft PR #9, and all free-only restrictions. Overall ARK/JARVIS remains NOT_PASSED.
