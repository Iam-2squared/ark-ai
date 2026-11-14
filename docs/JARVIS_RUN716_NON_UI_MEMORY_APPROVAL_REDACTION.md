# ARK AI — Run716: Memory timestamps, claim identity, privacy redaction and PNG fixture digest

**Scope:** Four independent, reversible, **FREE-ONLY NON-UI** work packages on Draft PR #8 (`research/jarvis-foundations`). No UI work, live tools, real/private data, Candidate, GPU, paid service, new credential, evaluation opening, human approval or main merge.

## Exact initial state and prerequisite

- Initial exact PR #8 HEAD: `768fe2f84b4a6737a0b04694defd0c9dd9ae877f`; canonical status was Run715.
- Previous checkpoint exact-head [CI #42497450451](https://github.com/Iam-2squared/ark-ai/actions/runs/42497450451) is **6/6 GREEN** (Ubuntu/Windows; Python 3.11–3.13). Later HEAD checks are separate evidence.
- PR #5 remains OPEN/Draft/unmerged at `805b377697472268db02650a89c7a94b1c5337c8`; PR #9 remains OPEN/Draft/unmerged, UI paused, at `3b49048dd70eebcb6268299b9ecef4e301bbc0fd`. Frozen V1/V2/Local UI/Launcher evidence and protected V3 gates were not changed.

## Package A — Memory lifecycle timestamps in ONE coherent WAL read

- Production [`262ba215`](https://github.com/Iam-2squared/ark-ai/commit/262ba215ebf14de790532d6eebbe0d92846d812c), `src/ark/memory/sqlite_retained_coherent_review.py`: records live row creation/update times along with owner, namespace and revision. Reconstructs each active lifecycle's CREATE timestamp and most recent CREATE/UPDATE timestamp from that *same* pinned WAL event scan and compares the complete five-field tuple, even if a valid unrelated-owner event advanced the global history and `prior_rows` was omitted. A terminal DELETE/EXPIRE requires absence of the live row. Nonmonotonic synthetic clock values remain valid; no global time-order requirement was added.
- [Six authored regressions `1911251e`](https://github.com/Iam-2squared/ark-ai/commit/1911251ec863eaf3cb3ca4b1bec6523acfa1948b), `tests/test_memory_coherent_timestamp_lifecycle_run716.py`: unchanged and legitimately updated Memory timestamp rewrites concealed by an unrelated owner append; valid updated/foreign-owner and backward-clock controls. Disposable local SQLite only.
- Limits: This checks **locally self-consistent timestamps**, not independently authenticated provenance. If a malicious writer rewrites *both* retained events and local `sqlite_sequence`, local-only evidence may be forged. When event count advances and no independently retained `prior_rows` exists, content/metadata/expiry rewrites without corresponding own events may remain undetectable. This is read-only denial/diagnosis, not an atomic authorization fence or permission to retry a COMMIT-UNKNOWN write.

## Package B — synthetic approval claim digest dependencies

- Production [`48423ea4`](https://github.com/Iam-2squared/ark-ai/commit/48423ea412ab24869157fc47e3e0d0cfb2251ca4) pins import-time `hashlib.sha256` and `json.dumps` in the existing original-carrier check, before an injected serializer/hash callback can receive a claim's synthetic issuer/subject/purpose/recipient data.
- [Five authored regressions `07aac427`](https://github.com/Iam-2squared/ark-ai/commit/07aac427654106658d8e8e8e5a0246071aa7e5be) exercise swapped hash/JSON callbacks at both make and review entry with call counters, and original hash behavior. Fixture inputs are synthetic. Existing registry/action binding and denial-only semantics unchanged.
- Limits: static process-local dependency pinning is **not authenticated issuer identity, actual human consent, trusted clock, revocation proof or authority to dispatch**.

## Package C — privacy-safe redaction SHA before private bytes

- Production [`2005ce54`](https://github.com/Iam-2squared/ark-ai/commit/2005ce54b1ce425f49164066448c31d4ae31799d) pins original `hashlib.sha256` at import and rejects a substituted hasher at `_require_original_denials`, before `preview_offline_redaction` hashes provided fixture text. The original local deny-only result fields and masking semantics remain unchanged.
- [Three authored regressions `a99c656c`](https://github.com/Iam-2squared/ark-ai/commit/a99c656cd4abd2c00a98ecafa096bda0263cff3d) cover full and partial masking modes with poisoned callbacks that must never receive fixture bytes, plus an unmodified fully masked result.
- Limits: process-local callback pinning is not an adversarial sandbox, full redaction is not erasure, and even complete masking grants no external-export permission. **Open review:** other unpinned JSON-related callbacks are exercised in the legacy serializer-negative-test path; evaluate a *separate*, test-aware preaccess custody change without invalidating in-flight CI or incorrectly treating a hash as consent.

## Package D — synthetic PNG digest preaccess

- Production [`637ec82c`](https://github.com/Iam-2squared/ark-ai/commit/637ec82c7ca479a3c55021e9bc6d3d56f609b910) pins the import-time `hashlib.sha256` identity before any raw caller-owned PNG bytes reach the checksum implementation. It does not decode pixels or change the canonical inventory policy. A replaced SHA callback is rejected rather than invoked.
- The inherited synthetic digest injection test was strengthened in [`7a0861b1`](https://github.com/Iam-2squared/ark-ai/commit/7a0861b16f849ab7b91eb85b20b05080c5c98810): now requires **zero callback invocations before denial**, rather than waiting until the callback has had an opportunity to mutate a denial descriptor. [Three new cases `017174f0`](https://github.com/Iam-2squared/ark-ai/commit/017174f0193477f4d023132ec34ed429c0fe6f26) test matching/nonmatching source SHA plus healthy original hash.
- Limits: This is process-local guardrail, **not** authenticated image origin, user consent, CRC integrity proof, or permission to open camera/screen. `zlib.crc32` and structural unpack callback dependencies merit separate review after matched CI, without stacking changes onto the same in-flight validation path.

## CI / evidence / verification posture

- Prior source basis CI #42497450451: **6/6 GREEN**, checked via six completed successful jobs.
- Package A tests HEAD `1911251ec863eaf3cb3ca4b1bec6523acfa1948b`: [CI #42501394862](https://github.com/Iam-2squared/ark-ai/actions/runs/42501394862), **IN PROGRESS** when last queried.
- Package B tests HEAD `07aac427654106658d8e8e8e5a0246071aa7e5be`: [CI #42501617066](https://github.com/Iam-2squared/ark-ai/actions/runs/42501617066), **IN PROGRESS** when last queried.
- Package C tests HEAD `a99c656cd4abd2c00a98ecafa096bda0263cff3d`: [CI #42501861587](https://github.com/Iam-2squared/ark-ai/actions/runs/42501861587), **QUEUED** when last queried.
- Package D tests HEAD `017174f0193477f4d023132ec34ed429c0fe6f26`: [CI #42502281381](https://github.com/Iam-2squared/ark-ai/actions/runs/42502281381), **QUEUED** when last queried.
- **17 authored tests, 4 production files, 4 new test files and 2 inherited test methods adjusted** (one PNG and one parameterized Memory method, the latter covering two failing cases).
- **Actual intermediate CI failure evidence:** [#42501394862](https://github.com/Iam-2squared/ark-ai/actions/runs/42501394862), [#42501617066](https://github.com/Iam-2squared/ark-ai/actions/runs/42501617066), [#42501861587](https://github.com/Iam-2squared/ark-ai/actions/runs/42501861587) all exposed the same inherited `tests/test_memory_coherent_row_delta_run514.py` assertion mismatch on `created_at_ms` and `updated_at_ms`. Actual Ubuntu 3.11 logs: first head **2 FAIL, 11,175 PASS, 1 SKIP**, second **2 FAIL, 11,180 PASS, 1 SKIP**, third **2 FAIL, 11,183 PASS, 1 SKIP**. The new coherent time check *correctly rejects earlier* with `live Memory row/time differs from event lifecycle`; legacy parameterized cases still required the later optional row-witness message `without its own`. The [test-only repair `c0764b3`](https://github.com/Iam-2squared/ark-ai/commit/c0764b3ea5e0dde9c81aee7779afc16c3001bf6a) accepts only the appropriate earlier message for timestamp cases while retaining the original row-witness message for metadata/expiry cases; no source semantics weakened. [Corrected exact-head CI #42502488847](https://github.com/Iam-2squared/ark-ai/actions/runs/42502488847) was **QUEUED** at last observation. Neither it nor the final report/checkpoint head is yet certified all-six GREEN. No local complete pytest/Ruff or physical-PC GGUF run; no latest-head all-six GREEN claim before final matching job evidence. All GitHub writes used normal Contents API and new HEAD reads, no raw-object, force-push, hidden route or concurrent overwrite. Automatic CI only, no duplicate manual workflow runs.

## Next plan / 今後の方針

1. Verify exact-head six-job CI for the final checkpoint; use real logs and minimal fixes for any failures, then work on another independent non-UI lane while CI runs.
2. Memory: further CAS/ABA and COMMIT-UNKNOWN manual outcome boundaries; ensure retained row commitments/replay evidence when legal foreign-owner append advances event count. Never automatically retry ambiguous writes.
3. Planner: independently retained step input manifest and restart-safe terminal/UNKNOWN proofs, while explicitly **not** treating READ hashes as proof of invocation.
4. Claim/Privacy/Observation: inspect JSON digest machinery before masked personal text can reach substituted callbacks, and PNG CRC/framing dependency integrity before raw fixture data. Preserve existing regression semantics, strengthen audit-before-action and occurrence-bound mock-only authorization.
5. Keep PR #5/#8/#9 Draft/unmerged; UI paused, frozen contracts/evidence unchanged, all paid/GPU/credentials/evaluation/Candidate/hardware/human-approval/main-merge boundaries closed. Overall ARK/JARVIS/V3 **NOT_PASSED**.
