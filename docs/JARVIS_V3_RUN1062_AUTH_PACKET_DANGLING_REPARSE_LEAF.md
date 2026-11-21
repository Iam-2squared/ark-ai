# V3 Run1062 — reject dangling authorization-packet reparse leaves before create

## Finding

The review-packet writer checked the final output with `Path.exists()` and
`Path.is_symlink()`, then checked reparse-point ancestors. A dangling Windows
reparse-point leaf can report `exists() == False` while still being a directory
entry with `FILE_ATTRIBUTE_REPARSE_POINT`; it is not necessarily reported as a
POSIX-style symlink. The prior post-write `lstat` check was too late to prevent
the exclusive-create attempt from interacting with that leaf.

## Change

- Admit parent ancestry using no-follow metadata before any path-following
  existence/directory checks.
- Use final-leaf `lstat()` to distinguish a genuinely absent path from any
  existing entry, including dangling reparse points.
- Validate the pinned reparse metadata policy before denying an existing leaf.
- Preserve exclusive-create (`xb`) semantics and the post-write byte/identity
  verification. No approval, execution, training, or spend authority is added.

## Regression

A synthetic Windows reparse-point file leaf reports regular-file mode with
`st_file_attributes=0x400`, while `exists()` and `is_symlink()` are configured
to fail if consulted. The test requires rejection before `Path.open`.

## Limits

Synthetic filesystem metadata only; no junction is created and no privileged
Windows operation is used. This remains local path admission, not atomic
directory-handle custody or protection against concurrent owner-controlled
renames. No frozen V3 Contract, Candidate, protected V2 evaluation, real
training, external GPU, paid service, or main branch is changed.
