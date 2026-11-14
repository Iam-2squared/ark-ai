# ARK JARVIS Run613 — non-UI detached WRITE, Memory prefix and attention custody

**Status:** implementation and offline regression *definitions* saved on Draft PR #8; **NOT an external permission, production integration or final PASS**. No UI/frontend, main merge, frozen contract, real action, paid compute, credentials, protected evaluation or Candidate work.

## Work basis and packages

- Invocation work-basis: `397698fc3c2572f9badb85d59f79c1e47b57e079` (Run612 status checkpoint). At invocation start, the six CI jobs of [run 41891543751](https://github.com/Iam-2squared/ark-ai/actions/runs/41891543751) were independently checked as **GREEN 6/6** for this exact SHA.
- **Package A — disconnected WRITE manual triage:** source `aadf3a602a4f30dea835d1efb71f1955c0f22d06`; test `05c63f56002e68c0c9ae82487ea83cbf3d7e2fb9`. Imported packet/restart/fence classes and their original False-only denial descriptors are pinned. The packet builder rejects changed class identities/properties before inspecting derived authority fields, including false-returning executable getters installed during packet construction. Existing pre/post input epoch checks and the no-dispatch/no-replay semantics remain intact. **20 authored parameter-expanded cases**: 14 pregetter denial variants, 4 packet constructor injection variants, 2 normal READ/WRITE cases. No physical WRITE execution.
- **Package B — Memory v1 event prefix:** source `ee106c940fc239a6d00d855f29dda3a76d8e8efd`; test `abcd78336b687dbcc8714f9dbd37ff8d75436729`. V1 event IDs are required to be dense from genesis; a retained witness with `last_event_id != event_count` is structurally impossible for the existing append-only schema. Reject such external witnesses **before** a SQLite scan, including apparently well-formed SHA fields. **7 authored cases**: 6 invalid count/tail pairs with forbidden-I/O assertion plus valid genesis/append comparisons. This does not authenticate witness custody or guard against coordinated database and sequence replacement.
- **Package C — proactive attention input identity:** source `d6517463d70e7ad9b5a4658d5d2ae70ea94346b2`; test `f7f505bb0749d5ec50e141764f8d6a73e6b103c0`. Inert policy and historical marker class bindings must remain the original imported classes before any untrusted field getter is read; imported result denial guard remains unchanged. **12 authored cases**: 2 counterfeit input type captures, 4 rolling-window/cooldown edges, 2 suppression/occurrence cases, 2 incoherent history, 1 64-bit clock overflow, 1 empty-history deny-only control. No notification, consent or real trusted clock.

**Total:** 39 *authored* pytest parameter-expanded cases, **not a claim of local pytest PASS**. No local clone was available through DNS. GitHub Actions is the intended execution evidence and will be reported by exact commit SHA and six-job result; a GREEN on an earlier SHA is not final-HEAD certification. No duplicate workflow reruns requested.

## Control and safety boundaries

These are strictly local diagnostic, no-side-effect contracts. An original class pointer/denial getter identity is in-process integrity, **not** signed provenance or robust hostile-process isolation. SQLite event density and hashes remain vulnerable to a coherent rewrite without externally protected witness storage. A detached reserved WRITE or manually triaged UNKNOWN effect stays quarantined. A proactive `REVIEW_ONLY` output never constitutes a notification permission or consent.

Do not merge any Draft PR automatically. Leave PR #5 V3 approval gates and frozen V1/V2/Local UI/Launcher evidence alone; leave PR #9 UI paused. Any real external effect, paid service, protected evaluation opening, Candidate promotion or frozen-contract change requires separate explicit authorization.

## Next plan / 今後の方針

1. Confirm the **latest exact-HEAD** Ubuntu/Windows × Python 3.11–3.13 CI, inspect actual logs and repair only concrete failures using normal GitHub Contents safety path.
2. Implement and test independent Memory COMMIT-UNKNOWN manual reconciliation and coherent row/event evidence without retry authority.
3. Advance Planner crash recovery and registry-bound permission/audit-before-*mock*-action interoperability only after lower-level exact-head GREEN.
4. Continue privacy-aware Personal Context, proactive scheduler and offline observation fixture contracts, plus V3 free-only provenance/identity guards. UI stays PAUSED and all PRs Draft/unmerged.
