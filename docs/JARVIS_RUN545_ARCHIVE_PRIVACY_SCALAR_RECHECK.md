# Run545 — Detached archive and privacy recheck integrity

This note records **fixture-only** changes on Draft PR #8. It is not a
JARVIS PASS claim, independent custody, external-effect proof, consent,
trusted-clock attestation, or authorization to replay a WRITE.

## Three independent source/test packages

1. **Detached batch cycle archive** — source commit
   `df3ec481699325a6f52133111eceee58c4e02b79`, test commit
   `6762b10c6baad9c88a84f75f3c9c2c493a97a495`:
   use field-carrier identity to detect equal-value receipt swaps during
   verification/creation; after the final read, pin both deterministic
   fixture receipts, the result fields, and all denial descriptors.
   Six newly authored fixture-only pytest cases, covering late source/result
   mutation, a False-valued descriptor replacement and a healthy roundtrip.
   The file is exclusive-create, not automatically deleted after uncertainty.

2. **Failure-aware batch archive** — source
   `9ed463e549a6d9d74c90e8adacfd90123da3c8a2`, tests
   `2034cee04d53cf0f43689aff8e46bba8539ea3de`:
   pin the original hypothetical failure receipt carriers across verifier,
   creation, witness-denial and final-read callbacks. A separately
   re-simulated receipt retains its own field identity epoch until return.
   Five authored cases. The failure mask is caller-supplied and does not
   authenticate an actual tool failure; no real dispatch occurs.

3. **Personal Context retention diagnostic** — source
   `25ae4a28878ef6fbf920171948bb4cc953b020f0`, tests
   `0c7ba914adc9a37809ff932e795832a98ea8075d`:
   compare four read-only retention inventory observations using independently
   materialized value epochs instead of patchable dataclass `__eq__`.
   Three adversarial stages plus false-equality liveness and safe, content-free
   review are covered by five authored cases. Retention review is *not*
   consent, actual erasure, or a deletion command.

**Total PR #8:** 16 new parameter-expanded pytest cases authored. Case
authorship is not independent local test PASS. Automated Actions must be
checked at the exact source/test HEAD before a GREEN claim.

## Boundaries and residual hazards

- Frozen V1/V2, Memory v1 and Planner contracts, Local UI/Launcher and
  protected evaluation remain unchanged. All changes are additive or local
  fail-closed verification adjustments in Draft PR #8.
- These tests exercise synthetic fixtures and locally constructed evidence.
  A local SHA or carrier identity is not authenticated provenance.
- No runtime ToolRegistry authorization, real ToolBackend, trusted clock,
  paid compute, hardware action, notification, privacy erasure, automatic
  replay, or main merge was performed.
- Independent cross-store atomicity and post-COMMIT ambiguous outcomes remain
  unresolved. Real-world side effects require a separate gate.

## Next plan / 今後の方針

1. Confirm exact-head Windows/Ubuntu Python 3.11–3.13 CI for these changes.
2. Diagnose any failed job from its log; prefer minimal safety-preserving fixes.
3. Continue Planner durable failure/READ journal integration and trusted-clock
   audit-before-action independently of in-flight archive tests.
4. Preserve unknown-WRITE quarantine and explicit approval gates.
