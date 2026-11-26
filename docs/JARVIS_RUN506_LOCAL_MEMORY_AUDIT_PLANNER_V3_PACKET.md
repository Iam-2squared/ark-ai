# ARK AI Run506 — local integrity work packages (free-only)

Saved evidence at **2026-10-31T23:53:11.050+09:00 Asia/Tokyo/JST** (ordinary execution wall clock; not independently attested).

## Exact source/test commits and scope

Initial PR #8 work-basis HEAD `97773b557c68c1e24bb001b876fc876c046255f8`; last source/test HEAD `854ef4c607acdd50074dcbca72bc58ce3627b73f`. PR #5 initial `fec9146b932c192a645e3790cb746aa542cc5171`; last source/test HEAD `1af2d32cd5103f4cad0fcd903fc7f12251bb5f86`. Both PRs remain **Draft/unmerged**; main `7a843f17eb96ed13d66f23b58b06406b3002e405` is unchanged.

1. **Memory v1 persisted-row budget verification** — `src/ark/memory/sqlite_store.py` blob `0fd10db21f6afc4760eeef1f6929641bbc3a5d29`, source commit `d74738ed84967c5964f86707e8db71cf09c7d62b`; `tests/test_memory_persisted_write_bounds_run506.py` blob `e504ffcb8d0b0f1c2e7854845b23ad95df0a94e5`, commit `6d37c13ebf298fb8b721b84e2e44559a2053c61f`. Hydration now denies hash-consistent but out-of-bounds source/content/metadata rows (including 65 keys, blank/oversized keys, >4096 values, oversized/blank content). Existing frozen v1 DDL and public constructors are unchanged. **8 newly authored cases**.
2. **Action Audit canonical request-ID/row consistency** — `src/ark/agency/audit.py` blob `7b2691fdd963e91deb39b629be98492a69821681`, source commit `8799083694fb27bdd227fbeeb777944bf123966c`; `tests/test_action_audit_request_binding_run506.py` blob `37cc14dca629ef4eca5299cb2d8f9a0588e3568e`, commit `a464260026a2e8146c6d45b52ec3b9b33f470caf`. Read-only events now recompute `act_` ID from independently persisted tool/capability/scope/argument digest using the existing frozen canonical encoder; valid-form but inconsistent row edits are rejected. **6 newly authored cases**.
3. **Planner exact scalar carrier epochs** — `src/ark/agency/planner.py` blob `21831ff220e771274371708f9d1f3ad2d907aa1f`, source commit `86d991239aa72002fcb8f7b33c5c05168e20a756`; `tests/test_planner_exact_scalar_carriers_run506.py` blob `de441404a4c199e3bb9d41640160565c89cb5218`, commit `854ef4c607acdd50074dcbca72bc58ce3627b73f`. The in-memory DAG now refuses reflectively replaced equal-valued step ID or ToolCall tool/capability/scope carriers, even when action digests remain equal. No backend dispatch. **5 newly authored cases**.
4. **V3 preflight review packet custody** — `src/ark/learning/authorization.py` blob `72becdcbf1b533d32c319a1ab4538d69e774c7e8`, source commit `acfc63040d28669f22819c53b248fb8be829614c`; `tests/v3/test_authorization_packet_epoch_run478.py` blob `00c98902414e24e6596042a44b863af7f7ecb1c8`, commit `1af2d32cd5103f4cad0fcd903fc7f12251bb5f86`. Pin the generated *review packet* JSON tree separately from the execution snapshot, reject post-serialization/hash-callback retargeting before adding its digest, and preserve the explicit NO-APPROVAL hard stops. **3 newly authored cases**.

Total **22 authored pytest cases across 4 packages**; counts are test definitions, not an independent local-run result.

## CI and limits at evidence-writing time

- PR #8 memory test head: [run 41211537530](https://github.com/Iam-2squared/ark-ai/actions/runs/41211537530) — 5/6 GREEN; Windows Python 3.12 IN PROGRESS.
- PR #8 audit test head: [run 41211615887](https://github.com/Iam-2squared/ark-ai/actions/runs/41211615887) — 3/6 GREEN; Windows jobs IN PROGRESS.
- PR #8 latest Planner test/source head: [run 41211789863](https://github.com/Iam-2squared/ark-ai/actions/runs/41211789863) — 3/6 GREEN; Windows jobs IN PROGRESS.
- PR #5 latest V3 source/test head: [run 41212041729](https://github.com/Iam-2squared/ark-ai/actions/runs/41212041729) — 4/6 GREEN; two Windows jobs IN PROGRESS.
- The previous Run505 exact heads [PR #8 run 41207705833](https://github.com/Iam-2squared/ark-ai/actions/runs/41207705833) and [checkpoint run 41208065165](https://github.com/Iam-2squared/ark-ai/actions/runs/41208065165) completed SUCCESS; neither is evidence for these new heads.
- Local Git checkout / independent pytest / Ruff: **NOT VERIFIED** (container DNS resolution for GitHub unavailable). Do not inherit older GREEN evidence.

## Interpretation, protected contracts and hard stops

SQLite data-row checks detect contradictory local bytes; a writer with control of all row fields and hash digests is **not** authenticated. Memory local deletion still does not certify secure erasure, historical append-prefix provenance or consent. Planner identity guards remain in-process and do not grant ToolRegistry/PermissionGate/WRITE authority or exactly-once external effects. A V3 packet digest is **not** a human signature, GPU authorization, price ceiling agreement or a valid Candidate.

Unchanged frozen blob identities observed: Memory `contracts.py` `b6e93821ecd69270a7634aceb20775dc36e9953c`; Agency `contracts.py` `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`; V3 `docs/v3/CONTRACT.md` `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`. V1/V2/Local UI/Launcher, protected evaluation, and main untouched by our writes.

**No paid/external GPU compute, paid API, model training or real Candidate/adapter/weights; no credential connection, real user Personal Context, OS device read, external Tool dispatch, automated UNKNOWN WRITE replay, V2 final evaluation opening, Candidate promotion, destructive action or main merge.** Only normal contents-API commits and ordinary public-repository CI were used.

## Next plan / 今後の方針

1. Confirm newest per-HEAD CI (all Windows/Ubuntu, 3.11–3.13), repair only evidenced failures without suppressing assertions.
2. Strengthen Memory event-row/canonical identity integrity, CAS/restart snapshot comparison and bounded expiry; audit untrusted SQLite writers and retained witness limitations.
3. Progress Planner persisted recovery of UNKNOWN WRITE (never auto-replay), registry-bound authorization/immutable ToolRegistry, exact-type PermissionGate, trusted-clock audit-before-action and Scheduler occurrence ledger.
4. Continue free-only V3 identity/packet/path/provenance validation, Personal Context consent/revocation and Observation fixture privacy; preserve all explicit gates.
