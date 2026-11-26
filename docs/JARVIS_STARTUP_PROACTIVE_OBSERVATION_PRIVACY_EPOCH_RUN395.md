# JARVIS detached local state review: startup, proactive, observation and privacy epochs — Run395

Status: **engineering/threat-model evidence only**, in the disconnected research
branch `research/jarvis-foundations`, Draft PR #8. No live dispatch, user
authorization, real media capture, model training, real Candidate, notification,
external API or paid compute is added. Earlier frozen V1/V2/Local UI/Launcher
contracts/evidence, Memory v1 SQL DDL and V3 Draft PR #5 remain outside scope.

## Basis and four independent packages

The read-only work basis was GitHub branch HEAD
`6263386e53c858d4b8c946926eedbc614e90adeb` after the prior Run394
work (GitHub CI #761, run 40105731420, GREEN 6/6 on that exact HEAD).
Subsequent Run395 writes use ordinary GitHub Contents API, each preceded by a
fresh branch HEAD read; no Git ref manipulation or bypass.

| Package | Source and focused regression fixture | Failure mode rejected |
| --- | --- | --- |
| Startup readiness | `startup_readiness_lease_review.py`; `test_startup_snapshot_carrier_epoch_run395.py` | A reentrant integrity callback replaces a component tuple or one nested result with equal values, changes a READY state after validation, or temporarily swaps a required component. The exact original tuple, nested carriers and original value epoch are rechecked at phase boundaries. |
| Synthetic proactive preparation | `proactive_synthetic_review.py`; `test_proactive_retained_preflight_epoch_run395.py` | An independently retained witness `assert_integrity()` callback changes the original policy, same-string SQLite Path carrier, or the prior valid history witness before the input baseline is established. Policy and Path are pinned **before** witness validation; witness values are pinned before its own callback. |
| Observation window | `observation_window_review.py`; `test_observation_window_carrier_epoch_run395.py` | The observation tuple is replaced with a value-equal tuple containing the exact original envelopes. Original tuple identity is retained from the beginning of hydration through later consistency/freshness/witness checks. Changed envelope members keep the historical “identity changed” denial diagnostic; same-member tuple substitution is reported as tuple drift. |
| Privacy retention | `personal_context_retention_review.py`; `test_retention_inventory_item_epoch_run395.py` | An earlier `SyntheticRetentionItem` has its memory ID, revision or expiry classification reflectively edited during subsequent Memory row hydration or later revocation review. The generated output items must match their independently retained per-item epoch before return. |

These checks are fail-closed **diagnostics**, not execution features.
They deliberately do not infer consent from local hashes, a READY probe, a
retained veto row, a prepared trigger, or an observation identifier.

## Actual validation and diagnostic compatibility

Ruff and Python 3.11/3.12/3.13 on Ubuntu and Windows are checked by the
existing repository PR CI matrix, not by a new manually dispatched workflow.
The initial startup carrier-only HEAD `870abcf9d9b85c5a50845d0cf4d1573b1232b9e0`
passed CI #762. Following startup and observation heads initially failed
**existing regression message expectations**, despite denying unsafe input:

* Existing `test_startup_requirement_pin_run384` expected the original
  **blocked dependency** rejection, whereas a new earlier phase check emitted
  “readiness inputs changed”. The fix evaluates the originally pinned
  dependency first; a READY substituted requirement is still rejected before
  the next integrity callback can restore it.
* Existing `test_observation_window_review_run361` expected
  “observation identity changed” for an entirely new member object. The fix
  retains that existing diagnostic while separately rejecting a value-equal
  tuple holding the same original member objects.

CI failures at their own commit SHAs are real and are **not** relabeled as
GREEN. Final source/test HEAD CI must be read independently after these fixes
and the privacy package; earlier GREEN does not imply final GREEN. The latest
canonical `docs/PROJECT_STATUS.md` checkpoint records observed run IDs and
final statuses; no status is fabricated here.

## Invariants, adversarial scope, and limits

* Startup evaluates **the originally requested dependency identities**, not a
  callback-selected replacement. A required BLOCKED component cannot be
  made READY by a different unrelated READY component. Callback-induced
  values cannot silently rebaseline a local snapshot.
* Scheduler preparation remains an inert, deduplicated SQLite fixture. A
  retained witness is a caller-custodied digest of local history, **not** an
  authenticated user instruction; a successful “prepared” marker never
  authorizes a notification, tool or irreversible action.
* Observation windows contain metadata and SHA-256 content IDs, not media
  bytes. Same-content hashes are not authenticated physical source identity.
  No camera, microphone or screen capture integration is performed.
* Retention inventory exposes only IDs, revisions and expiry categories. It
  does not delete data, provide proof of backup erasure, issue consent,
  expose Memory text/metadata, or authorize a Personal Context disclosure.
* Python `frozen=True` and identity checks detect particular **observed**
  in-process reflective mutations; they do **not** protect against privileged
  Python code, an attacker rewriting both prior witnesses and bytes, OS-level
  file replacement, rollback between unobserved callback boundaries,
  trusted-clock forgery, concurrent cross-SQLite transactions, or a restored
  ABA after the last review.
* UNKNOWN WRITE stays UNKNOWN; audit records and mock success are not proof
  of an external effect. The workflow never performs a real ToolBackend
  dispatch, replays an uncertain operation, or promotes a Candidate.

## Unresolved integration gates

Live operation still requires independently authenticated human issuer and
scope-bound authorization; trusted clock and replay/occurrence defense; OS-level
storage, content and identity custody; durable external idempotency receipts;
cross-store reconciliation; and explicit main/frozen-evaluation approvals.
Do not turn a synthetic reviewer or its regression count into a JARVIS PASS.

**Next:** verify the exact final source/test/document/checkpoint commits and all
six CI jobs, then develop cross-store restart-safe Planner/Claim/Occurrence/
ActionAudit reconciliation fixtures and Memory/CAS/privacy lifecycle in
separate FREE-only lanes. Continue independent synthetic Observation, Startup,
Scheduler and V3 authorization/path/identity audits while any CI is running.
