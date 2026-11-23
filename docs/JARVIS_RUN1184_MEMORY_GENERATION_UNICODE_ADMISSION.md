# Run1185 — Rebased Memory generation-CAS Unicode identity admission

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent HEAD at rebase: `1513277445b4308c4712f4a07f16dc13e806819e` (includes the Planner Unicode-format admission integration; no Memory generation-CAS source overlap).
- Rebased from Draft PR #368 exact child HEAD `d57cbaea38e28e5fdc324ac789b92db12966c077`.
- Prior exact-head CI [45168838119](https://github.com/Iam-2squared/ark-ai/actions/runs/45168838119) was GREEN 6/6 on the original child head only; it does not transfer to this rebased branch.
- New child branch: `research/run1185-memory-generation-unicode-rebase`.

## Change

- Carry forward the opt-in Memory generation-CAS complete Unicode General Category `Cf` rejection for owner ID, namespace and source ID.
- Pin the import-original `unicodedata` module and exact `category` classifier before and after identity scanning.
- Preserve existing C0/C1, bidi, separator/default-ignorable checks, UTF-8 byte budgets, CAS transaction order, no-retry behavior, Memory v1 schema/public API and frozen MemoryScope/MemoryWrite constructors.
- Add synthetic regressions for U+0600, U+FFF9 and U+E0001, positive Japanese identifiers, and module/classifier substitution denial before callback use.

## Validation boundary

The prior source child passed CI 6/6 at its exact original head. This rebase requires fresh exact-head Windows/Linux × Python 3.11–3.13 CI. No local pytest/Ruff result is claimed. The change remains an in-process identifier-integrity guard, not a Python sandbox, authenticated provenance, trusted time, consent, physical erasure or cross-store atomicity. The token remains non-authorizing.

No paid/external compute, paid API/service, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, destructive operation, frozen-contract change, UI/frontend work, external dispatch or main merge is involved. PR #5 and #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
