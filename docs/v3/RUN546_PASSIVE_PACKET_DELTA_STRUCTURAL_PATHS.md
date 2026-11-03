# Run546 — Unapproved V3 packet delta: unambiguous, bounded structural paths

**Scope:** passive local authorization-packet comparisons only. Neither this
change nor its test suite approves preflight, training, spending, Candidate,
protected V2 evaluation, promotion, a real model identity, or main merge.

## Change and regression coverage

- Normal GitHub Contents API source commit
  `42a99c4fa6a510ec71edd9b6b0c9d80ebb94a4d7` updates
  `src/ark/learning/authorization_packet_delta_review.py` without changing
  the frozen V3 Contract or any actual authorization gate.
- Test commit `04947a2602604ebb24c3739286c3a9f1f064b35c`
  introduces **12 parameter-expanded pytest cases** at
  `tests/v3/test_packet_delta_unambiguous_paths_run546.py`.
- GitHub Actions run
  [41385243347](https://github.com/Iam-2squared/ark-ai/actions/runs/41385243347)
  completed with **6/6 GREEN**, Windows and Ubuntu Python 3.11–3.13.
  This outcome certifies only its exact test commit, not a later note HEAD.

Before this change, flattening `{"a.b": 1}` and `{"a": {"b": 1}}`
could produce the same dotted field path; an empty dictionary or list produced
no leaf at all. That meant a structural change could be silently absent from a
field-name-only packet difference. Literal path delimiters now use an
unambiguous, deterministic escape scheme: `~` → `~0`, `.` → `~2`,
`[` → `~3`, `]` → `~4`. Ordinary dotted field paths retain their spelling.
Empty containers now have bounded, type-aware canonical leaves. The same
512-leaf and newly explicit 512-character path bounds fail closed.

These are **local diff semantics**, not verified provenance. SHA-256 digests
do not prove human approval, external byte custody, actual model or dataset
identity, billing controls, or that permission was granted. The V3 Draft PR
stays unmerged. No GPU, paid service, model download or Candidate generation
was started.

## Next

Continue passive fixture/path checks and independent snapshot provenance
review; do not open the frozen V2 suite or a full-training path without all
controlling independent approval gates.
