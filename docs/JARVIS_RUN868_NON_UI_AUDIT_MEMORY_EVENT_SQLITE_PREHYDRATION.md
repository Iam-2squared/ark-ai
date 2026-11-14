# ARK AI Run868 — non-UI audit and Memory event SQLite prehydration

Scope: existing open **Draft PR #8**, disconnected/free-only/reversible. **ARK/JARVIS NOT_PASSED.**
No UI/frontend work, frozen contract/DDL revision, live tool, external effect, private
data, training, Candidate, paid GPU/API or protected final evaluation.

## Verified work basis

- Previous canonical checkpoint: `97bdb59a61585aa6aceef3db7185da3fa881e765`
  (Run867). [CI #43578243653](https://github.com/Iam-2squared/ark-ai/actions/runs/43578243653)
  **GREEN 6/6** (Ubuntu/Windows × Python 3.11–3.13), verified from
  the actual six jobs at run start; cannot be inherited by Run868 commits.
- PR #5 and PR #9 separately confirmed open/Draft/unmerged; left untouched.
  V1/V2/Local UI/Launcher and protected evaluation contracts remain frozen.

## Package A: persisted ActionAudit v1 event admission

- Source at `09e875d093b76970958d5dc1364159a037f4c4df`;
  synthetic tests at `594d44a9122e9e0325e515d2c716f27578e21aca`
  (**8 authored parameterized/normal tests**).
- Before Python page hydration or a full historical event scan, a predicate
  reads at most one **SQL classification row**, checking exact SQLite storage
  classes and the actual UTF-8 byte widths (68 request-id, 64 argument hash)
  in the **same pinned read/writer transaction**. A BLOB identity cannot
  become a returned ActionAuditEvent or a basis for a new append.
- Intermediate Ubuntu CI from
  [#43582506592](https://github.com/Iam-2squared/ark-ai/actions/runs/43582506592)
  identified **three existing diagnostic-match regressions**: paged malformed
  predecessor clock, restarted append malformed clock, and BLOB tool-tail
  message. This is a real CI FAIL, **not** a GREEN claim.
- Semantics-preserving source repair
  `d7bde15b888de3362a4ce10d2e788cae33dc687a` classifies errors using
  bounded SQL outputs; it retains original clock/identity diagnostic strings
  before any unsafe persisted value is fetched. Test compatibility update
  `4b49a915ce512db25aa828dbdd59cd7d94d9b6d3` accepts the documented
  diagnostic variants. **These later commits require fresh exact-head CI.**

## Package B: scoped Memory event page admission

- Source `23bdcb08c980d1225f08b616791857126adaa521`,
  synthetic tests `460aeb0675c0f285a504c403f7ad684c9358e549`
  (**9 authored cases**).
- Admission uses a bounded ordered SQL **selected-page CTE** in the same
  read transaction, before Python `fetchall()` of that event page.
  `mem_`+SHA has exactly 68 UTF-8 bytes; each valid event operation has
  exactly 6. Original MemoryScope owner/namespace budgets of <=256
  codepoints imply <=1024 native UTF-8 bytes. INTEGER storage classes are
  checked before hydration. Valid scoped pagination stays unchanged.
- The full local global append-ID/high-water consistency check is retained,
  but this **page-specific** field check deliberately does not turn another
  owner's stored event into the current owner's disclosed data.
  Read operations still enforce on-row canonical scope/identity checks.

## Test and safety interpretation

All 17 new test cases are **authored**, not automatically proven to pass by
earlier successful runs. GitHub Actions is triggered automatically by each
normal Contents-API write; no manual duplicate workflow dispatch was used.
CI from intermediate source/test commits may fail independently of later
repairs. Full independent local pytest/Ruff, host PC/GGUF, trusted clock and
real side-effect tests were **not** run.

Neither SQL guard bounds every historical ActionAudit TEXT string: pre-existing
v1 tool/capability/scope/outcome TEXT contracts have no byte limit, and changing
their meaning here would be a separate explicit compatibility review. SQL
checks do not prove SQLite path-to-open or WAL/SHM final-close race freedom,
memory witness independent custody, COMMIT-UNKNOWN caller attribution,
restart-safe WRITE one-shot approval, external exactly-once effects, real
consent, or an action-executor trust boundary.

## Next plan / 今後の方針

1. Obtain **latest exact-head** Windows/Ubuntu × 3.11–3.13 CI results;
   repair any genuine regressions using the normal permitted GitHub write path.
2. Review Memory/ActionAudit WAL/SHM last-client-close and COMMIT-UNKNOWN
   disposable process fixtures, preserving UNKNOWN as manual-only.
3. Strengthen Planner persisted UNKNOWN lineage and Memory coherent
   CAS/expiry snapshot handling without mutating the frozen v1 contract.
4. Advance independent privacy-safe Personal Context, proactive and
   observation fixtures while any relevant CI remains in flight.
5. Connect registry-bound identity / exact PermissionGate / durable
   occurrence / trusted audit-before-action / mock executor **only after**
   prerequisite exact-head GREEN and without live backend dispatch.
