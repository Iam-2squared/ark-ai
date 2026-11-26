# Run1198 — ActionAudit bounded outcome and Unicode format-control rebase

## Exact basis

- Parent: Draft PR #8, branch \`research/jarvis-foundations\`.
- Exact parent HEAD at child creation: \`2df6b261554428cd01871f2723ce87c4dd05e4b4\`.
- Reapplies the isolated outcome-boundary finding from Draft PR #13 (Run990) onto the current foundation; PR #13 itself remains untouched.
- Child branch: \`research/run1198-action-audit-outcome-unicode\`.
- Production source commit: \`e25ba822193ecc932e4096f05262b43366252f9a\`.
- Focused regression commit: \`a84a690bb0e810c1645eeceabc144ca95d499295\`.

## Change

The ActionAudit v1 append path previously accepted any non-empty outcome text, and persisted outcome TEXT had no byte ceiling. The new validator preserves the open outcome vocabulary while applying:
- exact-string admission;
- a maximum of 256 Unicode code points and 256 UTF-8 bytes;
- strict UTF-8 encoding;
- rejection of C0/C1, bidi, line/paragraph separators, default-ignorable controls and every Unicode General Category \`Cf\` character;
- import-time Unicode module/category identity checks before and after scanning.

Caller input retains the existing \`ValueError\` surface and is rejected before SQLite open or trusted-clock sampling. Persisted oversized outcome values are refused by SQLite-side BLOB-length preflight before Python hydration. Persisted control/format values fail closed during historical-prefix validation and event reads; append is refused before clock sampling. No corrupt row is repaired.

## Regression coverage

Synthetic temporary SQLite tests cover empty/whitespace, code-point and UTF-8 byte overflow, controls/format characters across BMP and supplementary planes, lone surrogates, wrong exact types, Unicode dependency substitution, a valid 256-byte UTF-8 boundary, and corrupted persisted rows with no clock call or mutation.

## Preserved contracts and limits

ActionAudit v1 DDL/public fields, event identity, chronology, append transaction and COMMIT-UNKNOWN behavior are unchanged. The open outcome vocabulary is not replaced by a new enum. This is local input/resource-integrity hardening, not an authenticated event chain, independent custody, trusted time, consent, cross-store atomicity or proof of an external effect. The separate v1-to-v2 migration plan remains untouched.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. No real backend dispatch, private database, paid service, external compute, Candidate, protected V2 evaluation, credentials, hardware, destructive action, frozen-contract change, UI/frontend work or main merge is involved. PR #5 and #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
