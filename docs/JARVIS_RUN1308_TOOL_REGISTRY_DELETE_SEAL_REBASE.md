# ARK Run1308 — ToolRegistry deletion-seal regression rebased

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `b11a17c6c078d1b4675fa4f392a7810e17ba7cb5`.
- Rebased test-only package from Draft PR #473, whose prior child was based on `101be0cb505d8ae045027faf54f8d982c0a4f9d2`.
- The current `src/ark/agency/registry.py` was inspected before carrying the regression forward. The existing source exposes the sealed slots and checks the original deletion guard; no production source change is included.

## Regression coverage

- Ordinary deletion of every sealed ToolRegistry state slot is refused.
- Reflective deletion of the registration map is rejected by the public `bind` path before backend access.
- Replacing the class-level `__delattr__` guard is detected before the substituted guard executes.
- Healthy deterministic binding remains usable; the inert backend is never called.

## Evidence boundary

The predecessor branch's evidence is not transferred to this new base. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no local pytest/Ruff PASS is claimed.

This is local in-process object-integrity evidence only. It does not establish process isolation, authenticated backend identity, permission, trusted time, durable authorization, or exactly-once external effects.

No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, destructive action, frozen-contract change, UI/frontend work, or main merge. PR #5 and #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
