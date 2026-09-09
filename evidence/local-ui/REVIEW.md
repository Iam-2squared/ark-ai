# Local UI v1 Final Evidence — reviewed PASS

Target date: 2026-09-09 JST. Tested source: `1f4b197605fae6f9a1be8d47072122c6f3154e94`.
V1/V2 official freeze: `7e46a4529879243b4a5bd52bb6575d11c1ec0183` /
`6195beec55a2f97f68c53a1fef890f1f1422d6f1`. This evidence-only change does not
alter the UI runtime, V1/V2 evidence, Intelligence, model code, configuration,
policy, suite or scorers. PR #6's merge commit is the Local UI v1 freeze point.

## Decision

**Local UI v1: reviewed PASS; OFFICIAL PASS upon green final-head CI and PR #6 merge.**
The submitted originals and explicit target-PC observations satisfy the pre-existing
`docs/LOCAL_UI.md` contract. Real-model behavior is target evidence; CI uses mocks.

| Gate | Evidence | Result |
| --- | --- | --- |
| Loopback UI and model lifecycle | New process at 127.0.0.1; Loading → Ready; one model reused; occupied port failed safely | PASS, observed |
| Local V2/Qwen connection | Screenshot shows ARK V2, LOCAL MODEL, Qwen3-4B GGUF, Q4_K_M and Local JSONL | PASS |
| Japanese and multi-turn | Online/offline logs and screenshot show coherent Japanese and 青いりんご recall | PASS |
| Reset/context isolation | Exact reset events plus post-reset `未指定`; screenshot has no prior transcript | PASS |
| Browser controls | Chrome: IME confirmation does not send; Enter/Send work; Shift+Enter newline; generating disables Send/reset; reload preserves conversation | PASS, user-observed + deterministic client tests |
| Errors | Missing config screenshot shows Needs attention, disabled input/reset and LOCAL UI rather than LOCAL MODEL; port conflict reported clearly | PASS |
| Physical offline cold start | User disconnected networking, started a new UI process on 127.0.0.1:8766 and completed Japanese inference/recall/reset | PASS, user attestation + logs |
| V1 regression | Real backend, correct model SHA, startup true, six successes, zero failures | PASS |
| V2 regression | Frozen 12 cases: 11/12, runtime failures 0; only math-02 format FAIL retained | PASS, baseline preserved |
| Comparison | compatible/controlled true, no regressions, every domain delta zero | PASS |

## Target and provenance

Windows 11 10.0.26200, Intel 8th-generation Core i5 class, 16 GiB RAM,
CPU-only, Python 3.12.10, llama-cpp-python 0.3.35, Chrome 152.0.7977.83.
Qwen3-4B-Instruct-2507 Q4_K_M, 2,497,280,736 bytes; weight SHA-256
`2fde00ce69dd4899c70d020845e2638353015bba0fdf161b3eb965f2bca4464e`.
The user reported branch `feature/local-ui`, the exact tested source SHA above,
and no tracked source changes; the only status item was an untracked evidence-upload
folder. This is user attestation, not signed process provenance.

The first offline log proves a new local session and Japanese output. The later
offline-reset log is valid UTF-8 (PowerShell display decoding caused the reported
mojibake) and contains start → passphrase setup → recall → exact reset event →
post-reset question → exact `未指定`. Physical disconnection itself is not
automatically proven by localhost, `LOCAL MODEL`, or model output.

Three PNG originals were directly reviewed. They show the expected ready/recall,
post-reset and missing-config states. They include unrelated browser chrome/taskbar
details, so they are not duplicated into the public repository; immutable hashes,
dimensions and findings are recorded in `manifest.json`. Only designated test logs
are published. Reattached duplicate files were not counted as additional runs.

The V2 regression was re-scored with the frozen scorer. `math-02` answered
`3/4 + 1/8 = 7/8`; arithmetic is correct but the answer violates the numeric-only
format. It remains FAIL. The submitted comparison exactly reproduced comparison
against frozen `evidence/v2/raw/v2-real-1.json`. No fixture, scorer or policy change.

## Limits

This review establishes the Local UI v1 integration/completion gate, not broader
model quality, automatic network-state detection, authentication for other local
users, streaming, long-term memory or V3 learning. `LOCAL MODEL` identifies the
loaded local backend only. V3 Draft PR #5 remains independent and unmerged.
