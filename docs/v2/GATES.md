# V2 completion and promotion gates

Current: **REAL-MODEL ADAPTER IMPLEMENTED / TARGET MEASUREMENTS PENDING**.
V1: **OFFICIAL PASS**, main freeze `7e46a4529879243b4a5bd52bb6575d11c1ec0183`.

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

- [x] V1 formally PASS after target-PC evidence review (PR #4)
- [x] V2 branch includes V1 main evidence freeze
- [x] Explicit local runtime adapter and result schema; simulated adapter tests
- [ ] Real GGUF evaluation
- [ ] Real-model conversation/context verification
- [ ] Real-model Math measurement
- [ ] Real-model Reasoning measurement
- [ ] Real-model Coding measurement
- [ ] V2 evidence recorded and reviewed
- [ ] V2 formally PASS

## Merge constraint

Keep the PR **Draft** with **MERGE BLOCKED: V2 real-model review pending** in title/body.
Do not enable auto-merge. CI green does not grant merge authorization without V2 evidence.
No workflow publishes, promotes or merges this branch. Unit tests simulate the local
adapter; their temporary fake-weight reports are not actual model measurements.

Next: follow [REAL_MODEL.md](REAL_MODEL.md), collect fixed-suite real results and
V1 regression evidence, review all failures without changing questions or scorers,
then freeze the baseline. If a V1 defect appears, fix main separately and sync again.
V2 PASS also requires current-head green CI and no critical V1 regression.
Long-term memory, tools, planning, vision/voice and computer actions remain out of scope.
