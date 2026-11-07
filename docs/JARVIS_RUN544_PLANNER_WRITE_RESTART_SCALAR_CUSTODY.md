# Run544 — Planner Durable WRITE Restart Scalar Custody

**Scope:** disconnected Planner quarantine/restart simulation using an existing synthetic SQLite WRITE reservation ledger. This is neither a dispatch path nor evidence of an external effect. Unknown/RUNNING WRITE claims remain quarantined.

**Source commit:** `e9401cc84a66222973d42fa9117f32a667957ed4` (`src/ark/agency/disconnected_write_restart_binding.py`).

**Test commit:** `8f1c2b96cfff978102043e58bc4c7d3e5175520f` (`tests/test_write_restart_scalar_custody_run544.py`), **7 authored pytest cases**: one stale retained tip, four separately forged SQLite-reinspection stages, one forged public `ledger.inspect` callback, and one legitimate quarantined restart under always-False witness equality. These are authored cases, **not local pytest PASS evidence**.

## Why the integration needed hardening

The existing restart reader correctly compared reservation membership and quarantined every synthetic WRITE, but five subsequent comparisons still used `WriteSlotLedgerWitness` dataclass object equality. Monkeypatching its class `__eq__` to return True could misrepresent an instrumented, forged inspection result as equal to the original independently retained tip. Monkeypatching it to False could reject an otherwise valid no-dispatch read.

A shared `matches_retained_tip` helper now requires the exact retained witness class, checks the existing denied capability property, and compares **primitive count and SHA-256 chain tip** directly to the pinned original. It is used at all five boundaries: first transaction inspection, in-transaction repeat inspection, public callback inspection, independent second SQLite snapshot, and final snapshot after all authority-denying report getters.

Any incorrect count or hash rejects without authorizing a WRITE; the lower-level disconnected slot ledger retains its separate exact-class/CAS/rollback guards. No frozen contract, public Memory v1 API, schema or permission policy was changed.

## Evidence and limitations

The lower-level WRITE scalar-CAS source/test commit `8862c09a5a4e5e139bf4758540cf72c8dd78cf38` is confirmed **6/6 GREEN** in existing GitHub Actions run [41373933860](https://github.com/Iam-2squared/ark-ai/actions/runs/41373933860), across Ubuntu and Windows Python 3.11–3.13. This is **not** the exact HEAD of this Planner change. The Planner source/test run [41374898998](https://github.com/Iam-2squared/ark-ai/actions/runs/41374898998) was still **IN PROGRESS** at note preparation; do not infer its result.

Hashes and caller-held witnesses do not authenticate actors, trusted time, file/WAL custody, completeness of cross-store Planner state, user consent, or once-only real-world effects. Real ToolBackend remains disconnected; explicit human approval is required before protected main merge or external action.
