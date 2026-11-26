# Run1201 — Proactive trigger Unicode format-control rebase

## Exact basis

- Parent: Draft PR #8, branch \`research/jarvis-foundations\`.
- Exact parent HEAD: \`2df6b261554428cd01871f2723ce87c4dd05e4b4\`.
- Rebased the isolated proactive-trigger Unicode finding from Draft PR #364 (Run1180) onto the latest PR #8 parent; PR #364 remains untouched. The source file was byte-identical between the predecessor base and the latest parent. Predecessor Draft PR #385 exact-head CI [45209468351](https://github.com/Iam-2squared/ark-ai/actions/runs/45209468351) was GREEN, 6/6, but does not transfer to this rebase.
- Child branch: \`research/run1201-proactive-trigger-unicode-rebase\`.
- Production source commit: \`2e913ea00f214723a18c31d09232fb16b781559f\`.

## Change

The disconnected synthetic proactive-trigger policy already rejected a hand-maintained set of control/invisible characters before hashing or SQLite access. That list did not cover every Unicode General Category \`Cf\` scalar.

- Pin the import-time \`unicodedata\` module and exact \`category\` function.
- Reject all \`Cf\` characters during initial identity admission and retained-policy revalidation.
- Check dependency identity before and after scanning.
- Preserve existing C0/C1, NUL, bidi, separator, UTF-8 and 512-byte limits.
- Keep the trigger ledger disconnected and deny-only; no notification, dispatch, automatic replay, trusted clock or consent authority is added.

## Synthetic regression coverage

Temporary in-process policy values cover U+0600, U+FFF9 and U+E0001 in owner, namespace, definition ID and policy revision; reflected mutation of retained policy fields; Unicode category substitution; and module substitution before policy admission.

## Limits and validation

This is an in-process validation guard, not a Python sandbox or independent runtime attestation. No real scheduler, notification, Tool, external action, live user data or private context is used. No frozen Observation/Memory/PermissionGate contract or evaluation boundary changes.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. No paid/external compute, paid API/service, Candidate, protected V2 evaluation, credentials, physical hardware, destructive operation, frozen-contract change, UI/frontend work or main merge is involved. PR #5 and #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
