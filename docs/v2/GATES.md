# V2 completion and promotion gates

Current: **ADVANCE DEVELOPMENT / MOCK VALIDATION**.
V1: **CODE COMPLETE / REAL-MODEL OFFLINE GATE PENDING**.

## Branch implementation checklist

- [x] Intelligence Contract fixed
- [x] Context Manager and reset semantics
- [x] Conversation / reasoning task policies
- [x] Explicit model capability interface
- [x] Fixed Math scoring
- [x] Fixed Reasoning scoring
- [x] Restricted Coding tests
- [x] Fixture regression comparison and future result schema
- [x] Unit / failure / boundary tests
- [ ] CI GREEN on the current Draft PR head (confirm in GitHub)
- [x] Documentation

## Unfulfilled gates - remain pending

- [ ] V1 formally PASS after target-PC evidence review
- [ ] Reviewed V2-J real-model evaluation adapter (no advance-branch CLI unlock)
- [ ] Real GGUF evaluation
- [ ] Real-model conversation/context verification
- [ ] Real-model Math measurement
- [ ] Real-model Reasoning measurement
- [ ] Real-model Coding measurement
- [ ] V2 evidence recorded and reviewed
- [ ] V2 formally PASS

## Merge constraint

Keep the PR **Draft** with **MERGE BLOCKED: V1 PASS pending** in title/body.
Do not enable auto-merge. CI green does not grant merge authorization while V1 is pending.
No workflow publishes, promotes or merges this branch. V1 target evidence must be checked
before changing this state. A documented green infrastructure run is not that evidence.

When the PC becomes available: use main for the V1 offline cold-start and two benchmark
runs first. Review the conversation, reset, errors and JSONs. If a V1 defect appears,
fix main and integrate that fix into V2. Only after V1 PASS, review the V2 real-runtime
connection, repeat the same frozen suite and record actual model measurements. Treat
V2-J as unfulfilled until then. Long-term memory, tools, planning, vision/voice and
computer actions are outside this PR.
