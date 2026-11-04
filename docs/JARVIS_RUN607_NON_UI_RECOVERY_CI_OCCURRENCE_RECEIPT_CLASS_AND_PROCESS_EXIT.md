# ARK AI — Run607: disconnected recovery CI and receipt-constructor custody

Work basis: Draft PR #8 `research/jarvis-foundations`, prior checkpoint
`516d8c5e36e871db7182bf072087507e76c4439d`.
This is isolated, reversible, local/mock-only non-UI work. No real ToolBackend,
paid/external compute, authenticated approval, physical device or private export.

## 1. Reconcile previous HEAD's actual CI failure

The prior checkpoint [CI #41833631243](https://github.com/Iam-2squared/ark-ai/actions/runs/41833631243)
completed **6/6 FAIL**. Ubuntu Python 3.12's actual job log showed
**8093 PASS, 1 SKIP, 2 FAIL**; Windows Python 3.12 showed
**8034 PASS, 60 SKIP, 2 FAIL**. Both failures were legacy test regexes in
`tests/test_disconnected_recovery_result_carriers_run470.py` that expected
late carrier-change diagnostics. Existing fail-closed
`_require_original_fence_denials()` now correctly rejects a forged review
class **before** invoking the replaced constructor, reporting
`mixed-plan authority descriptor changed`.

Commit `1bed4466125eae65040cf4a8ca5e5dc8122549b3` changed only the two
expected diagnostics. It did not relax the safety condition or change source.
[Repair CI #41840222702](https://github.com/Iam-2squared/ark-ai/actions/runs/41840222702)
had Ubuntu 3/3 and Windows Python 3.12 GREEN at the last read; remaining
Windows 3.11 and 3.13 still required completion evidence then.

## 2. Receipt result class identity before synthetic reservation

Previously, `durable_occurrence_review._assert_receipt_denials()` verified the
three original deny-only descriptors but did not verify that the exported
`SyntheticReservationReceipt` name still referred to its original class.
A forged class could copy all three original properties, pass descriptor
verification, and run a side-effecting replacement constructor **after**
the SQLite reservation COMMIT before result-type rejection.

Production source commit `4805a046c09d1a7de818505abdb93574b4fbe042`
also requires `SyntheticReservationReceipt is _RECEIPT_CLASS` in this existing
admission/callback integrity check. This covers preinstalled, token-digest
callback and post-COMMIT class-alias replacement without invoking the fake.
It does **not** assert that a post-COMMIT refusal rolled back the transaction.

New `tests/test_synthetic_reservation_receipt_class_custody_run607.py` at
`e2ae8d8d61006569b6d6d48da580de9cb860c5da` authors four synthetic
test cases: preinstalled counterfeit, token-hash-time counterfeit,
post-COMMIT counterfeit, and an ordinary deny-only receipt. They assert
the forged constructor is never called, the backend is never dispatched,
no premature reservation is committed, and a post-COMMIT reservation remains
consumed and unreplayable. **Four authored tests are NOT a local pytest PASS.**

## 3. Preserve the meaning of old post-COMMIT fault tests

Earlier legacy tests simulated post-COMMIT failure by replacing the receipt
constructor **before** admission. That is no longer a valid post-COMMIT fault:
the stronger guard must reject it before spending a token. Test commits
`8552bbd6d5f82a38311cb403e86590f3a62f5e1e` (five parameter cases)
and `0b68a7945a12eff0c4edf16c10378c1d9510ecdb` (three parameter cases)
now inject the forgery or denial-property replacement from the SQLite
COMMIT callback instead. They require the earlier guard to reject without
calling malicious constructors or getters and require the committed
one-shot reservation to remain used.

On [CI #41840972146](https://github.com/Iam-2squared/ark-ai/actions/runs/41840972146),
Ubuntu Python 3.12 completed with **8098 PASS, 1 SKIP, 1 FAIL** at the
last read. The sole failure was a separate real-process hard-exit test
still installing its fake constructor *before* admission. Test-only commit
`162fb9debf6b22c2adaf68a93acd5f5249167463` moves the simulated
`os._exit(43)` directly after the actual SQLite `conn.commit()`.
This preserves the intended process-crash durability check without
demanding execution of a forged result constructor.

## Validation scope and boundaries

- Branch/PR: Draft PR #8; no main merge. PR #5 and UI-paused Draft PR #9
  remain untouched. Frozen Memory/Planner/V3 contracts and V1/V2/Local
  UI/Launcher evidence are not modified.
- Local pytest was **not** run: the working container cannot resolve
  `github.com` for read-only source checkout. GitHub-hosted six-job CI
  on each exact HEAD is the validation source. Do not infer current-head
  6/6 GREEN from earlier successful runs.
- No synthetic receipt proves human consent, a real independent audit,
  trusted time, external outcome or exactly-once real-world execution.
  Post-COMMIT refusal is **unknown outcome** and never authorizes replay.
- Protected V2 final evaluation, real Candidate generation, V3 paid compute,
  secrets, external GPU, real tool dispatch, irreversible deletion and
  automatic promotion remain prohibited. **ARK/JARVIS/V3 NOT_PASSED.**

## Next plan / 今後の方針

1. Verify the exact CI on the final test-fix HEAD (Ubuntu/Windows,
   Python 3.11/3.12/3.13); read actual FAIL logs and fix narrowly if needed.
2. After exact-head GREEN, resume Memory generation-CAS COMMIT-UNKNOWN
   readback/retained row-event coherence and Planner restart quarantine
   in separate, reversible non-UI lanes.
3. Combine registry-bound mock identity, exact PermissionGate,
   audit-before-*mock*-action and occurrence replay safety only under
   proved lower-level gates; no real backend dispatch.
4. Continue Personal Context consent/revocation, proactive/observation
   fixture integrity and free-only V3 approval/path/identity review.
