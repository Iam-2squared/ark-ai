# ARK AI — Run714: detached READ exact inputs and cross-owner Memory custody

**Scope:** free-only, non-UI Draft [PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), branch `research/jarvis-foundations`. Initial basis `e05e13b7dd3567e32469b4cd4fd512aa599f71ba`. Implementation/tests saved by ordinary GitHub Contents API, no force/raw Git writes. **ARK/JARVIS/V3 NOT_PASSED.** No real tool, privileged machine action, model, GPU or paid service invoked.

## A — Planner detached READ expected-input integrity

- [`a40e520fc16f64d2572238041fe91f6951d190d8`](https://github.com/Iam-2squared/ark-ai/commit/a40e520fc16f64d2572238041fe91f6951d190d8) introduces opt-in `src/ark/agency/disconnected_read_input_binding_review.py`. The existing detached READ recovery bridge already validates receipt sequence, request/operation/result hashes, dependency order, terminal states and the retained journal count/tip; it did not know the caller's **expected per-step input digests**.
- The new read-only second-stage review requires a bounded, exactly typed ordered tuple of `(step_id, input_sha256)` for **every and only** successful plan step. It validates the original full journal recovery before comparing stored receipt input hashes, then returns a domain-separated input-binding digest and four original false-only authority flags. A valid locally rehashed SQLite receipt with an **unexpected input digest is now rejected** by this *optional* reviewer.
- [`b711dd79ebdc282e8823423884b27df447360df8`](https://github.com/Iam-2squared/ark-ai/commit/b711dd79ebdc282e8823423884b27df447360df8) adds **11 new pytest cases**: SQLite create/close/reopen positive case, recomputed valid chain with wrong input, seven invalid/missing/reordered/duplicate/extra manifest cases, unrelated success under UNKNOWN branch, and counterfeit result-constructor early rejection.
- **Boundary:** expected inputs and retained tip are **caller-supplied**. The review does not independently authenticate their custody, attest execution or authorize dispatch/replay. The exact input digest must ultimately originate from a separately preserved original request payload. This does not integrate real ToolRegistry, PermissionGate, or an executor.

## B — Memory global event integrity across unrelated owners

- [`e1dc01eb5a9f0b3f7c1e9c1ab24c5c38c619f6bf`](https://github.com/Iam-2squared/ark-ai/commit/e1dc01eb5a9f0b3f7c1e9c1ab24c5c38c619f6bf) adds **4 new fixture cases** in `tests/test_memory_cross_owner_global_prefix_custody_run714.py`. [`083bff7496e5da3f661fdc1cad8623169097b67f`](https://github.com/Iam-2squared/ark-ai/commit/083bff7496e5da3f661fdc1cad8623169097b67f) applies a formatting-only follow-up.
- In three disposable SQLite corruption fixtures, foreign-owner event time/revision/owner is rewritten **without changing COUNT/MIN/MAX or the SQLite AUTOINCREMENT high-water**. The original target CAS token and target row remain unchanged, but the independent *global* `compare_local_memory_event_prefix` and `review_memory_event_alignment` must reject. A fourth case checks a valid unrelated append advances the global prefix (still `ADVANCED_PREFIX_UNAUTHENTICATED`) while the target's lifetime token remains unchanged.
- **Boundary:** a per-row generation token is intentionally not an authenticated *global* history witness. Global event checks are separate read snapshots, not atomic authority to mutate; neither a global hash nor a matched local CAS image proves historical writer identity, consent, erasure or an ambiguous caller's COMMIT. No production Memory schema/put/delete/CAS change.

## CI, verification and independent review

- Exact starting checkpoint `e05e13b7dd3567e32469b4cd4fd512aa599f71ba`: [CI #42487792442](https://github.com/Iam-2squared/ark-ai/actions/runs/42487792442) completed **6/6 GREEN** across Ubuntu/Windows × Python 3.11–3.13 before Run714 changes.
- Run714 READ tests: [CI #42491805724](https://github.com/Iam-2squared/ark-ai/actions/runs/42491805724) had **Ubuntu 3/3 GREEN, Windows 3 IN PROGRESS** at the earlier inspection; no 6/6 PASS claim. The Memory style-checkpoint [CI #42492095936](https://github.com/Iam-2squared/ark-ai/actions/runs/42492095936) was **IN PROGRESS**. Subsequent report/checkpoint commits have separate runs; exact final-head CI is not assumed.
- Read-only secondary audit of frozen [V3 PR #5](https://github.com/Iam-2squared/ark-ai/pull/5) at `805b377697472268db02650a89c7a94b1c5337c8`: the existing `docs/v3/PRE_PAID_COMPUTE_GATE.md` still requires immutable model/dataset/provenance, environment, cost proposal and explicit preflight approval. **No V3 files or frozen contracts were changed.**
- Full local `pytest`, Windows machine verification and external privacy/provenance review **not executed** in this invocation. Authored test counts are not all-platform PASS evidence until matching CI finishes.

## Integration blockers and next

1. Confirm exact final-head six-job CI. If red, use actual failing job logs to fix the smallest proven issue before extending the same code path.
2. Independently retain and authenticate original READ input manifests and journal tips before treating the optional input join as an integration dependency; never silently infer effective tool inputs from a plan.
3. Preserve Memory global history integrity across CAS, WAL and ambiguous-COMMIT review **within coherent snapshots** before claiming complete cross-owner recovery; no automatic retry.
4. Then review immutable registry-bound permission identity, durable occurrence authorization, trusted-clock audit-before-action and disconnected mock; leave real executor blocked.
5. Keep PR #5/#8/#9 Draft/unmerged, UI development paused, frozen V1/V2/Local UI/Launcher evidence unchanged, and all paid/hardware/approval/evaluation gates closed.
