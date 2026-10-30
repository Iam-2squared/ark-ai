# Run481 — Memory chain / Context replay / WAV result custody / V3 numeric guards

Free-only, reversible code and tests on Draft PR #8 and #5. All authored data is synthetic. This document is NOT a PASS, an authorization grant, or evidence of real-world effects.

## Four independent packages — 66 parameterized pytest cases authored

1. **Memory retained-epoch chain (16 cases)**. Source src/ark/memory/retained_epoch_chain.py blob 91b33dc87af0489334b46bf65a2edc9648335e70; tests tests/test_retained_memory_epoch_chain_run481.py blob aa9a666558312ad5906205882b15b8ea4beb879c. Bounded 2–16 exact separate observations; reject regressions, same-tail rewrites, scope retargeting, duplicated observation objects, or input mutation across callbacks. Digest binds every intermediate observation. Appended events remain ADVANCED_HISTORY_UNVERIFIED, not authenticated history, trusted writer, consent, external custody, or cross-store atomicity. Memory v1 DDL unchanged.

2. **Personal Context synthetic SQLite replay ledger (21 cases)**. Source src/ark/personal_context_replay_ledger.py blob ed189bdc44556c77d070cb2b25c12346395f6053; tests tests/test_personal_context_replay_ledger_run481.py blob 28f3729d92a2df114e85f8a22c9923cdcc8ff690. Create-only schema, bounded read-only witness, BEGIN IMMEDIATE retained-witness CAS, UNIQUE request IDs, hash-chain validation, path alias checks, restart/replay and post-COMMIT error handling. Stores no context text, but request and owner hashes are linkable private metadata. Cannot authenticate caller identity, consent, revocation, independent custody, real exactly-once effects, or Tool authority.

3. **Disconnected WAV receipt/result custody (8 cases)**. Source src/ark/offline_pcm_wav.py blob 8d67f2db21b6614283113e8d02d790a01e4cc405; tests tests/test_offline_pcm_wav_result_custody_run481.py blob ecf0fae7ca2bce6025307b9f529f653eab4fe9f2. Pin original result class/request fields; reject forged constructors, mutated result, callback-induced source mutation and false consent/microphone/speech/disclosure flags. No microphone or ASR operation.

4. **V3 postrun metric numeric boundary (21 cases)**. PR #5 source src/ark/learning/run_manifest.py blob 7ad5051206abee0b22682598c850e2a390ce004d; tests tests/v3/test_candidate_metric_numeric_boundary_run481.py blob 26f5717f09352c7099b7134d0c4a0458a1ed1807. Wrap huge integer float conversion overflow in CandidateRunManifestError and reject numeric subclasses with coercion hooks. Validation-only; no real Candidate or GPU activity.

## Verified CI evidence and pending exact-head status at drafting

- Older PR #8 Run480 checkpoint c0b0d4f03f22ceb0bfa401a4373718a5207b1ab9: #1624 / run 41068640529 six-job SUCCESS.
- Corrected Memory chain source HEAD ad5d63f92000379990b7b0ecdab43380f2c65264: #1628 / 41075443485 six-job SUCCESS, not the latest Context/WAV head.
- PR #5 final source/test HEAD 21de6635404b9e277c363a5b795ca52006bcbe62: #1632 / 41076118914 six-job SUCCESS (Ubuntu/Windows Python 3.11–3.13).
- PR #8 latest four-package source/test HEAD 0ff1c5e9fd0e2412771c75c8797d6be757fab714: #1634 / 41076430525 IN PROGRESS when drafted; do NOT claim all six green.
- PR #8 #1625/#1626/#1627 FAILED during initial Memory syntax/import setup. A Ruff I001 import error and incorrect escaped regex/domain were corrected through ordinary GitHub Contents writes, preserving failure evidence. No bypass or force-push. Independent local whole-repo pytest/Ruff NOT VERIFIED because Git clone DNS was unavailable. No duplicate manual workflow launches.

## Frozen contracts, paid gates, remaining limitations

PR #5 and #8 remain Draft/unmerged. V1/V2/Local UI/Launcher frozen evidence, Memory v1 schema, protected V2 evaluation, V3 frozen Experiment 001, contamination/provenance/regression/reproducibility and human-review gates are unchanged. No paid APIs, external GPU, training, Candidate adapter/weight generation, protected evaluation opening, ToolBackend/OS execution, model promotion, new credentials, real data/media capture or main merge.

Next: confirm latest exact-HEAD PR #8 CI including Windows; make a minimal non-weakening correction only if necessary. Continue independently retained Memory/event witness research, actual revocation/trusted clock audit-before-action contracts, Planner UNKNOWN WRITE quarantine, Scheduler restart semantics and V3 free-only identity/approval checks. SQLite/local hashes do not prove independent writer custody.
