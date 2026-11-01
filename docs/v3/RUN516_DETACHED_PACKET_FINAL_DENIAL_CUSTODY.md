# Run516 — offline authorization-packet final denial custody

**DRAFT / V3 NOT_PASSED / review-only**. No paid GPU run, Candidate, training, promotion or protected V2 evaluation is authorized by this packet.

## Source boundary and exact commits

- PR #5 `research/v3-learning-evaluation` initial work-basis HEAD `a73919dca17ce3370cf90711e0e499b55e0cb163`.
- `src/ark/learning/authorization_packet_verify.py`, commit `267ed7bfb574232b23adade8fefc44866772f86f`, blob `7ce66d00b3c87d23b013a8f36dac04170b5cb4e5`.
- `tests/v3/test_authorization_packet_final_denial_run516.py`: source/test HEAD `4ed2e9de1f38b593a2d783105502daba3987c67f`, then **import-order-only** correction at `50aeb0eae122c69ecebe58ca9b7c366d4c082642`, test blob `6dea0289ba5d03f62c4f8f84d250f3c3d3eaad46`.
- **4 newly authored pytest cases** (three parameter expansions plus one getter-epoch case), not independently run local PASS counts.

## Invariant tightened

`verify_detached_authorization_packet` already rebuilds canonical packet bytes and compares a separately retained SHA-256. That comparison establishes only a local consistency check, not independently authenticated approval or consent.

A false-valued synthetic witness property may be a reentrant callback. A malicious final getter can modify a previously inspected authorization descriptor *after* the first denial pass. The verifier now repeats exact witness field checks and all `_DENIAL_FLAGS` (external compute, Candidate generation, protected evaluation, main merge) during the final callback/JSON input epoch, rejecting any authorization claim not **exactly False**. New regressions inject a late flip of `external_compute_authorized` at different getter reads, or `candidate_generation_authorized` during a digest getter, and require rejection.

The existing frozen V3 contract and training execution checks remain unchanged; no policy approval is issued.

## CI outcome is HEAD-specific

- First source+test [41258465205](https://github.com/Iam-2squared/ark-ai/actions/runs/41258465205) at `4ed2e9de1f38b593a2d783105502daba3987c67f`: **6/6 FAIL**, with Ruff I001 import block; standard GitHub Contents API was used to fix **only imports**.
- Corrected source+test [41258635907](https://github.com/Iam-2squared/ark-ai/actions/runs/41258635907) at `50aeb0eae122c69ecebe58ca9b7c366d4c082642`: **6/6 GREEN** when last checked (Ubuntu Python 3.11/3.12/3.13 and Windows Python 3.11/3.12/3.13). These are CI jobs, not independently performed local model/GPU tests.
- Earlier Run515 [41254241274](https://github.com/Iam-2squared/ark-ai/actions/runs/41254241274): 6/6 GREEN at predecessor HEAD, not evidence for Run516 changes.

## Unresolved hard stops

No external GPU/API/billing, credentials, real Candidate weights, protected V2 final opening, automatic promotion, frozen-contract change, external tools or main merge. Immutable HF base/tokenizer revision and byte hashes, human-reviewed dataset/contamination decisions, pinned real runtime identities, proposed provider cost cap and explicit JPY authorization remain unresolved. No synthetic hash or unverified timestamp can replace them.

**Next plan:** continue offline-only exact-byte path/provenance and authority-denial guard reviews while separate physical-PC and potentially billable lanes remain gated by explicit authorization.
