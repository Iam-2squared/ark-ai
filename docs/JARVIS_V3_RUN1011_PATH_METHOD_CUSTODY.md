# V3 Run1011 — local export path inspection dependency custody

**Work basis:** Draft PR #44 exact head c9e3457b7431c8b0fcd79140921a3a2b53e52137, whose exact-head CI run #6632 completed GREEN across all six Windows/Ubuntu × Python 3.11–3.13 jobs.

**Isolated branch:** research/v3-export-path-method-custody-run1011, proposed as a Draft child of PR #44. PR #5 remains protected Draft/unmerged.

## Change

The Run1008 export preflight admitted exact pathlib.Path instances and pinned the Path factory plus os.fsencode, but it did not pin the inspection methods used after admission. A class-level replacement of Path.lstat/resolve/is_dir/absolute/__fspath__, or a replacement of selected os/os.path primitives, could execute substituted code before the local path checks completed.

The preflight now checks an import-original method/primitive inventory before encoding or inspecting any supplied path:

- pathlib Path factory and concrete path type.
- Path __fspath__, absolute, exists, is_dir, is_relative_to, lstat, resolve, and path-shape descriptors.
- os.fsencode, os.fspath, os.lstat, os.stat, os.getcwd, and os.path identity.
- os.path abspath, join and realpath function identities.
- The captured method-name vectors and native path-byte limit.

If a pinned dependency changes, admission fails before the replaced callback is invoked. This remains a local process integrity check, not a Python sandbox or protection against arbitrary code that can rewrite all module/class globals.

## Regression coverage

The new V3 test parametrizes five Path method substitutions and eight os/os.path primitive substitutions. Each replacement records a callback and raises if called. The expected result is a fail-closed ValueError before any replacement callback executes. No filesystem mutation, converter, quantizer, model load, or export is performed by these tests.

## Boundaries and limits

Only export-plan path admission and synthetic tests are changed. No Candidate file/weight generation, training, export, model load, GPU, paid service, credentials, protected V2 evaluation, frozen contract, UI, PR #5, or main branch is touched. The existing TOCTOU boundary between path checks and later filesystem use remains explicit. V3 remains NOT_PASSED.

## Validation status

Source, tests and this note are saved on the isolated child branch. Exact-head CI is pending after the Draft PR is opened. No PASS is claimed.
