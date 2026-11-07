# ARK AI Run684 — non-UI observation scope, Memory expiry WAL, Planner diamond evidence

**2026-11-07 JST — FREE-ONLY / UNMERGED / MOCK & DIAGNOSTIC ONLY**  
Initial work basis: `2d40c4e85857475ed8a70b2a1157f84ef43ec68e` (Run683 checkpoint, [CI #42361397759](https://github.com/Iam-2squared/ark-ai/actions/runs/42361397759) COMPLETED 6/6 GREEN). Branch: `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8). Report write basis: `0df906348fcdb0a3504705bfb598a967594266dc`. Audit note captured at administrative UTC `2026-11-07T10:55:35.076Z` (not a trusted clock/consent attestation).

## Package A — Observation privacy scope ingress

- Production `src/ark/observation_rollover_review.py`: `a41984cd6d4c79f225d715bd91e8e94d9bbb39f2`. The direct `ObservationRolloverWitness` constructor now rejects non-UTF-8 and privacy scope labels over **1024 encoded UTF-8 bytes** (including multibyte-only overflow), matching `ObservationEnvelope` metadata budget. No capture, notifications, model, UI, external network or dispatch implementation.
- Tests `tests/test_observation_rollover_utf8_budget_run684.py`: initial `7f915a313ef9786201a4b7c686ebde8dc1952423`, seven parameterized/plain cases including 1024-byte boundaries, non-ASCII labels, invalid surrogate, blank scope and a complete disconnected two-window rollover.
- CI #42365641814 found **one test-fixture mistake**: the string `"bad\\ud800"` was a literal backslash sequence, not an unpaired Unicode surrogate. This was a test-only failure, NOT a production protection bypass. Normal Contents API correction `0df906348fcdb0a3504705bfb598a967594266dc` constructs `"bad" + chr(0xD800)` to exercise strict UTF-8 rejection. Safety check unchanged.

## Package B — concurrent Memory expiry and WAL epoch

- New `tests/test_memory_cross_scope_expiry_wal_epoch_run684.py` at `3e9da4f6e29d4a231baf1091b61f723762649afa`: **3 scenarios**. A separate SQLite writer runs scoped expiry purge while a retained row/event coherence scanner has already pinned a WAL read transaction: expiry only, expiry and same-ID new lifetime, or expiry and other-owner creation.
- Old read must remain exactly the pre-expiry row/event snapshot. A new independent read must show the full advanced event/row/scope epoch, never a mixed intermediate. Each result denies historical writer/consent/cross-store authentication and action authority. No Memory v1 schema changes or destructive physical-data actions; temporary synthetic SQLite fixtures only.

## Package C — Planner registered READ diamond proof

- New `tests/test_planner_diamond_registered_read_bundle_run684.py` at `705dec037e359e47b8b224979f8525e0f6edd2c9`: **6 scenarios** on a four-step A→B,C→D diamond. Each SUCCEEDED ancestor and sibling must supply a distinct independently retained registered READ receipt; evidence ordering does not change the deterministic bundle. Omitting any one of four receipts rejects, and a pending D does not imply success evidence for D.
- Test uses an inert backend that raises if invoked; no actual external outcome, WRITE permission, autonomous dispatch, persisted cross-store transaction, or replay is claimed.

## CI and evidentiary scope at report preparation

- Prior exact Run683 checkpoint `2d40c4e85857475ed8a70b2a1157f84ef43ec68e`: [#42361397759](https://github.com/Iam-2squared/ark-ai/actions/runs/42361397759), **6/6 GREEN**.
- Observation source [#42365600533](https://github.com/Iam-2squared/ark-ai/actions/runs/42365600533): intermediate; observation test [#42365641814](https://github.com/Iam-2squared/ark-ai/actions/runs/42365641814): Ubuntu 3.11/3.12 FAIL caused by the escaped-surrogate fixture, now corrected.
- Memory expiry [#42365736215](https://github.com/Iam-2squared/ark-ai/actions/runs/42365736215): in_progress; Planner diamond [#42365840439](https://github.com/Iam-2squared/ark-ai/actions/runs/42365840439): in_progress.
- Corrected observation fixture [#42365902339](https://github.com/Iam-2squared/ark-ai/actions/runs/42365902339): queued at sampling. The report itself and final canonical status produce distinct exact HEADs with their own automatic CI. Never inherit an ancestor's GREEN for those HEADs.

## Boundaries and next integration prerequisites

Frozen V1/V2/Local UI/Launcher contracts and all protected V2 evaluation evidence remain unchanged; V3 [Draft PR #5](https://github.com/Iam-2squared/ark-ai/pull/5) stays under the separate spend/approval and provenance gate. [Draft UI PR #9](https://github.com/Iam-2squared/ark-ai/pull/9) is untouched and non-UI work continues. PR #8 remains Draft/unmerged; main untouched.

Before connecting a real executor, independently require exact-head GREEN for Planner, immutable Registry identity, exact PermissionGate effect, authenticated explicit consent, trusted-clock audit-before-action, durable occurrence reservation, and a reviewable non-replay policy for unknown outcomes. Private SQLite hashes and fixture receipts do not constitute authenticated provenance or cross-store atomicity. No paid or external GPU, new API, credentials, candidate weights, protected final-evaluation opening, merge or physical-machine action was initiated.
