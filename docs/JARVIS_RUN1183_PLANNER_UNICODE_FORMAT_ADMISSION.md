# Run1183 — Complete Unicode format-control admission for Planner identities

## Exact basis

- Parent branch: `research/jarvis-foundations` (Draft PR #8).
- Exact parent work-basis HEAD at child creation: `844e68078a6a9c2172b84a40ed828d02b3fc161a`.
- The parent commit after `a27344061d5abc5304c44c03f7457005deb4c89d` changed only `docs/PROJECT_STATUS.md`; compare evidence showed no source/test changes. The earlier parent run [45155119780](https://github.com/Iam-2squared/ark-ai/actions/runs/45155119780) was GREEN 6/6 on `a27344061d5abc5304c44c03f7457005deb4c89d`, not on the later documentation commit.
- Child branch: `research/run1183-planner-unicode-format-controls`.
- Exact child HEAD before this report: `d148e7a015c459ee121370dd89451714af3fbf6a`.

## Finding

Planner's optional `PlanGraph` label admission rejected a hand-maintained set of C1, bidi, separator and default-ignorable code points, but did not reject every Unicode General Category `Cf` format character. Synthetic labels containing U+0600, U+FFF9 or U+E0001 could therefore pass the label gate when used as a step ID, dependency, ToolCall tool/capability/scope, or transition ID.

This is an identity-display and local recovery/audit consistency boundary. It is not a change to the frozen `PlanStep` or `ToolCall` constructor contracts.

## Change

- Pin the import-original `unicodedata` module and `category` function.
- Reject every character whose Unicode General Category is `Cf` during standalone PlanGraph label admission.
- Preserve the existing explicit C1, bidi, line-separator and default-ignorable checks; the broader category check supplements rather than weakens them.
- Check the Unicode dependency before caller-controlled label processing and again after category scanning.
- Recheck the policy during PlanGraph epoch validation so a changed classifier cannot be used by an already-constructed graph.
- Keep frozen dataclasses, schemas, Planner transition rules, journal semantics and dispatch authority unchanged.

## Regression coverage

The new synthetic test module has 21 parameterized/ordinary cases:

- 15 cases: U+0600, U+FFF9 and U+E0001 across step IDs, dependency IDs, ToolCall tool, capability and scope.
- 3 cases: transition IDs reject the same controls without changing status/revision.
- 1 case: ordinary Japanese graph labels remain valid.
- 2 cases: replaced Unicode module/classifier bindings are denied before the replacement callback receives graph text.

## Validation boundary

No local pytest or Ruff result is claimed. A fresh exact-head Windows/Linux × Python 3.11–3.13 CI run is required on the final child HEAD. Earlier CI on the parent or another child does not transfer.

This is an in-process dependency-integrity check, not a Python sandbox, authenticated runtime identity, independent custody or trusted-clock proof. No real tool backend, permission grant, consent, external effect, automatic replay or production dispatch is introduced.

No paid/external compute, paid API/service, Candidate generation/promotion, protected V2 evaluation, credentials, physical hardware action, destructive operation, frozen-contract change, UI/frontend work or main merge is involved. PR #5 remains gated Draft/unmerged; PR #8 remains Draft/unmerged; PR #9 remains paused and untouched. **ARK/JARVIS remains NOT_PASSED.**
