# Run1049 — ActionAudit Windows reparse-point path admission rebase

**Work basis:** Draft PR #8 branch `research/jarvis-foundations`, exact parent HEAD `aa6e47284fbba6f45845274531defdeb5a974252` (Run1047 ToolRegistry custody integration). This child is based on that exact parent; fresh exact-head CI is required.

## Gap

The current ActionAudit path preflight rejected POSIX symlinks, non-directories, hardlinked database files and unsafe SQLite sidecars. It did not explicitly inspect Windows `FILE_ATTRIBUTE_REPARSE_POINT`. A junction or another reparse-point directory can report directory mode while `stat.S_ISLNK()` is false.

## Change

- Pin the import-time reparse-point attribute mask and policy.
- Recognize POSIX symlinks and Windows reparse-point attributes.
- Reject reparse-point ancestors, database leaves and SQLite WAL/SHM/rollback-journal sidecars before SQLite access.
- Use `lstat` for the database leaf rather than following it through `exists()` / `is_symlink()`.
- Preserve the existing path length, hardlink, orphan-sidecar and schema checks.
- Align sidecar diagnostic tests with the fixed path-free reparse denial while retaining metadata checks for ordinary directory/hardlink cases.

## Regression coverage

Synthetic stat fixtures cover reparse-point ancestors before parent creation, database leaves before SQLite open, sidecars before reopen and mutation of the pinned policy mask. The sidecar diagnostic regression distinguishes the fixed reparse refusal from ordinary alias metadata. No privileged junction is created.

## Evidence and limits

Previous PR #144 exact child head `30927ef65e12492f4e4a0566611fe35f1243b2da` passed CI #44857908057 (6/6), but it was based on older PR #8 head `784f93d7a48860e774f6d94648ff4e44297c9569`; that evidence does not transfer to this rebase.

These repeated local metadata checks are best-effort path admission, not atomic descriptor-relative custody, authenticated audit history or protection against hostile concurrent filesystem replacement. The v1 audit schema and event contract remain unchanged. No action, audit event, backend dispatch, paid service, external compute, Candidate, protected V2 evaluation, frozen contract, UI work or main merge is involved.

**Exact-head CI:** pending for this new branch; no local pytest/Ruff PASS is claimed. PR #8 remains Draft/unmerged. Overall ARK/JARVIS remains NOT_PASSED.
