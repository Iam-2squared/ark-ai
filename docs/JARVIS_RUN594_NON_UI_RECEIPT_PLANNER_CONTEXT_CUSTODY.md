# ARK AI Run594 — non-UI receipt custody, Planner hashing boundary, Context replay

2026-11-04 JST. Draft PR #8 `research/jarvis-foundations`; work-basis
`502d6da5444f106f02e95eb45eb36382e5eea105`. This is a free-only
disconnected/mock fixture iteration. It does **not** approve external execution,
prove an external effect or promote ARK/JARVIS/V3 to PASS.

## Observed baseline CI failure and semantics-preserving repair

Pre-invocation checkpoint CI [#41742640230](https://github.com/Iam-2squared/ark-ai/actions/runs/41742640230)
failed all six Linux/Windows Python 3.11–3.13 jobs. Python 3.12 on Ubuntu
reported **7,788 passed, 1 skipped, 2 failed**: the two
`dispatch_authorized` and `automatic_replay_authorized` parameter cases in
`tests/test_proactive_receipt_original_authority_run593.py` expected
`gained authority` while the earlier fail-closed branch rejected with
`trigger receipt authority epoch changed`. No source safety checks were
weakened. An initial test correction at
`fdece9ab608d56544917721b88f96eed2626b776` expected only the early
epoch diagnostic, but [CI #41748658600](https://github.com/Iam-2squared/ark-ai/actions/runs/41748658600)
showed the `notification_authorized` parameter still correctly emits
`trigger receipt gained authority` (Ubuntu 3.12: **7,789 passed,
1 skipped, 1 failed**). The final narrow test correction at
`ff53f81bac94cd13f7573fb5ffc6917d393df707` allows both
`gained authority|authority epoch changed`, without changing denial outcome,
SQLite marker or retry behavior. **Final exact-head six-job CI pending** as of
this note; failed earlier runs are not evidence of a final pass.

## Package B — original offline WRITE-slot receipt declarations

- Source `src/ark/agency/disconnected_write_slot_ledger.py` commit
  `99ba630be3a3284ed8c5f030c6d7d4756ebb6686`.
- Regression `tests/test_write_slot_original_receipt_denials_run594.py`
  commit `012d0815c8edcdee53130e082cd1afb259c6a52f`: **6 authored cases**.
- The five original denial-property descriptors are captured at module load.
  Post-COMMIT review rejects an equally False-valued replacement which
  a late-sampled descriptor baseline previously permitted. Reentrant denial
  rebinding remains rejected; neither a committed slot nor a receipt proves
  execution, exact-once effect, attested clock or approval. An old witness
  cannot be reused after a committed reservation.

## Package C — Planner result hashing as a reentrant boundary

- Source `src/ark/agency/planner_journal_review.py` commit
  `4d68dfd5da7eee5674ad04f622869062c2a462cc`.
- Regression `tests/test_planner_digest_denial_recheck_run594.py`
  commit `75d4a835dbe7744b384458f31337ed23fdc6ed30`:
  **2 authored cases** (`recover` and `append`).
- After the last deny-only getter, `PlanGraph.status_digest()` may itself
  be a synthetic callback. Recovery now rechecks original
  `dispatch_authorized` / `automatic_replay_authorized` property identity
  *after* hashing so equal-False descriptor substitution cannot cross the
  last review boundary. A pre-COMMIT append rejection rolls back the tentative
  local event. A recovered RUNNING step still remains UNKNOWN; nothing is
  executed or retried.

## Package D — offline Personal Context receipt custody

- Source `src/ark/personal_context_replay_ledger.py` commit
  `5b8125f67e8f10caa3beafbb7fb1d4a4e6e3ae79`.
- Regression `tests/test_context_replay_original_receipt_epoch_run594.py`
  commit `51ba17761dc54e6347353d4d31bbc11beece6499`:
  **7 authored cases**.
- The five original False-only Context receipt descriptors are pinned and
  checked after the last receipt getter; exact request ID and witness carrier
  are revalidated after the final callback. Tests probe five equal-False
  replacements, one value-equal request-ID rebinding and normal denial-only
  operation. The SQLite marker represents local request deduplication, **not
  authenticated consent, revocation freshness, permission to disclose, an
  authenticated erased record or actual tool dispatch**. A rejected
  post-COMMIT receipt is never permission to retry.

## Scope and verification boundaries

The **15 new authored tests** (6 + 2 + 7) are source-case counts, not
independently executed local pytest successes. GitHub Actions on the exact
commit, with Linux and Windows 3.11–3.13, is the verification gate. Earlier
source/test runs [#41748821834](https://github.com/Iam-2squared/ark-ai/actions/runs/41748821834)
and [#41748989846](https://github.com/Iam-2squared/ark-ai/actions/runs/41748989846)
cannot validate the later corrective test commit. No equivalent manual CI
rerun was launched. Inspect the final exact-head job outcomes before citing
new GREEN evidence.

No V1/V2/Local UI/Launcher frozen evidence, Memory or Planner frozen contract,
PR #5 protected V3 final-evaluation gate, or main branch was edited.
PR #9 Next Generation UI remains explicitly **PAUSED**, Draft/unmerged.
Only normal GitHub Contents API writes were used, with HEAD checked before
each change. No paid service, GPU, Candidate generation/promotion, credential
creation, real ToolBackend execution or external action occurred.

## Next plan / 今後の方針

1. Inspect full six-job exact-head CI and repair only observed regressions by
   the normal GitHub Contents API; no speculative PASS labels.
2. Review and harden restart-safe audit-before-action, occurrence replay
   quarantine and registry-bound permission decisions in disconnected mode.
3. Advance Memory generation CAS, coherent expiry/UNKNOWN manual recovery,
   Planner persistent failure propagation and Personal Context revocation
   freshness without fabricating independent authority or trusted time.
4. Preserve all frozen/version gates, keep UI stopped, and leave all Draft PRs
   unmerged unless their explicit controlling approval is supplied.
