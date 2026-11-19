# Run1001 — Windows reparse-point rejection in V3 local identity trees

**Work basis:** Draft PR #16 exact head `83364e3c60276a233c0c724f410b7e1898624abd`, itself a free-only child of gated Draft PR #5. This follow-up is isolated; PR #16 and PR #5 are not modified.

## Gap and hardening

Windows directory junctions are name-surrogate reparse points, but they are not necessarily reported by DirEntry.is_symlink() or stat.S_ISLNK(). Python's no-follow stat results expose Windows file attributes, including FILE_ATTRIBUTE_REPARSE_POINT.

The local identity traversal now:

- recognizes the reparse-point attribute in addition to POSIX symlink mode;
- rejects reparse-point ancestors during standalone file identity checks;
- rejects a reparse-point snapshot root or directory/file entry before adding it to the traversal stack; and
- retains the existing entry-count, UTF-8 path budget, file/directory epoch and no-follow checks.

A synthetic regression marks a normal fixture directory's no-follow DirEntry.stat result with the Windows reparse-point bit while leaving is_symlink() false. The traversal must reject it before calling scandir on that directory. No privileged Windows junction creation is required.

## Safety and limitations

This is local path-admission hardening only. It does not provide atomic directory-handle custody or prevent a hostile concurrent filesystem replacement after checks. It does not modify V3 Contract 1, open protected V2 evaluation, load models, start training, generate Candidates, promote artifacts, invoke paid services, or change PR #5.

**Validation:** source, synthetic test and report are authored; exact-head CI is pending. No PASS is claimed. PR #16 and PR #5 remain Draft/unmerged. Overall ARK/JARVIS remains NOT_PASSED.

## Reference

Python's os.stat(..., follow_symlinks=False) documentation describes Windows name-surrogate reparse points, including directory junctions, and the st_file_attributes field: https://docs.python.org/3.11/library/os.html#os.stat_result.
