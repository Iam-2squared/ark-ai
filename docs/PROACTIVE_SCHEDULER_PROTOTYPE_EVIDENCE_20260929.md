# Proactive Scheduler Prototype Evidence — 2026-09-29

Status: local-only, reversible prototype evidence for Draft PR #8. No live source, external service, paid compute, real action backend, Candidate work, protected evaluation, promotion, or main merge was used.

Work basis: `be5b9c62f89eb85f8fd56fc9e33d48fe3e209f7f`.

## Prototype scope

A temporary SQLite prototype exercised the local proactive state contract without connecting any real observation or action backend.

The prototype bound trigger instance identity to:

- trigger definition ID and revision;
- owner and namespace;
- source ID;
- observation SHA-256;
- policy revision.

Prepared-item deduplication used one SQLite primary key per deterministic trigger instance and serialized writes with `BEGIN IMMEDIATE`.

Notification state persisted only content-free scheduling metadata: last observation digest, evaluation/notification timestamps, window counters, and revision state.

## Results

- deterministic trigger identity: PASS;
- observation or policy revision change -> different identity: PASS;
- owner change -> different identity: PASS;
- 16 concurrent prepare attempts for one trigger identity -> exactly 1 persisted winner: PASS;
- restart then re-prepare same trigger identity -> deduplicated: PASS;
- 20 concurrent notification evaluations for one unchanged observation -> exactly 1 `notify`, 19 `unchanged`: PASS;
- minimum evaluation interval boundary: PASS;
- cooldown boundary: PASS;
- rolling-window notification budget: PASS;
- window reset at exact boundary: PASS;
- invalid bool-as-revision input rejected: PASS;
- raw private payload bytes absent from the SQLite file when only its digest was persisted: PASS.

A separate boundary sequence produced:

`notify @0 -> too_soon @50 -> cooldown @100 -> notify @200 -> window_budget @400 -> notify @1000`

under a 100 ms minimum evaluation interval, 200 ms cooldown, maximum 2 notifications per 1000 ms window.

## Design findings

1. Persisting the last observation digest during cooldown is desirable: once the cooldown expires, the exact unchanged observation remains suppressible instead of surfacing late.
2. Concurrency safety must be enforced by the local store transaction, not by in-memory scheduler objects.
3. Prepared-work deduplication and notification-rate state should remain distinct. A trigger can be safely deduplicated while notification policy independently decides whether anything is surfaced.
4. Scheduler state creates no action authority. Any later write-effect action still requires ToolRegistry resolution, exact capability scope, durable one-shot authorization, pre-action audit, and replay-safe execution occurrence state.

## Next implementation step

After the current Planner/Memory/ToolRegistry/action-safety prerequisites land, implement the scheduler store with strict schema validation, exact integer storage checks, trusted-clock rollback protection, CAS revisions, and restart tests before exposing proposal-only proactive behavior.
