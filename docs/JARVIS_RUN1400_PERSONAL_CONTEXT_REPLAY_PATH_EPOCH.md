# Run1400 — Personal Context replay path-policy epoch custody

## Exact basis

- Parent: Draft PR #8, branch \`research/jarvis-foundations\`.
- Exact parent work-basis HEAD when this child branch was created: \`a1bff14b0ca731ee1d094d6611caf76c08640398\` (after the exact-head-green Memory path-policy package from PR #574 was integrated).
- Child branch: \`research/run1422-context-replay-path-epoch-20261126\`.
- Child HEAD before this evidence document: \`711b4eed783b3c46b78dc570b65075a739db7b6a\`.
- Source blob: \`e94e5dd70c4f48457df0bab77c891105a776a28e\`.
- Regression-test blob: \`452282647f21b140692189df09c4953046f974b2\`.

## Finding and correction

The disconnected Personal Context replay ledger checked its SQLite path with live \`stat.S_ISDIR\`, \`stat.S_ISLNK\` and \`stat.S_ISREG\` bindings but did not retain a complete import-time path-policy epoch. It also did not reject Windows reparse-point metadata on ancestors, the database leaf or SQLite sidecars, and path callbacks were not consistently followed by a policy recheck before reading metadata.

The path preflight now retains the original \`os.fsencode\` and \`stat\` module/predicate inventory, maximum path budget, reparse attribute and reparse classifier as one tuple captured by a keyword-only verifier default. It uses the retained classifiers and rechecks policy after \`lstat\`, metadata access and path construction. Reparse-point ancestors, database files and sidecars are denied before SQLite access.

## Regression coverage

- Joint replacement of the stat module, mode predicates, reparse mask/helper and aggregate epoch is denied before \`Path.lstat\`.
- A replacement installed reentrantly by an ancestor \`lstat\` callback is denied before \`st_mode\` is read.
- Synthetic Windows reparse metadata is rejected for an ancestor, database leaf and SQLite sidecar.
- A reentrant \`st_file_attributes\` accessor cannot replace the path policy and then return a seemingly safe value.

## Scope and evidence limits

Only synthetic temporary paths and metadata are used. Personal Context replay DDL, row format, hash-chain domain, request binding, CAS reservation, retention and public APIs are unchanged. The ledger remains hash-only and denial-only: it does not prove consent, revocation freshness, context disclosure permission, trusted time, independent custody, atomic directory-handle custody, physical erasure or exactly-once external effects. Repeated pathname checks are not a sandbox or protection against hostile concurrent filesystem renames.

No live personal data, external context, real ToolBackend dispatch, notification, credentials, hardware, paid/external compute, Candidate generation/promotion, protected V2 evaluation, frozen-contract change, main write/merge or UI/frontend work occurred. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. Fresh exact-head CI is required; no PASS is claimed.
