# ARK Usability Infrastructure Contract

Status: **FROZEN BEFORE IMPLEMENTATION / TARGET-PC GATE REQUIRED**.
Base: Local UI v1 official freeze
`1617e94e46379969cdba8c70d6d1accf106d5985`.

## Boundaries

`ark-launch` is only a safe local launcher for the existing `ark-ui` server. It
does not duplicate inference, context, policy or model loading. It may reuse a
compatible ARK UI already listening on `127.0.0.1`, otherwise it starts exactly
one server on port 8765 or the fixed fallback 8766. It never binds publicly,
kills a process, downloads a model, requires a network connection or treats a
browser-open failure as a server failure.

`ark-gate local-ui` collects review material. It calls the existing V1 benchmark,
V2 fixed evaluation and comparison implementations without changing their
fixtures, scorer or policy. It never edits source, commits, uploads, merges,
replaces a model, suppresses a failure or declares an official PASS.

Each gate run uses a unique Git-ignored directory. Its identity is the repository
HEAD, configuration SHA-256, model SHA-256 and V2 suite/scorer/policy identities.
Resume is rejected when any identity changes. Files are created without
overwriting prior evidence and a SHA-256 manifest protects the final bundle.

Session collection is explicit. Candidate discovery is restricted to the run
window, parses UTF-8 JSONL and reports structure; it does not copy the newest log
or unrelated conversations. The user selects a candidate. Reset evidence requires
a Local UI start event, turns, recall, the exact reset event, and a post-reset
turn. Terminal mojibake never causes rewriting of an original.

Software observations and human attestations are separate. Physical network
disconnection, native IME behavior, visual state, Enter/Shift+Enter, buttons,
generation locking, Loading→Ready and refresh retention remain human evidence.
The strongest generated status is `READY_FOR_REVIEW`; otherwise it is
`INCOMPLETE`. Review and merge remain separate human-controlled decisions.

## Completion gate

- Launcher: validation, loopback-only start/reuse, fixed fallback, browser-open
  safety, duplicate avoidance, offline operation, tests, docs and CI.
- Gate runner: unique bundle, Git/environment/config/model identity, existing
  V1/V2/comparison integration, content-based session selection, reset validation,
  screenshots/checklist, separate attestations, stale rejection, resume support,
  report/manifest, failure preservation, tests, docs and CI.
- Target PC: real launcher, compatible-server reuse, port fallback, offline start,
  one real gate run, session selection, screenshot finalization and bundle review.

V1/V2/Local UI frozen evidence and V3 Draft PR #5 are outside this change.
