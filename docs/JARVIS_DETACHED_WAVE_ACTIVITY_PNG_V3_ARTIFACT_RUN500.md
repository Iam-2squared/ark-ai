# Run500 — Detached wavefronts, independently rechecked fixture reports, and V3 JSON identity custody

This document records *source-level behavior*, not system authorization, complete integration, final CI PASS, user consent, attested provenance, or real tool effects. The two feature branches are independent, reversible and intentionally Draft.

## Foundation A: offline PCM region report re-verification

- PR #8 `src/ark/offline_pcm_activity_regions.py`: `verify_activity_regions(report, pcm, expected_sha256, sample_rate, ..., threshold controls)`.
- Independently retained exact PCM bytes, SHA-256 and threshold parameters are recomputed with the existing bounded activity-grouping algorithm. The resulting frame counts, sample boundaries and every region's exact integer fields must match the detached report.
- Rejects subclass/duck-type reports, bool-as-int, mutable region arrays, changes to source hash and late reflected alteration during recomputation.
- Returns `None` on success, not an execute/disclose or microphone permission grant. A caller recycling untrusted thresholds cannot infer authenticity.
- Fixture tests: `tests/test_offline_pcm_activity_detached_verify_run500.py` (15 pytest cases defined).

## Foundation B: deterministic detached batch wavefronts

- PR #8 new `src/ark/agency/disconnected_batch_schedule.py`.
- Calls the existing `verify_disconnected_batch_plan` with a caller-retained plan digest. Each output wave contains every currently dependency-ready step ID in original plan order; dependencies become ready only in later waves.
- Derives a domain-separated canonical SHA-256 over `request_id`, `plan_digest` and ordered wave IDs. Rechecks the plan after wave construction and after the result's denial-only getters. `verify_disconnected_batch_schedule` separately recomputes membership.
- Pure preview: no ToolRegistry dispatch, scheduler start, parallel executor, WRITE permission, replay, clock observation, billing, or real ToolBackend.
- Later integration requires independent exact-head CI evidence for registry-bound identity, PermissionGate and durable occurrence fencing before even considering a mock executor coupling.
- Fixture tests: `tests/test_disconnected_batch_schedule_run500.py` (12 cases defined).

## Foundation C: IDAT scanline witness re-verification

- PR #8 `src/ark/offline_png_scanlines.py`: `verify_offline_png_scanlines(audit, request)`.
- Reuses the bounded zlib/raw-row decoding and palette validation, then compares the detached report's IDAT SHA, reconstructed SHA, geometry, raw length and five filter counts against independently retained request bytes.
- Exact result type and denial-only source/capture/consent/export properties are checked. Does not yield pixels.
- It does NOT prove PNG container integrity, actual camera capture, user consent, or authorization to disclose observation data.
- Fixture tests: `tests/test_offline_png_detached_verify_run500.py` (12 cases defined).

## Foundation D: independent V3 offline artifact byte check

- PR #5 new `src/ark/learning/identity_artifact_verify.py`.
- `verify_local_identity_artifact(path, retained_sha256=...)` reads existing identity JSON from disk only, bounded to 8 MiB. Rejects missing/aliased symlink or hardlink paths, non-regular files, substituted descriptor identity, size/mtime drift, noncanonical whitespace, duplicate keys, nonfinite JSON and mismatching independently retained SHA-256.
- The JSON canonical form is the *existing* V3 `canonical_json`, not a modified frozen contract. A returned witness includes the hash, byte count and top-level field names, plus explicit denial-only authority flags.
- On its own, a matching JSON hash cannot authenticate the claimed HF revision, source files, GPU runtime, human review or Candidate provenance. No protected V2 final evaluation, preflight compute, training or Candidate promotion is opened.
- Fixture tests: `tests/v3/test_identity_artifact_verify_run500.py` (18 cases defined).

## CI / boundaries

- Defined tests for these four new modules: **57 parameterized pytest cases** by code enumeration; these are *not* claimed passed solely by being committed.
- A Run500 PR #8 CI on source/test head `160e564cec2e29d2b1a29cf919acb4f4fe6db3a1` failed only `ruff I001` (import sorting in the new wavefront test), six platforms. Semantics-preserving fix at `bbc57d3ec3473c67d5bc612c0e3266418e4bc849`; newer exact-head matrix evidence must be read separately.
- PR #5 source/test head `500704f8d30c5041de87335b4ac548cccbc35743` has a six-job matrix, whose exact final outcome must be checked separately.
- Independent local `git clone` / pytest is blocked by container DNS resolution of github.com. Existing GitHub Actions PR CI is the available verification path; no duplicate workflows were started.
- Frozen V1/V2/Local UI/Launcher/Memory/Agency/V3 contracts are untouched by these add-on files or scoped noncontract functions. Theoretical digests and fixtures do not prove external effects or permission.
