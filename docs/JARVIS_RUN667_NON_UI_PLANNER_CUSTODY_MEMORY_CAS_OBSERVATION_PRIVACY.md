# ARK AI — Run667: non-UI Planner custody, Memory CAS, observation and revocation

Scope: existing **free-only / disconnected** foundations on `research/jarvis-foundations` / [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8). This is an incremental engineering note, not JARVIS completion evidence, consent, independent custody, trusted time, or authorization to dispatch.

## Work basis and inherited validation

- Initial, independently read work-basis HEAD: `ec9f70a8a2f4de414767cb39678869a9b33cebe0`. Inherited exact-HEAD [Actions #42266035684](https://github.com/Iam-2squared/ark-ai/actions/runs/42266035684) was re-verified as **6/6 GREEN** (Ubuntu/Windows × Python 3.11–3.13); all six jobs individually finished successfully. This does **not** validate the new commits below.
- The branch PR #8 was initially OPEN, **Draft / unmerged**. Main remained `7a843f17eb96ed13d66f23b58b06406b3002e405`; PR #5 and UI PR #9 were OPEN, Draft and unmerged. UI development remains fully paused.

## NEW packages — five independent, narrow changes

1. **Planner nested input epoch production hardening** at `8ceca52a85142d2a81c4a17e2840aa2d26298d9d`:
   `src/ark/agency/disconnected_planner_fence_projection.py` now pins import-original caller `ToolCall` nested tool/capability/scope/arguments **carrier identities** and canonical request ID, in addition to the `PlanStep.call` object and topology digest. Recheck across hash and fence callbacks so a frozen-but-reflectively-mutated in-place `ToolCall`, including a *value-equal new arguments mapping*, cannot be silently adopted after topology hashing. No new effect/dispatch API and no successful-step receipt is invented. Source-only [CI #42273594778](https://github.com/Iam-2squared/ark-ai/actions/runs/42273594778) sampled Ubuntu 3/3 GREEN, Windows **IN PROGRESS**.
2. **Memory two-handle generation CAS races** at `a30f46f313a65ec48307e8f3e1cb8e36bf952457`:
   `tests/test_memory_two_handle_stale_token_run667.py` adds **3 authored tests**: both identical and divergent duplicate attempts using the same stale lifetime token, and an old token refused after a second writer commits a newer generation. The single winner is preserved; ambiguous matching content stays **manual-only**, with no caller authentication, auto-retry, WRITE or trusted-clock authority. [CI #42273769622](https://github.com/Iam-2squared/ark-ai/actions/runs/42273769622) was sampled Ubuntu 3/3 GREEN / Windows **IN PROGRESS**.
3. **Mixed Observation provenance/lineage** at `472ec970da31105795e88e0c5c04b04d32b2463f`:
   `tests/test_observation_mixed_fixture_chain_run667.py` adds **6 authored tests**: a valid four-kind TEXT→TRANSCRIPT→IMAGE→SCREEN closed digest chain, source and privacy-scope isolation (2), repeated payload digest ambiguity, and past/equal-time rejection (2). No camera/microphone/display acquisition or disclosure. [CI #42273894573](https://github.com/Iam-2squared/ark-ai/actions/runs/42273894573) was **IN PROGRESS** when sampled.
4. **Planner projection replay regression** at `df4235e8b25c1e678e0f1f85962b564bec52050b`:
   `tests/test_planner_projection_nested_identity_run667.py` adds **5 authored tests**: callback-time nested tool/scope mutation or value-equal arguments replacement (3), refusal of truly replayed SUCCEEDED without separately verified result receipt, and rejection of a forged status revision/digest. Synthetic SQLite event count is checked unchanged for rejected projections. The source path and tests are combined here; [CI #42274022671](https://github.com/Iam-2squared/ark-ai/actions/runs/42274022671) was **IN PROGRESS** when sampled.
5. **Personal Context revocation restart/cross-handle integrity** at `a40274402a1cba872a80c5f180393a39b73cedb2`:
   `tests/test_revocation_restart_prefix_run667.py` adds **3 authored tests**: independently retained veto prefix survives restart with a newly revoked scope; another SQLite handle cannot duplicate one scope veto; unrelated owner/namespace is isolated without implying consent. No actual Memory erasure or veto removal. [CI #42274472110](https://github.com/Iam-2squared/ark-ai/actions/runs/42274472110) was **QUEUED** when sampled.

**Total:** **17 authored new regression cases**, source hardening of one existing non-UI module, 4 new test modules. The number of tests authored is **not** an assertion that the exact final HEAD has fully passed.

## Exact file-scope review

Comparison `ec9f70a8...a4027440` reported five commits ahead and **exactly five files changed**: the Planner projection source and the four non-UI test files above. No new UI/frontend integration, package dependencies, V1/V2/Local UI/Launcher frozen artifacts, frozen V3 Contract, action/policy grant surface or real ToolBackend effects were changed.

## Limitations and safety boundaries

- SQLite/read-only review, local synthetic digests and caller-supplied clocks cannot authenticate writer/actor identity, cross-process independent storage custody, consent, externally trusted time, real tool results, exactly-once external effects or safe retry after COMMIT-UNKNOWN.
- Recovered Planner **SUCCEEDED** is still intentionally rejected by the detached projection without independently reviewed result receipts; no fabricated result hash or `COMPLETE_UNVERIFIED` is returned. Only inert `READY_MOCK_ONLY` can appear for eligible unstarted reads.
- No paid service/API, external GPU compute, model/Candidate generation or export, protected V2 evaluation, new account/credential, physical PC action, notification, irreversible operation, UI work or unauthorized main merge was attempted.

## Next plan / 今後の方針

1. Finish exact latest HEAD's six Ubuntu/Windows jobs. Inspect and minimally fix any real CI failures on the **normal GitHub Contents API**; never infer full GREEN from earlier partial jobs.
2. Continue read-only/retained Memory COMMIT-UNKNOWN and ABA/expiry reconciliation and Planner independent SUCCEEDED result receipt binding. Neither stage can issue live permission or automatically replay unknown WRITE.
3. Advance registry-bound mock READ / exact-type PermissionGate / durable occurrence and audit-before-action only after dependent exact-head GREEN. Keep permission/approval, receipt, and clock provenance separate.
4. Continue scoped privacy revocation/retention, proactive restart quarantine, observation fixture lineage and free-only V3 path/identity/approval guards; keep PR #5 protected evaluation/training, UI PR #9, and main merge gated.
