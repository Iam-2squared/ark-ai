# ARK AI Run1017 — V3 export concrete Path type custody

**Work basis:** PR #52 exact head `16f321b322f35f32c2f33914f9ba88db4d3fa428`, branch `research/v3-export-path-method-custody-run1011`. Parent exact-head CI run [#44697363788](https://github.com/Iam-2squared/ark-ai/actions/runs/44697363788) completed GREEN 6/6. This is an isolated free-only child of Draft PR #52 / protected Draft PR #5.

## Finding

The path codec pinned the original `Path` factory and `__fspath__` descriptor but did not independently pin `_ORIGINAL_PATH_TYPE`. A rebound subclass can inherit the original `__fspath__` and inspection methods while overriding `__getattribute__`; changing the module's expected type to that subclass could therefore pass the descriptor comparisons and reach subclass attribute hooks.

## Change

Both codec and filesystem-inspection guards now require `_ORIGINAL_PATH_TYPE` to remain the concrete type returned by the import-original Path factory. This rejects a rebound subclass before `os.fsencode` or any caller-supplied Path attribute access. The no-follow/path-budget behavior and V3 frozen contract are unchanged.

## Regression and limits

One synthetic temporary-directory test rebinds the expected Path type to a subclass whose `parts` access raises. The guard must reject before that hook executes. The test is authored, not a local pytest PASS; exact-head six-job CI is required.

This is local path-admission hardening, not atomic directory-handle custody or a sandbox; filesystem TOCTOU remains explicit. No converter, quantizer, model load, training, Candidate, GPU, paid service, external compute, credentials, protected V2 evaluation, frozen-contract change, UI, PR #5 merge, or main merge is included. PR #5 and PR #52 remain Draft/unmerged.
