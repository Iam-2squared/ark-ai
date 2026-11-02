# Run550 — Passive V3 packet-delta combining-mark display custody

**Scope:** Free-only, read-only review of *unapproved* authorization packet change paths on PR #5 (Draft/unmerged). No model bytes, actual review decisions, external execution, compute, Candidate or protected V2 scorer were accessed.

## New source and test evidence

- Source: `src/ark/learning/authorization_packet_delta_review.py` at source correction HEAD `8b269b49b330c818ee9c3dbab5b3f5af9c553375`. This extends the existing printable, unambiguous `~u{HEX}` field-component representation to Unicode **combining marks** (general category `M*`). They may otherwise be rendered as visually overlaid accents or marks, making two distinct review keys look equivalent. Existing ASCII-space and punctuation path conventions, empty-key encoding `~5`, and escaped literal `~0` are preserved.
- New regression tests: `tests/v3/test_packet_delta_combining_marks_run550.py` at commit `3020eb57750fef108ce7ada1de3f0984b5e94778`: **9 parameter-expanded authored cases** for six mark codepoints, composed vs decomposed spelling, literal-marker non-aliasing, nested path overlay, ordinary ASCII-space paths.
- First source iteration `97a0c329434dc1ecb05f89a6946775f4e8c9877d` used literal backslash-n instead of Python newlines inside its comment/condition. GitHub Actions [41402054693](https://github.com/Iam-2squared/ark-ai/actions/runs/41402054693) failed Ruff invalid-syntax / E501 on all six Python/OS jobs. The **semantics-preserving textual newline correction** is `8b269b49b330c818ee9c3dbab5b3f5af9c553375`; [41402446491](https://github.com/Iam-2squared/ark-ai/actions/runs/41402446491) **6/6 GREEN** independently inspected across Windows/Ubuntu Python 3.11, 3.12 and 3.13.
- New case count is authored/parameter-expanded test declarations, **not an independently run local pytest total**.

## Boundaries

Packet paths are display-only evidence, never authorization or certified human approval. Existing execution snapshot integrity gates, independently retained packet file hashes and strict local-file-only checks still control the V3 preflight package. No heavy dependencies, external GPU or API, frozen contract, V2 final evaluation, Candidate weights, auto-promotion, main merge, or spending is authorized by this change.

**Next:** Continue passive local identity/path/provenance guards only. Actual immutable model revision and byte identities, approved data and human review, pinned runtime/tool hashes, cost-cap evidence and explicit user authorization remain unresolved.
