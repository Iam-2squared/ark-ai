# Run532 — Memory generation, Planner terminal and Scheduler due-preview safety

**Detached, synthetic, free-only ARK/JARVIS groundwork.** No real ToolBackend,
scheduler notification, WRITE, GPU, Candidate, protected V2 evaluation or
external effect. All hashes are local continuity observations, **not signed
human approval, trusted clock or writer provenance**.

## 1. Retained Memory CAS generation fence (21 authored cases)

New source: `src/ark/memory/retained_generation_fence.py`, commit
`884b4f8cf4765bb23b5d2bfb85825a29c78968c4`.
New tests: `tests/test_memory_retained_generation_fence_run532.py`, commit
`01e65cdb7ad8934f2ed1839a5870a204e75ac08d`.

`verify_retained_memory_generation` requires the caller's **separately
retained** exact `MemoryGenerationReview` and independently resamples
one SQLite v1 snapshot using `review_memory_revision_reuse`. It rejects
event-history updates, deletion, recreated deterministic IDs **even if
revision 1 recurs**, changed expected revision, false-valued mutating authority
getters, forged hashes/counts, and local SQLite event tampering. It only
returns `None` on agreement. **It is NOT a transactional compare-and-swap
write**: another writer can commit immediately after this read; it does not
fix ABA at the original v1 write API or authenticate an event's author.
No frozen schema or `SQLiteMemoryStore.put` behavior changed.

## 2. Hypothetical Planner terminal result post-denial custody (6 authored cases)

Modified `src/ark/agency/disconnected_batch_terminal_projection.py`
at `b99e2f09c4515002048c8be9b87a407b536134c5`; added
`tests/test_disconnected_terminal_postdenial_run532.py` at
`c6ed56894c8c40333136e1997e57fa2f94385ce5`.
A final property getter returning False may still rewrite a preceding
descriptor, the terminal report, DAG step or schedule. The returned
report's fields, authority descriptors, original plan and schedule are
revalidated after **every** denied-authority callback. Failed/blocked states
remain purely hypothetical. No external step is dispatched, no execution
or completed dependency is attested.

Initial source/tests CI `41317964343` on `c6ed5689...` reported
four older test assertion failures solely because the stronger rejection used
a different error string. The compatibility-only source update at
`9530841245b0ccb076ba343890ddd04dc338c676` restored the previously
expected `terminal receipt changed` message, **not** a weaker guard.
This corrected source requires exact-head CI verification.

## 3. Scheduler due-preview non-authority descriptor epoch (6 authored cases)

Modified `src/ark/disconnected_schedule_preview.py` at
`34ad9b2ba59cd4112b030e9b1d134d4cb88955ed`, and added
`tests/test_schedule_preview_descriptor_epoch_run532.py` at
`283a968bc1a6aa2671ddda0ce6522648c6877e42`.
Each denied `trusted_clock_verified`, `notification_authorized`,
`tool_execution_authorized`, `automatic_replay_authorized`, and
`consent_verified` getter is followed by a fresh exact result check,
caller-policy/cursor check and pinned class-descriptor comparison. A final
False consent getter cannot silently set an **earlier** notification/tool
descriptor True. A due label remains just a caller-clock observation:
no authenticated clock, automatic dispatch or consent.

Earlier scheduled CI `41318252693` included the still-unfixed Planner
error-string expectation; do not count it as latest corrected-head GREEN.

## Exact-head test semantics and boundaries

The three packages contain **33 initially authored parametrized pytest cases**
(21 Memory + 6 Planner + 6 Scheduler). Authored-case counts are not local
pytest PASS counts. The source/test changes remain isolated on PR #8
(`research/jarvis-foundations`), Draft/unmerged. No main merge or V1/V2
contract rewrite. The first Memory test run `41317618747` and later
Planner/Scheduler runs must be checked per exact HEAD; inherited GREEN from
a previous SHA is not valid on a newer SHA.

This documentation commit and the eventual canonical project checkpoint
are also distinct heads. Recheck their CI separately. No costly action
or real ToolBackend is permitted by this work.

## Follow-on engineering

1. Confirm corrected PR #8 CI; repair only real test/source issues without
   bypassing GitHub Contents normal permissions.
2. Design an opt-in generation-aware CAS **transactional** boundary behind
   an explicit integration contract; never treat a read-only fingerprint as
   an atomic write guard.
3. Join Planner persisted mock history, registry-bound READ receipt and
   terminal propagation in a disconnected integration test.
4. Extend trusted-time audit-before-action, restart occurrence uniqueness,
   consent/retention privacy and safe startup, still mock/local-first.


## 4. Independent privacy erasure descriptor boundary (6 authored cases)

Source `src/ark/privacy_erasure_evidence_review.py` at commit
`94cbb57ecc693a7360f84582cff0344f4eca8a97`, new
`tests/test_privacy_erasure_descriptor_epoch_run532.py` at commit
`784dbb79484573d75bc25d85db66289b60f5f1e2`.

The optimistic synthetic erasure assessment previously evaluated all four
denied-authority getters but could not detect a late false-returning getter
**replacing an earlier property descriptor**. The new source pins each
`SyntheticErasureAssessment` class descriptor before reentrant permission
reads and checks its identity at the result boundary. Six cases cover a
normally inert assessment plus first/final false-authority callbacks which
replace an earlier or later denied property, even with another false-looking
property.

This does **not** prove forensic deletion, memory erasure, WAL compaction,
consent, or backup deletion. No file or database deletion is performed. The
older return fields and rejection message stay unchanged.

**Run532 total: 39 newly authored PR #8 parametrized pytest cases**:
21 Memory, 6 Planner, 6 Scheduler, 6 privacy. Together with the distinct
16-case PR #5 V3 review package: **55 new authored cases in five packages**.
Counts are not standalone local pytest PASS counts. CI must be verified for
the exact corresponding head after this latest privacy change.
