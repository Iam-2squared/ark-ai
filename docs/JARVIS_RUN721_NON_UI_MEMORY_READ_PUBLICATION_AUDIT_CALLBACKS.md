# ARK AI Run721 — Free-only non-UI custody and privacy hardening

**Scope:** isolated, reversible JARVIS foundations on Draft PR #8
(`research/jarvis-foundations`), no UI changes, no real execution or paid service.

## Exact saved change basis

- Initial basis: Run720 checkpoint HEAD
  `d4b311615e7c07dbb42d0a252581dcb7af97297b`.
- Final source/test work HEAD before this report:
  `3c57ac72cea22f79fae39f922d3310c593293667`.
- Work packages: four separate non-UI modules, four new synthetic test files,
  **25 authored parameter-expanded cases** (4 Memory, 3 Planner, 12 Audit,
  6 Personal Context).
- The commits and source/test changes are backed by ordinary GitHub Contents API
  writes, with a fresh branch HEAD read before each write.

## A — Memory event alignment digest callback custody

Source commit `015bdac8110270d285cb4683d5b968a33dc6d5c2`;
test commit `1b2e272d85ae78d8383a98f73ed7aec3ed0e8dc0`.

The read-only `sqlite_event_alignment` verifier pins the original local SHA-256
and JSON-dumps identities before opening private SQLite. Its existing result
authority check and row-phase source checks now re-evaluate these pins;
`_charge` also checks immediately before serialized event identities enter
JSON. Reentrant changes while hydrating a private row or charging an event
must refuse rather than forward data to a replaced callback.

Four synthetic tests cover preinstalled SHA and JSON replacement, replacement
during row decoding, and replacement immediately before event JSON charge.
The resulting local fingerprint **is not an authenticated history witness**;
mutable SQLite history and independently retained custody remain separate.

## B — Planner READ write-once manifest publication race

Source commit `522857ad47a14fdccd1cc719b426a8fff0110516`;
test commit `060bae903652b16b5b5d9a31dde14b0d5aee24b9`.

After file fsync and the existing POSIX parent-directory fsync, the writer
checks that the named manifest still designates the same exact regular
single-link file, including local device/inode, size and modification/change
epochs. A rename, unlink, or detected overwrite during this publication
window yields fail-closed UNKNOWN; the writer does **not** delete, overwrite
or automatically retry the artifact. Three synthetic tests cover removal by
rename, overwrite, and the unchanged successful deny-only path.

The check is **not** independent/authenticated custody, not guaranteed against
later replacement, and not cross-file atomicity. Windows still cannot claim
POSIX directory-fsync durability. A locally retained digest is not proof that
the backend READ happened or that its result is correct.

## C — Action Audit / ToolCall digest dependency pin

Source commit `268a32e96dbf21894a037e7e9b2a510ea257b3c7`;
test commit `3c57ac72cea22f79fae39f922d3310c593293667`.

The local audit guards original SHA-256, audit canonical JSON, ToolCall-side
canonical JSON and JSON freezer, plus JSON.dumps before reconstructing private
ToolCall arguments, decoding stored audit identity, or recomputing request ID.
The check repeats around a reentrant clock callback, before writing the
pre-action event and before hydrating read events.

Twelve parameter-expanded synthetic tests cover five dependency replacements
on both append and paged-read entry points, and SHA/JSON replacement during
the synthetic clock callback. No actual tool adapter is connected; no action
is authorized by these checks. Audit hashes and injected time are **not**
authenticated source provenance, trusted time, user approval or exactly-once
external side effects.

## D — Personal Context private fixture hash/JSON preaccess

Source commit `257ab2bcdd968eb8f8434f891682dae0af4b79fe`;
test commit `644664f2cea488af8edb96abfa1cf53f3882a672`.

The offline, deny-only local context fixture builder and its retained-review
entry point now reject replaced SHA-256, JSON encoding, and JSON decoding
callbacks before private synthetic content is read, hashed or serialized.
The existing immutable-carrier checks also recheck the original callbacks
between content and serialization phases. Six synthetic parameter-expanded
cases require the hostile callback never to execute on both build and verify.
The fixture output remains local-only; it does not prove consent, live Memory
authority, erasure or permission to export context or use real tools.

## Evidence status and cross-boundary audit

- Run720 checkpoint CI
  [#42516998663](https://github.com/Iam-2squared/ark-ai/actions/runs/42516998663):
  **6/6 GREEN** on older `d4b3116...` only.
- Run721 source/test runs started automatically by ordinary GitHub Contents API
  commits. At report revision, exact-head 6/6 GREEN is **NOT YET VERIFIED**.
  Tests are authored, not locally executed; do not promote older-head CI to
  a newer-head PASS. No duplicate Actions workflow was requested.
- CI diagnostics: [#42522000836](https://github.com/Iam-2squared/ark-ai/actions/runs/42522000836)
  Ubuntu 3.11 had **11,262 PASS / 1 FAIL / 1 SKIP**; the failing inherited
  coherent Memory test expected a later attacker-controlled SHA callback,
  but the new Memory alignment preaccess guard now refuses the retained
  witness **before** that callback. Other observed Ubuntu jobs failed the
  same single test (different Python/job totals). The test-only correction
  [`6b629df0`](https://github.com/Iam-2squared/ark-ai/commit/6b629df04b9a722b7f145ae72094b368e854703c)
  now requires the earlier `invalid retained witness` denial and zero
  execution of injected callbacks. No production safety check was relaxed.
- Read-only spot review of existing `docs/V3_FREE_GUARD_REVIEW.md` against
  protected Draft PR #5 (`805b377697472268db02650a89c7a94b1c5337c8`)
  found its older preflight cross-binding checklist is now covered by source
  checks for device, VRAM, tokenizer-probe, and wall budget. The protected
  branch was not changed; no claim about complete V3 readiness.
- Frozen V1/V2/Local UI/Launcher evidence, V3 Contract 1 and protected V2 final
  evaluation are unchanged. PR #5 remains protected Draft/unmerged, PR #9
  remains paused Draft/unmerged/untouched. This work does not imply ARK PASS.

## Next

1. Inspect exact-head six-job CI and correct real failures with the smallest
   semantics-preserving normal GitHub write, if any.
2. Memory: coherent retained evidence over foreign WAL appends, CAS/ABA and
   manual COMMIT-UNKNOWN triage without automatic uncertain-write replay.
3. Planner: detached input independent custody, crash/restart UNKNOWN handling,
   and stricter Windows publication limitations; no backend execution claims.
4. Exact-type ToolRegistry/PermissionGate, one-shot ledger, occurrence replay
   fencing and audit-before-action, then disconnected/mock-only integration
   after exact-head evidence.
5. Continue privacy-safe Personal Context, proactive state and observation
   back-end fixtures; retain all free-only and UI-pause gates.

**Hard boundaries:** no new payment, external GPU, cloud model, training,
Candidate/weights, credential, account connection, destructive action,
real tool dispatch, protected V2 evaluation, promotion, frozen-contract
change, or main merge.
