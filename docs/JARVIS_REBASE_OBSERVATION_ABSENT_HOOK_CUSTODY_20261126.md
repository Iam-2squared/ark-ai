# Rebase — Observation envelope and fixture adapter absent-hook custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `db7f12a406ef668b2f6bf1cdbf46715d8a406ce8`.
- Both source files and the two adjusted legacy regression files were verified byte-identical between old basis `7178d91c4ae332908dd8bd34fd9f8ab939385bd3` and the current parent before rebase.
- Rebased from Draft PR #599 / Run1414, exact child HEAD `a6d3a1a608aa833c855f64d09c64c072ac7a7bb2`.
- Prior exact-head CI run [45668084989](https://github.com/Iam-2squared/ark-ai/actions/runs/45668084989) was GREEN on that old child HEAD only; it does not transfer to this rebase.
- New child branch: `research/rebase-observation-absent-hook-custody-20261126`.

## Finding and correction

Both ObservationEnvelope and the fixture adapter recorded absent `__new__`, `__getattribute__` and `__getattr__` hooks with `vars(type).get(name)`. Explicit `None` therefore compared equal to true absence. The change introduces unique absent-hook sentinels and retained import-time epochs for exact envelope aliases, field/hook vectors, original descriptors and sentinels. Expected-absent hooks require namespace non-membership; expected-present descriptors require membership and exact identity.

The previous exact-head CI failure on the older Run1414 child exposed two legacy tests that expected a later constructor-result error even though the new guard correctly rejects the substituted constructor earlier. This rebase retains the corrected assertions and explicitly checks that the counterfeit constructor is never invoked.

## Regression coverage

- Explicit `None` and each module's exact sentinel installed as each absent hook.
- Sentinel rebinding, equal-valued-but-distinct hook-vector replacement and epoch replacement.
- Joint replacement of public/private envelope type aliases.
- Identity getter rejects hook substitution before the digest callback.
- All class-slot mutation probes run in isolated subprocesses.
- Existing fixture-constructor tests assert the earlier fail-closed boundary without executing counterfeit constructors.

## Scope and evidence boundary

Synthetic, disconnected fixture inputs only. No live microphone, camera, screen capture, file, network, ToolBackend, notification, device or production dispatch is introduced. Observation Envelope v1 fields, schema, digest domain, privacy labels, parent lineage, fixture byte limits and public adapter signatures are unchanged. No consent, trusted-clock, source authenticity, independent custody, physical deletion, authorization or exactly-once external-effect evidence is claimed.

No paid/external compute or service, Candidate generation/promotion, protected V2 evaluation, credential/account connection, hardware action, destructive operation, frozen-contract change, main write/merge or UI/frontend work occurred. PR #5 remains gated Draft/unmerged; PR #8 remains Draft/unmerged; PR #9 remains untouched.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff result or Observation/production-readiness PASS is claimed.
