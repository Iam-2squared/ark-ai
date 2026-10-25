# ARK JARVIS Foundations — Run415: exact-carrier privacy, audit-link receipt, bounded startup DAG, observation rollover

**Scope:** disconnected, zero-cost, local/mock-only defensive review. This document is engineering evidence, not an execution authorization or PASS decision.

**Work-basis checkpoint:** `1e7ff06c976379073e1551ae65cc178e2a8f8eed` (Run414, CI #1026 / `40173274118` checked SUCCESS in six Ubuntu/Windows Python 3.11–3.13 jobs before these writes). Branch `research/jarvis-foundations`, PR #8 **Draft/unmerged**. PR #5 **Draft/unmerged/NOT_PASSED**.

## Four independent packages, 20 new parametrized pytest cases

| Package | Normal Contents source commit | Normal Contents fixture commit | Safety property | Fault injection |
| --- | --- | --- | --- | --- |
| Privacy fresh projection | `0e8cd5bcae8216132f92cb8aa38a3a04da16a42c` | `3082a4f9691cafc706aa509eadc980d901b53133` | Original request owner/text/namespaces, veto scopes and ContextSelectionPolicy field *carriers* persist across continuity and revocation callbacks | Equal-valued owner, query, policy-revision or scope string replacement fails before a private projection can be accepted; 5 cases |
| Audit-link receipt | `31ee1eda9e67b25ff6badc18be322435a3f70ab0` | `e9bae7c6b4922a54f32dd77bd0be89704e35817b` | Post-COMMIT diagnostic receipt must be exact-type, same original occurrence/event/link carriers; input/source remains pinned during receipt construction | Equal-valued occurrence/hash replacement, event-ID corruption, alien result, or ledger path rebinding all reject output; committed link is *not* rolled back; 6 cases |
| Startup DAG resource fences | `f43fceb7811b6f6e3eaee5d206bafaef4308e342` | `778301fe6cb31127fdbd87a822424dd5a4c9e055` | Max 10,000 nodes, 4,096 parents per component, 65,536 total edges across probe hydration and cached snapshot integrity | Oversized component, first over-budget generator element, forged cached snapshot and reflected dependency mutation reject; exactly 65,536 valid edges remain diagnostic-only; 5 cases |
| Observation rollover result custody | `1fdfcdb4f56171d003e01a53460aa8eccf2db7fd` | `7c9b94594f4fa3d03d0455c22ccd27737fab4441` | Constructing a new rollover witness cannot silently alter retained observation history or the previously checked privacy-scoped source | Equal-valued digest swap, window scope replacement, retained digest swap all reject; clean deterministic rollover accepted; 4 cases |

**Last implementation/test HEAD before this document:** `7c9b94594f4fa3d03d0455c22ccd27737fab4441`. These are commit IDs for specific normal GitHub Contents writes; they are not blob hashes, external runtime identities, or approvals. CI state and actual whole-suite count must be checked at the exact HEAD separately. No CI success is inferred from the ability to commit files. The prior confirmed Run414 exact-source suite had 2,284 passing tests; an additional 20 tests is *not* automatically a claim that 2,304 passed.

## Fail-shut semantics and review limitations

1. **Privacy:** Veto-marker absence is not consent. Memory and revocation are separate SQLite stores, and a second veto check does not supply an atomic read/consumption proof. Private context must not be exported, fed into a live model, shared with tools, or notified based on these diagnostics.
2. **Audit/Occurrence:** The synthetic reservation, pre-action audit and link SQLite transactions are independent. A successfully committed sidecar row is preserved even if a later Python constructor callback causes diagnostic denial; there is no inferred backend effect and no permission to retry an UNKNOWN/RUNNING/reserved-PENDING WRITE.
3. **Startup:** The thresholds bound direct fixture DAG work. A READY probe is caller-supplied and cannot authenticate clock, backend, user, device or physical PC state. A future integration must obtain separate readiness evidence and authorization.
4. **Observation:** All envelope and clock fields remain caller supplied. No cameras, microphone, screen readers, biometric analysis, notification pipeline, external identity attestation, sensor fetches or physical actions are invoked. Hashes demonstrate local consistency only.
5. **Adversarial boundary:** These equality/identity and reentrant-callback guards address reviewed local Python fixtures; they do **not** defend against an attacker controlling the interpreter, all private references, a filesystem swap, multi-store snapshot races or a compromised OS. No real-world exactly-once guarantee is claimed.

Frozen V1/V2/Local UI/Launcher and V3 Contract 1 evidence, V2 protected final evaluation, Memory v1 SQL and ActionAudit v1 SQL remain unchanged. No paid/external compute/API/GPU, new credentials, real Candidate or adapter, protected evaluation opening, promotion, irreversible operation or main merge was requested or performed.

## Next plan / 今後の方針

Check the exact implementation/test HEAD CI in six Ubuntu/Windows Python variants; inspect logs on failure and use only the ordinary Contents safety path for a minimal fix. Independently review multi-SQLite retained-prefix crash loss; Memory CAS/expiry/coherent snapshot races; privacy veto continuity and data minimization; trusted-clock/issuer interface without activation; and startup–scheduler–observation integration only after lower-level exact-HEAD GREEN. Keep both PR #5 and #8 Draft, with all live effects disabled.
