# ARK JARVIS disconnected fixture and READ receipt custody — Run499

Recorded: 2026-10-31T08:51:06.555Z (runtime UTC; JST local sample 2026-10-31 17:51:06, not independent trusted-clock evidence).

## Scope and provenance

All changes were made by the ordinary GitHub Contents API, on two separate OPEN/DRAFT/UNMERGED research PR branches. No main merge, real Candidate generation, protected V2 evaluation, external GPU, paid API, live sensor capture or effectful ToolBackend dispatch took place.

### JARVIS draft PR #8 — source/test packages

1. **Observation fixture post-validation epoch:** after the original ObservationEnvelope validator returns, independently compare every field to the pre-hash expected tuple. This prevents a local digest or metadata callback from retargeting a frozen fixture envelope *after* its construction-time check. Source `f378c2852b03c72e4a6bb0ba1327400c9ce2a2b2`, tests `0b2297ef616e791fb95846b53b679ec058f83799`: 12 parameterized cases (10 late mutations across text/binary and two intact cases).
2. **PCM16 resampler output custody:** require the exact pinned result type and exact original source/output digests, rates, sample counts and PCM bytes after result factory construction. No ASR, microphone, consent, or speaker authentication is implied. Source `da10c548d2291b2c817dafad0608b892d40a80c9`, tests `d6998ab16aa0a960ee8ece148324be831034d534`: 9 cases.
3. **Transcript cue denial and result custody:** pin the full five-field result epoch, require exact result class and all four denial-only getter values, then recheck the source and result after the callbacks. A wake-text match cannot authorize an action or prove a speaker. Source `72900d1e718f296da6b25ffc3be4e917ad8a3c0b`, tests `7f460c8e4e3942bff8747ee170ce90493237af80`: 15 cases.
4. **Planner disconnected READ receipt final epoch:** a late getter on the verified synthetic binding could alter a previously checked receipt. Recheck bound request, result, binding and exact receipt *after* the final getter, prior to returning. Source `05a595b2644718d2478ab6991a04ced4249d1d5e`, tests/final JARVIS source HEAD `2c4436e647120b80467a92d33f88f26437236cb4`: 6 cases. This is an inert receipt only, not evidence of execution.

### V3 draft PR #5 — free-only identity output path

5. **Identity CLI path alias rejection:** create-only local artifact generation now rejects `..` path segments, overlong path text and symbolic parent directories before exclusive opening. Existing create-only semantics are unchanged. This remains a best-effort path preflight, not an atomic OS ancestry custody proof. Source `8f0556213c9514d4d62986809c29b09475ecdb12`, tests/final V3 source HEAD `6753e834c8b2cde4696490ffbd9182ed7895dd60`: 4 cases, with symlink tests skipped if the runner OS prohibits creating symlinks.

**New tests: 46 concrete parameterized cases over five new pytest modules.** They are fixtures and negative/adversarial checks, not production model evaluations. A successful CI on an *earlier* HEAD must not be treated as proof for either final-source HEAD.

## Preservation and remaining risks

- Frozen Memory/Agency contracts and V3 Contract/Contract.sha256 remain unchanged; their expected blobs were re-read in this session.
- No real speaker, capture permission, deletion, trusted time, OS attestation, source identity or end-to-end JARVIS acceptance is established by these local checks.
- Separate SQLite witnesses have no independently trusted cross-store atomicity or provenance; UNKNOWN WRITE still requires human reconciliation and must never replay automatically.
- A local path preflight cannot prevent an attacker with concurrent directory mutation privileges from changing ancestry after the check. A future open-handle-based, platform-specific custody design would need explicit review.
- V3 materialized model/tool bytes, actual approved data, reviewer decisions, pinned runtime/hardware and user-authorized billing remain blocked and must not be fabricated.

## Verification protocol and next dependency order

Check six Ubuntu/Windows × Python 3.11–3.13 jobs for **exact source/test** SHA `2c4436e647120b80467a92d33f88f26437236cb4` ([run #1840](https://github.com/Iam-2squared/ark-ai/actions/runs/41186150416)), and V3 SHA `6753e834c8b2cde4696490ffbd9182ed7895dd60` ([run #1842](https://github.com/Iam-2squared/ark-ai/actions/runs/41186212959)). At document preparation both were QUEUED. A read-only git clone for independent local pytest/Ruff was unavailable because this runtime could not resolve github.com; no local GREEN claim is made.

Next: (1) resolve exact-head CI failures if any without weakening tests, (2) Memory CAS/expiry with retained epochs, (3) Planner UNKNOWN WRITE and registry-bound identity, (4) Trusted Clock audit-before-action and restart-safe occurrence fences, (5) scoped Personal Context/Observation synthetic revocation and no-permission adapters, (6) V3 free-only approval/path/identity guards. Keep PR #5 Draft and all forbidden gates closed.
