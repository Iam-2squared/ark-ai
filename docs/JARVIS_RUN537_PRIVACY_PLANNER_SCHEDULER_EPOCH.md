# Run537 — Personal Context, Planner READ, Scheduler restart verification

**Basis:** Draft PR #8 `research/jarvis-foundations`, initial HEAD `549bb1f2d495731c709df85a166d6ed55a0bfcdc`. All packages remain free-only, disconnected and reversible. They do not dispatch a ToolBackend, schedule an actual notification, delete any Memory, authenticate consent/time, replay UNKNOWN WRITE, launch a GPU or move a protected evaluation gate. Main and frozen Memory/Planner contracts are unchanged.

## 1. Privacy retention recheck — post-denial custody

`src/ark/personal_context_retention_recheck_review.py` was strengthened at `5785fa0df34c74cc8f83f1810b84c3e7181fee03`. Each denial-only result getter is a reentrant Python callback; after *each*, independently retained cached input/source epoch, current inventory carriers, returned data-only fields and original permission descriptors are rechecked. It refuses a misleading local privacy report if the last False getter rewrites an already inspected source, output, item, path or earlier descriptor.

`tests/test_retention_recheck_postdenial_epoch_run537.py` at `75d5c4731946e022da91d912289784b200179de9` adds **10 authored cases** (nine parametrized mutations and an ordinary denial-only control). The initial Linux CI found **nine legitimate-path test failures**: the newly added test compared separately reconstructed equal-valued scope-digest strings by *object identity*, which is not guaranteed. The narrow fix at `69db7151a9da99cfdf4565b8772277e344b2c2f3` compares that cross-inventory digest by value while preserving independently pinned cached and current inventory checks. A corrected exact-head CI result remains required before declaring this package GREEN.

No physical deletion, consent validity, backup/WAL erasure or legal basis is proven.

## 2. Planner registered READ / persisted mock DAG join

`src/ark/agency/disconnected_registered_archive_bridge.py` at `acc9b892c3bc1d5f17ab37ab2085ca0b845e5a89` pins nested plan-step and registered READ evidence carriers. A later verifier callback can no longer silently replace a nested step operation, argument string, request object or grant tuple while leaving only the outer plan/evidence tuples unchanged.

`tests/test_registered_cycle_archive_bridge_run535.py` at `09a2177b4f25a18f060fddc23c6962160f169d02` adds **4 authored negative cases** targeting mutation after the second registered READ review. This diagnostic still joins independent SQLite/file observations, *not* a global atomic snapshot or live READ/WRITE authorization, and does not authenticate actual outcomes.

## 3. Scheduler independent recurrence check

`src/ark/offline_schedule_resume_review.py` at `40fc5cc0473f38dbab79e4e0bf4ec3d96d50f1af` now verifies exact preview carrier types and independently derives the expected next occurrence, due time and classification from the pinned policy, cursor and caller-supplied timestamp. An exact-class, falsely denied-only preview callback cannot mislabel a due occurrence as NOT_DUE or exploit Python `True == 1` to impersonate the next index.

`tests/test_offline_schedule_resume_run534.py` at `7e580a37afd22c629e7b1531425e10618eec2832` adds **6 authored cases** (five forged previews and a normal unverified-due control). This is still a *synthetic* caller clock, not trusted time. No cursor mutation, timer activation, notification or automatic replay.

## CI evidence and limitations

The prior Observation-only exact HEAD `549bb1f2d495731c709df85a166d6ed55a0bfcdc` [41339614370](https://github.com/Iam-2squared/ark-ai/actions/runs/41339614370) was **6/6 GREEN**, not proof of these new packages.

Initial new-privacy CI [41340366153](https://github.com/Iam-2squared/ark-ai/actions/runs/41340366153) and [41340418517](https://github.com/Iam-2squared/ark-ai/actions/runs/41340418517) exposed cross-inventory string object-identity errors. The smallest fix at `69db7151a9da99cfdf4565b8772277e344b2c2f3` retains the new denial gates; its [CI 41341023536](https://github.com/Iam-2squared/ark-ai/actions/runs/41341023536) was **QUEUED** at the last observation. Historical failures remain FAIL. No local standalone pytest/Ruff PASS is claimed. In-flight and subsequent doc/checkpoint commits require their **own** exact-head results.

## Next / authorization boundary

1. Confirm CI on the corrected latest PR #8 HEAD and apply only semantics-preserving fixes when required.
2. Review post-callback source identity and cross-store clock/provenance consistency without granting real execution or silently widening retention.
3. Preserve all frozen V1/V2/Local UI/Launcher and V3 Contract evidence, keep PR #5/#8 Draft, and do not merge main without required approval.
4. Leave paid/possibly billable services, external GPU, Candidate generation, protected V2 evaluation, new credentials, actual notifications, private erasure, live ToolBackend and irreversible actions blocked pending explicit authorization.


## 4. Personal Context request binding — permission descriptor custody

`src/ark/personal_context_request_binding.py` at `3efc7e234ace7a6ace23244cf56ac8318d7f2a8c` pins exact preview and returned-binding permission descriptors before the first authority callback. Every late False getter is bracketed by original carrier checks, including the previously validated denied descriptors. An earlier permission getter cannot be rebound by the last getter to create misleading affirmative authorization, even if the replacement also returns False.

`tests/test_context_binding_permission_descriptors_run537.py` at `2b184f4d3e6328d50fa9c2bfa3deabb89180c530` adds **8 authored cases**: four late binding-descriptor rebindings, two preview-descriptor rebindings, an equal-value result digest carrier replacement and a deterministic, content-minimized deny-only control. GitHub CI [41341497716](https://github.com/Iam-2squared/ark-ai/actions/runs/41341497716) was **QUEUED** at last observation; no source/test GREEN is claimed before exact-head validation.

This request-scoped local JSON binding does not consult a live revocation ledger or legal/consent authority, and the added guards do not make a context fixture eligible for actual external disclosure, retention or Tool execution. The package is independent of the in-flight SQLite retention, Planner and Scheduler validations.
