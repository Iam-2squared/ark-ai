# Run582 — Non-UI audit tail and Personal Context retained-prefix review

## Work basis and scope

- Branch: `research/jarvis-foundations` / Draft PR #8; initial verified HEAD `5590b837a3664c03bf2d9b856392d87415820837`.
- Previous exact HEAD CI: [#41639618730](https://github.com/Iam-2squared/ark-ai/actions/runs/41639618730), **6/6 GREEN** on that prior HEAD only. New work must earn its own verdict.
- UI PR #9 remains untouched Draft/unmerged; no frontend changes, real backend dispatch, paid services, GPU, physical-PC activity, protected evaluation, Candidate generation, or main merge.

## Package A: Action Audit fail-closed persisted-tail identity

- Source `src/ark/agency/audit.py`: normal Contents API commit `f549bcc49ae66061b20c172f0e0a9b7977fda33f`.
- New tests `tests/test_action_audit_tail_identity_run582.py`: commit `0b43d93a70b6ac72526f2e4856aa61279ad06e97` — **7 authored cases**, not independently executed local pytest passes.
- The same writer transaction now validates the immediately preceding audit row's exact types, nonempty text, lowercase digest syntax and request-ID recomputation *before* inserting any later event. A valid clock alone cannot cause new evidence to be appended after a malformed tail.
- CI [#41647522919](https://github.com/Iam-2squared/ark-ai/actions/runs/41647522919) exposed **one existing regression expectation mismatch** on Ubuntu 3.11: malformed tail clock rejected under a newer message rather than the earlier `clock regressed` text; 7,561 tests passed, 1 skipped, 1 failed. Source commit `b1595014cd3b39976e7b138b55b7c2c08ba3075d` restored the diagnostic without weakening denial. Latest fix CI [#41648286884](https://github.com/Iam-2squared/ark-ai/actions/runs/41648286884) initially IN PROGRESS.
- Only the last row is checked during append. This is **not** a cryptographically authenticated history, full historical scan, trustworthy writer identity, clock attestation or proof that a backend executed.

## Package B: restart-local Personal Context replay-prefix custody

- Source `src/ark/personal_context_replay_ledger.py`: commit `f7953338bb209f0090d6a5cc997a4e4c45ec9dae`.
- New tests `tests/test_personal_context_replay_prefix_run582.py`: commit `b084da8471d32f9f011fa4e067c6d20e4ffa8b0f` — **6 authored cases**.
- New `verify_retained_prefix(retained)` is a **read-only** review: inspect complete SQLite v1 hash-linked history in one read transaction; verify the exact previously retained chain tip at its original sequence even if valid later entries exist. Reject truncated/rebased history, malformed retained witnesses, changed reference/path carriers. No new schema, receipt insertion, plaintext export, live tool, authorization or retention extension.
- The prior witness **must be retained separately** to help detect history replacement; a ledger-created hash is not independent custody, authenticated consent, revocation freshness, trusted time, or real-world exactly-once.
- Source [CI #41647831330](https://github.com/Iam-2squared/ark-ai/actions/runs/41647831330) and tests [#41647945431](https://github.com/Iam-2squared/ark-ai/actions/runs/41647945431) had not received an exact-head six-job GREEN verdict at note preparation.


## Package C: registry-bound PermissionGate instance-authority pin

- Source `src/ark/agency/policy.py`, commit `5d889665cc6c2d311a9d798a939cbc58671cefaf` adds `inspect.getattr_static(self, "authorize")` identity validation against the original `PermissionGate.authorize` implementation before and during registry-bound policy decisions.
- Tests `tests/test_permission_instance_shadow_run582.py`, commit `9ae52e46dced9eb7663b2a11d96719bc0a7398e3` add **5 authored cases** for shadowed READ/WRITE, already-consumed token replay laundering, mutation during grant iteration, and restored original policy. The prior logic checked only the class implementation and a token's presence in the consumed set; an instance-level no-op shadow could reuse that already-consumed token as supposed proof of a new spend.
- The fix prevents the diagnostic from treating a previously spent process-local token as a newly spent one when an instance-level method is monkeypatched. No real external execution or durable authorization is created; process-local consumed tokens are **not** restart-safe approval.
- Source [CI #41649101572](https://github.com/Iam-2squared/ark-ai/actions/runs/41649101572) and tests [CI #41649190513](https://github.com/Iam-2squared/ark-ai/actions/runs/41649190513) were not yet verified all-six GREEN when prepared.

## Frozen and next

- Independently fetched unchanged blobs: Memory `src/ark/memory/contracts.py` `b6e93821ecd69270a7634aceb20775dc36e9953c`; Agency `src/ark/agency/contracts.py` `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`; V3 `docs/v3/CONTRACT.md` `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`.
- Next: finish latest exact-head CI; fix only grounded failures; keep both stores fail-closed; review registry-bound authorization and independent durable occurrence witnesses in another isolated non-UI lane. Do not equate a local diagnostic receipt or a synthetic hash with permission to execute, disclose, retry, spend money, merge, or declare PASS.
