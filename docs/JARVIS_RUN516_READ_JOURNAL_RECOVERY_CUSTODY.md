# Run516 — disconnected READ journal and recovery custody

Status: **DRAFT / synthetic-only / no external dispatch / NOT_PASSED**.

## Exact source and test basis

- Run start: PR #8 `research/jarvis-foundations` work-basis HEAD `5875bd00baa17f9d5b22f45f145ba5f0f70083c4`.
- READ SQLite journal source: `src/ark/agency/disconnected_read_journal.py`, commit `ad2640dacfd6bcd3e3d8f9333ea641cee998a398`, blob `f636491798e4bfd42aadd90da63cbde384afb18d`.
- READ journal tests: `tests/test_disconnected_read_journal_authority_cleanup_run516.py`, commit `72d35379a362d85c1d44206875912d50d033c162`; **11 authored pytest cases** including parameter expansions.
- READ recovery source: `src/ark/agency/disconnected_read_recovery_schedule.py`, commit `16a18a1fdb6f967fc6971ec655aea383aadbdb9a`, blob `e60484564e408937918af8e6ce8f7ec5a98225a8`.
- READ recovery tests: `tests/test_read_recovery_late_denial_run516.py`, commit `9ac12cf09c68dac9d6c1f5210cccf50d461494fb`; **5 authored pytest cases**, including parameter expansions.
- Exact combined source/test HEAD: `9ac12cf09c68dac9d6c1f5210cccf50d461494fb`. Do not treat subsequent documentation or status commits as independent local tests.

## Journal invariants and negative fixtures

The locally retained `ReadJournalWitness` can compare an independently retained tip/count to an existing SQLite history; it **cannot** authenticate that a backend executed, reveal real source provenance, grant permission, or authorize replay. The journal now checks all four non-authority flags for exact `False` on ingress and during each retained-carrier callback boundary. A false-valued getter that flips to `True` while a hash is computed causes a pre-commit rejection, preserving transaction rollback.

`DisconnectedReadJournal.open` now explicitly closes an acquired SQLite handle when marker, schema, or continuity validation rejects, including the ordinary custom rejection path. The fixture checks a foreign marker and synthetic SQLite failure without touching any user database or generating an external side effect.

These measures are not substitutes for OS-level file-handle custody, authenticated time, consent, a secure evidence store, or cross-process witness authenticity.

## Recovery invariants and negative fixtures

`schedule_detached_read_recovery` now verifies the returned result and its previously constructed decisions a second time after the full set of denied-authority getters. A nominally `False` final getter cannot silently rewrite the prior result fingerprint, a nested disposition, the original source row, or an earlier `dispatch_authorized` descriptor. `READY_MOCK_ONLY` remains an inert classification, not actual READ authorization or a replay grant.

A `RUNNING` or `UNKNOWN` outcome does not become a trustworthy completed external action; unknown WRITE paths remain outside this module entirely. No ToolBackend, clock, process, network, human-review or notification operation is invoked.

## CI tracking (HEAD-specific, not inherited)

- Earlier Run515 PR #8 source [41253895460](https://github.com/Iam-2squared/ark-ai/actions/runs/41253895460): **6/6 GREEN**, predecessor only.
- Journal intermediate HEAD `72d35379a362d85c1d44206875912d50d033c162`: [41258385232](https://github.com/Iam-2squared/ark-ai/actions/runs/41258385232), Ubuntu 3/3 GREEN and Windows 3 in progress when last inspected.
- Combined source/test HEAD `9ac12cf09c68dac9d6c1f5210cccf50d461494fb`: [41258581825](https://github.com/Iam-2squared/ark-ai/actions/runs/41258581825), Ubuntu 3/3 GREEN and Windows 3 in progress when last inspected. **Do not claim final 6/6 GREEN until all six jobs actually finish successfully.**
- Independent local pytest/Ruff and physical-PC validation: **not performed**. New case count is authored tests, not local PASS count.

## Boundaries and follow-on

Only GitHub's ordinary Contents API was used, after checking the branch HEAD before each write. Frozen V1/V2/Local UI/Launcher contracts and evidence remain unchanged; PR #8 remains Draft/unmerged. No billable service, external GPU, real model/Candidate, protected V2 evaluation, external action, unknown WRITE automatic replay, irreversible operation or main merge.

**Next plan:** finish exact-head CI; integrate READ receipt and recovery against a separately retained source-identity witness with lower-level GREEN evidence; continue Memory CAS/coherent review, manual-only unknown WRITE recovery, trusted-clock audit-before-action and scheduler replay fences as isolated workstreams. Never infer external success or authority from a local digest.
