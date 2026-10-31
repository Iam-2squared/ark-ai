# JARVIS Run504 — detached receipt verification and V3 final epoch

This is **technical, non-normative source/test evidence** for Draft PR #8 and
Draft PR #5. It is not a PASS, a trusted human sign-off, an execution gate, a
model-training result or a dispatch authorization.

## Work basis and scope

- PR #8 initial checkpoint HEAD: `3db5794167c7e9708ba3df8c8f7d03ddfab41dfe`.
  Source/test work ended at `a7ee631f53e64a043493c39aab60fa31dc27ba38`.
- PR #5 initial HEAD: `5f20a00aa86c20dab76323a82279419a17c19f03`.
  Source/test/CI-fix work ended at `d10807e3493b390af6778b186f6cf837860fbafb`.
- Main baseline: `7a843f17eb96ed13d66f23b58b06406b3002e405`;
  no merge, protected evaluation or real Candidate work requested.

## Five separately bounded source/test packages

1. **Detached Planner schedule receipt:** the verifier no longer accepts
   monkeypatched dataclass `__eq__` as integrity proof. Compare exact primitive
   request/plan/schedule/wave identities; recheck after each denial-only getter
   and after independent plan validation. Source
   `5b2e43e68963f11187badbde2c5693407bf4f619`; tests
   `cd6f311e452233e124e6a826eee581efdffdbdc9`. Six authored cases.
2. **Detached V3 authorization packet witness:** recheck snapshot/packet JSON
   epochs after final digest field reads, not only after authority flag reads.
   Source `660eda1f44553095a4b4198ea476ab915417e6c2`; two tests initially
   `f5d7c77e3497dccda48f136a02f06a728977281a`. CI
   `41202835935` **FAIL** on a test-fixture property lacking the setter needed
   by a frozen slots dataclass; fixed only that property fixture at
   `d10807e3493b390af6778b186f6cf837860fbafb`. The new CI is pending.
   No paid compute or human approval is inferred from a matching local hash.
3. **Memory retained epoch chain:** add `verify_retained_memory_chain` to
   compare all exact receipt fields against an independent deterministic
   recomputation, including post-denial source/result checks. Source
   `90cf76a3e2c8506b65a13651346087e6cb0413e7`; tests
   `a438b21d768618d88705d67acf0f9df0aa597185`. Fourteen authored cases.
   Matching locally retained epochs remain **not** writer provenance,
   historical append-prefix proof, trusted time, erasure or consent.
4. **Detached Planner terminal projection:** exact request/digest/failure-set/
   terminal-state comparison, no dataclass equality shortcut; revalidate
   plan/schedule after denial getters. Source
   `acc7d841bb08027a4c8220e1f6d780bfead8ad8d`; tests
   `70385c4acc046ade26546bb393b0adc34b8318e2`. Nine authored cases.
   Failure assertions are hypothetical; no tool run occurred.
5. **Detached Planner fixture cycle:** reject spoofed receipt equality and
   reflective late changes to digest, wave hashes or plan/schedule under an
   otherwise False permission property. Source
   `2b17d41a1c046b7323e8779abb7d7b5fee7405f9`; tests
   `a7ee631f53e64a043493c39aab60fa31dc27ba38`. Eight authored cases.
   A mock result remains no evidence of side-effect completion.

**39 authored test cases (6+2+14+9+8)**, not an independently executed local
pytest claim. Local Git access remains DNS-blocked, so the repository's exact
GitHub Actions matrix is the only observed execution evidence.

## Evidence and outstanding checks

- Earlier PR #8 checkpoint CI `41200740885`: 6/6 GREEN for **previous**
  Run503 checkpoint only.
- PR #5 source-only CI `41202810929`: GREEN before adding the two new
  late-callback tests. PR #5 test CI `41202835935`: 6/6 FAIL from a
  shared test-fixture constructor failure; the fixture is corrected, not
  assertions removed or weaker. Latest exact-head
  `41203103897`: IN PROGRESS at preparation time.
- PR #8 latest source/test `41203273094`: QUEUED at preparation time;
  earlier partial source CI cannot certify this final HEAD.
- Frozen source blobs verified unchanged: Memory contracts
  `b6e93821ecd69270a7634aceb20775dc36e9953c`, Agency contracts
  `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`, V3 Contract
  `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`.

## Reversible safety limits and next gates

No physical PC access, external tools, paid compute, real model training,
Candidate generation, microphone/camera capture, protected V2 evaluation,
automatic promotion, destructive state mutation, credential provisioning,
frozen contract change or main merge took place. PR #5 and PR #8 remain Draft
until their controlling gates.

1. Check both latest exact-head 6-job CI matrices; fix only observed failures
   and preserve the rest of the regression assertions.
2. Prioritize Memory CAS/expiry/coherent snapshots and Planner UNKNOWN WRITE
   manual quarantine/triage before any durable integration.
3. Bind immutable ToolRegistry and exact PermissionGate in disconnected
   simulations only after lower-level GREEN. Keep trusted-clock audit and
   scheduler occurrence/replay protection fail-closed.
4. Keep V3 approval/identity/provenance checks detached and free-only.
