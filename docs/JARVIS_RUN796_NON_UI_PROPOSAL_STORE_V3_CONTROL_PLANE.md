# ARK Run796 — Offline proposal CAS store and detached V3 protocol custody

**Scope:** Draft PR #8, `research/jarvis-foundations`, non-UI and free-only. Work-basis HEAD `8410494fc4d4c893d3b67db554b3367137414d29`. This is a reversible fixture, not a released JARVIS capability or approved learning run.

## Package A — durable synthetic proposal-only event store

- Source: `src/ark/agency/disconnected_proposal_store.py`, source commit `fb42a9d005399e768b0e8a35ffa5d9d824f37c16`, blob `3b9b0aa16052d5c5728c85620808873e9dc9e3a3`.
- Tests: `tests/test_disconnected_proposal_store_run796.py`, test commit `3bcb2a3cfda93ed651a2a7e87f383aae272d32d4`, blob `c082447bf816952ad865d280cfe7be57c4f5ed84`; **17 parametrized cases submitted**, not an all-platform certification until exact-head CI finishes.
- One SQLite fixture created with exclusive `O_CREAT|O_EXCL`; rejects an existing target rather than clobbering it. Refuses nonabsolute paths, symlink ancestors, symlink/nonregular target and hardlinked target. Confirms exact schema version/definition and SQLite quick integrity check on reads/writes. These checks **do not prove freedom from filesystem races, unsafe sidecars, arbitrary process mutation or backup retention**.
- Every event has an exact per-proposal lifecycle revision/state/SHA-256 chain verified through the existing detached replay contract, plus one global ordered sequence/hash binding every proposal. `BEGIN IMMEDIATE` serializes competing local appends, and both a **caller-retained global witness** and a **per-proposal exact tip/revision** are compared inside the same write transaction. Replayed/stale events are denied. One append is locally committed, never dispatched as an external effect.
- A read-only SQLite snapshot can compare a separately retained *prefix*. This detects divergence at the retained count, but **cannot detect an unwitnessed rollback or authenticate the source of the witness**. A caller who loses a post-COMMIT receipt must inspect/reconcile manually and must **not automatically reissue an ambiguous WRITE**.
- Only a hash-derived proposal ID, state/revision names and chain digests are stored; there are no raw prompts, human names, tool payloads or full improvement evidence. Even content-free hashes can be linkable personal information. No automatic erasure/export, real review, audit attestation or executable approval exists. All returned authority properties are strictly false.

## Package B — detached V3 metadata guard

- Source `src/ark/v3_detached_preflight_crossbind.py` updated at `712b3146dcb4a624c2054de7ffa45db75e144016`, blob `5d232e0ccdec23ee12d3aaffba00276310a17223`.
- Tests `tests/test_detached_v3_controlplane_run796.py` committed at `454f0ca683c944e914a1eb5fbc8c77f003ce80e4`, blob `f2959364a1fc90f5c90637b3ccc236addd78c9d7`; **9 cases submitted**.
- Import-time control-plane fields, hook tuples, descriptor mappings and math finiteness predicate are pinned, including in-place map modification. The existing device/VRAM/time/tokenizer validation and no-authority result behavior are preserved. No Draft PR #5 contract/evaluation/approval boundaries change.

## Verification record

- Prior exact baseline HEAD `8410494fc4d4c893d3b67db554b3367137414d29`: GitHub Actions [#43053263143](https://github.com/Iam-2squared/ark-ai/actions/runs/43053263143) **6/6 GREEN**, separately inspected (Ubuntu/Windows, Python 3.11, 3.12 and 3.13). This is Run795 evidence only.
- Source-only SQLite package [#43062024586](https://github.com/Iam-2squared/ark-ai/actions/runs/43062024586): Ubuntu 3/3 GREEN and Windows 3 jobs IN PROGRESS at inspection.
- Source+tests SQLite package [#43062209306](https://github.com/Iam-2squared/ark-ai/actions/runs/43062209306): IN PROGRESS at inspection.
- V3 source [#43062487537](https://github.com/Iam-2squared/ark-ai/actions/runs/43062487537): IN PROGRESS at inspection.
- Latest V3 test HEAD [#43062573335](https://github.com/Iam-2squared/ark-ai/actions/runs/43062573335): IN PROGRESS at inspection.
- A disposable local Python 3 harness with a *temporary stand-in* for the detached lifecycle contract exercised 17 SQLite store tests successfully. The actual repository lifecycle was **not** loaded in that local run; only GitHub CI can certify the integrated code on this branch. GitHub blob SHA values for the store source and tests were checked against local `git hash-object`; they match. No physical PC/model/GPU testing or human review is claimed.

## Boundaries and next checks

The new store is reversible, isolated, **not encrypted**, and **not a trust anchor**: trusted time, authenticated reviewer identity/consent, credible independently preserved witness, privacy lifecycle policy, backups, process-level isolation and reliable post-commit handoff remain unsolved. It is **not** authorization to edit source, grant tools, generate Candidates, open V2 final evaluation or spend money.

Keep PR #5 Draft/unmerged and its frozen Contract 1, all V1/V2/Local UI/Launcher evidence untouched; keep PR #9 Draft/unmerged and PAUSED. No paid compute/API, external GPU, credentials, live backend, automatic UNKNOWN WRITE retry, destructive operation, protected evaluation, promotion, or main merge.

**Next:** exact-head six-job CI resolution and minimal real-log fixes if needed; strengthen store sidecar/path lifecycle and externally retained witness handoff without inventing authentication; continue Memory CAS/ABA/COMMIT-UNKNOWN, Planner durable recovery, and registry-bound audit-before-action mock-only integration. Overall JARVIS **NOT_PASSED**.
