# ARK AI Run720 — Three independent FREE-ONLY non-UI core packages

**Work basis:** PR #8 (`research/jarvis-foundations`), initial HEAD `8794bd1e26d6ea7d22114b8a1101b0bdd0037ab1`. No changes to main, protected PR #5, paused UI PR #9, or frozen V1/V2/Local UI/Launcher contracts and evidence. This is *not* a JARVIS or V3 PASS.

## A. Detached Planner READ input manifest: POSIX directory-entry durability

- [Source `a36975a`](https://github.com/Iam-2squared/ark-ai/commit/a36975aadc49835aebaab77341abe7601051d44b) retains the existing exclusive `O_EXCL`, bounded canonical JSON, file `fsync`, no-overwrite and caller-supplied retained hash semantics, then synchronizes the containing directory on POSIX. Parent must be a real directory and `O_NOFOLLOW` is requested where available. A failure leaves the already-created file *untouched* and raises a deny-only exception; the caller must treat publication durability as **UNKNOWN**, manually inspect and never auto-retry.
- [Two POSIX-specific regressions `940a5e2`](https://github.com/Iam-2squared/ark-ai/commit/940a5e2ed87ada549577976a412c89bc0589a430) assert file-then-directory synchronization and injected parent-`fsync` failure retaining the un-overwritten artifact. Tests are intentionally skipped on non-POSIX; there is **no equivalent Windows power-loss guarantee** from this path.
- Scope: directory sync is *not* independent authentication or cross-file/SQLite atomicity. A returned digest does not establish backend READ, consent, privacy authority or external effects.

## B. Memory generation-fenced CAS: full AUTOINCREMENT marker-set validation

- [Source `e52508b`](https://github.com/Iam-2squared/ark-ai/commit/e52508b8b5182a919d0918a908526a2d784275ab) replaces a `sqlite_sequence` `fetchone()` with a same-transaction **complete marker-set scan** in the existing generation observation/write snapshot. The previously accepted valid-looking first marker could conceal a second forged `memory_events` high-water record; `sqlite_sequence.name` is not UNIQUE. An empty event stream requires no marker; a nonempty stream requires exactly one valid marker matching dense event IDs.
- [Four new synthetic cases `b8e1404`](https://github.com/Iam-2squared/ark-ai/commit/b8e1404eaaf4ee8a877c5b4de96e36d849503cd2) exercise three forged-duplicate values against both read observation and atomic CAS (no appended event or changed row), plus a valid unrelated-owner append that must remain allowed.
- Scope: local SQLite high-water is editable; this cannot authenticate writers, provide independent historical custody, consent, or a trusted clock. Existing COMMIT-UNKNOWN/manual-review rule remains.

## C. Offline PNG scanline fixtures: protect private IDAT from swapped codec/getters

- [Source `2a4a60e`](https://github.com/Iam-2squared/ark-ai/commit/2a4a60e22a62cb317d0a1f55173c3e41b941d959) pins the import-original SHA-256, zlib decompressor and request class/slot/lookup descriptors before the first compressed-byte access and across digest/decode and detached re-verification. It makes no camera, consent, computer-vision, or external-tool claim.
- [Seven synthetic regressions `9deb5c8`](https://github.com/Iam-2squared/ark-ai/commit/9deb5c814bf404f24f07dd9c875af7693aadcc61) cover original codec substitutions on inspect/verify and three malicious class getters; the test fixture byte literal was corrected in [`5d464f9`](https://github.com/Iam-2squared/ark-ai/commit/5d464f9ef26ce996950756e91f2b7dd897429ba9).
- [Inherited regression adjustment `de42711`](https://github.com/Iam-2squared/ark-ai/commit/de4271181606662a4daafa73585613e01db16f51) now requires the adversarial decompressor **never be called** rather than waiting for its later reflected mutation. No safety check was removed.
- Scope: in-process import-original identity pins are not hardware isolation, remote attestation, authenticated data custody or capture-source proof.

## Verification and next dependencies

The three coherent packages add **13 authored parameter-expanded synthetic cases** (2 + 4 + 7), plus one strengthened inherited test. **No full local pytest/Ruff, physical GGUF or Windows hardware run** was executed here. The inherited [Run719 exact checkpoint CI #42514293638](https://github.com/Iam-2squared/ark-ai/actions/runs/42514293638) was still running while these independent paths were edited, and later completed **6/6 GREEN on the *older* `8794bd1` HEAD**. It cannot certify Run720.

GitHub Actions CI was automatically started on each ordinary Contents API commit; do not launch a duplicate workflow. Final package-code HEAD before this report is `de4271181606662a4daafa73585613e01db16f51`. [Its CI #42516546745](https://github.com/Iam-2squared/ark-ai/actions/runs/42516546745) was **QUEUED** when last read. Every intermediate and report/checkpoint HEAD has an independent CI identity: none may inherit prior-head GREEN. Continue working on independent lanes while CI runs. On any failure inspect actual job logs and fix only what they demonstrate.

## Hard boundaries

Only zero-cost disconnected/mock/local logic and disposable synthetic tests. **No paid service/external GPU/API, Candidate adapter or weights, real private data, real tool dispatch, trusted authorization, protected final V2 evaluation, human review fabrication, destructive migration, credential connection, physical PC action or main merge.** PR #5 remains Draft/unmerged under Contract 1; PR #9 remains Draft/unmerged and untouched under the UI pause. ARK/JARVIS/V3 remain **NOT_PASSED**.

**Prioritized next:** exact-HEAD CI triage; retained Memory row/event commitments and manual COMMIT-UNKNOWN adjudication; Planner write-once manifest custody on Windows and crash-stage verification; independently scoped durable one-shot PermissionGate + trusted-clock audit-before-action + disconnected mock executor; privacy-safe Personal Context/proactive state; free-only V3 guard review. Do not integrate until dependency exact-head GREEN.
