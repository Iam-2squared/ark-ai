# Run1103 — durable-first mock WRITE authorization ordering

## Exact basis

- Repository: `Iam-2squared/ark-ai`
- Parent: Draft PR #239, `research/run1103-durable-first-auth-order`
- Exact source parent HEAD: `385010f49df16ef5cd56788622873415dc7c0581`
- Original foundation base: Draft PR #8, `research/jarvis-foundations`, HEAD `e8761e183094cd27955423844a8db7d6b0063829`
- Child branch: `research/run1103-durable-first-auth-order-tests`
- Regression suite: `tests/test_disconnected_mock_executor_durable_first_run1103.py`

## Ordering under test

For WRITE, the disconnected executor now performs:

1. Bounded one-time materialization of the supplied grant iterable.
2. Exact registry-bound PermissionGate preflight on a throwaway gate. This checks grant, request and expiry consistency but is not dispatch authority and does not spend the executor's gate.
3. Durable synthetic occurrence reservation, keyed by the token digest and registry-bound action identity.
4. Consumption by the executor's actual process-local PermissionGate.
5. Fail-closed pre-action audit commit.
6. Exact in-process mock backend call and completion audit.

If durable reservation fails, the executor's actual local gate token remains unspent. If the actual gate denies after the reservation, the durable occurrence remains reserved and no audit/backend call occurs. Neither path retries.

## Regression coverage

Five synthetic tests cover duplicate durable reservation before actual-gate spend, actual-gate denial after durable reservation, missing exact-scope grant, grant-generator failure before reservation, and successful ordering with explicit non-authority receipt assertions.

## Limits

Only the exact deterministic MockToolBackend and disposable local SQLite stores are used. Timestamps and grants are synthetic. The occurrence and audit databases remain separate stores; this does not prove cross-store atomicity, trusted time, authenticated consent, power-loss durability, exactly-once external effects, real backend dispatch, or independent storage custody. No frozen contract/schema, UI, V1/V2/Local UI/Launcher evidence, PR #5, PR #9 or main branch is changed.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. **ARK/JARVIS remains NOT_PASSED.**
