# ARK AI — Run725 non-UI Windows CI recovery and preaccess boundaries

**Work basis:** Draft PR #8, `research/jarvis-foundations` at `090fd13fb74f7d1a37699f388aead8e87d1d98bd` (Run724 checkpoint). **Report source/test basis:** `2de251b27e11295133257a5bd9d303fa1fe3b63f`. Everything here is local/free-only, disconnected and reversible. This is non-normative evidence; no frozen contract or PASS gate changed.

## A. Exact Run724 Windows CI failure repair

- [Run724 exact checkpoint CI #42537079024](https://github.com/Iam-2squared/ark-ai/actions/runs/42537079024) completed **FAIL**: Ubuntu Python 3.11/3.12/3.13 GREEN; Windows 3.11/3.12/3.13 FAIL. Actual logs show only two failing parameters on each Windows host: `test_named_file_metadata_change_after_read_is_rejected[st_mtime_ns/st_ctime_ns]`, `DID NOT RAISE ReadInputManifestRejected`.
- The test monkeypatched `Path.stat` but the native `WindowsPath` method may be a different override. [Fix `7f5b8f1`](https://github.com/Iam-2squared/ark-ai/commit/7f5b8f1f43ee70fc48c20c99bef604d610a960b6) uses `type(target).stat` to instrument the method actually called for the native filesystem path. The modified test still demands refusal of a late *same-size* named-file metadata change and does not loosen the production guard. Existing Windows same-source timestamp limitations and post-publish TOCTOU caveats remain.
- [First-fix CI #42541375640](https://github.com/Iam-2squared/ark-ai/actions/runs/42541375640) **still failed all three Windows jobs**, with the same two parameters; Ubuntu remained 3/3 GREEN. The native Windows symlink preflight can itself consume an extra named-stat observation, so choosing the second named call is not a portable marker for the post-read epoch. [Follow-up test-only fix `eaaf135f`](https://github.com/Iam-2squared/ark-ai/commit/eaaf135f253e42dddca5e37b5b49def4a5980d6f) observes the *second actual file-descriptor fstat after reading bytes* and injects named-stat drift only after that point. Its exact-head CI is pending. No production manifest integrity logic was weakened.

## B. Manual-only WRITE restart/triage privacy gate

- [Source `8157b565`](https://github.com/Iam-2squared/ark-ai/commit/8157b565d4a68c5aba5aeedb3a05997d66832fc4) pins import-original SHA-256, JSON encoder, and fixed digest domain in `offline_write_manual_triage`. A hostile replacement is rejected before the original WRITE step/carrier is inspected, and reentrant drift is checked after child recovery callbacks. The packet remains a **manual investigation checklist**, not an external-effect verification or approval.
- [Six synthetic cases `2b28e55d`](https://github.com/Iam-2squared/ark-ai/commit/2b28e55defa1cd51b8f58d10a8b301f04326474f) cover three preinstalled substitutions and three child-review rebindings. A throwaway local SQLite ledger only; zero ToolBackend dispatch.
- Real [intermediate CI #42541592623](https://github.com/Iam-2squared/ark-ai/actions/runs/42541592623) exposed **five Ubuntu failures**: two older tests expected a replaced digest callback to execute, while the newer earlier fence correctly refuses it; three new cases required an inner denial message whereas the public wrapper returns `local WRITE recovery validation denied`. [Existing-test correction `4504cc73`](https://github.com/Iam-2squared/ark-ai/commit/4504cc730e908b2cd397d48ac0725b2e8ac3e242) now requires **zero hostile callbacks**; [new-test diagnostic correction `8d6f78a2`](https://github.com/Iam-2squared/ark-ai/commit/8d6f78a2f4b2cf7cf3b9b694c07347f0a63a142b) preserves the requirement for a typed denial. Production safety fence unchanged.

## C. Personal Context revocation continuity

- [Source `1f379106`](https://github.com/Iam-2squared/ark-ai/commit/1f3791066c169102f72841d69cd3db9b5957874e) checks the original schema validation function `_validate` before opening/processing a synthetic private SQLite revocation snapshot. [Three synthetic cases `4a350ec7`](https://github.com/Iam-2squared/ark-ai/commit/4a350ec792846b349028d41b86c425935f45c0f9) cover preinstalled and reentrant substitutions with and without a retained witness.
- [Intermediate source/test CI #42541776479](https://github.com/Iam-2squared/ark-ai/actions/runs/42541776479) on Ubuntu 3.11 reported **11,345 PASS / 12 FAIL / 1 SKIP** on that older HEAD: five WRITE triage diagnostic/early-refusal regressions described above, and seven inherited revocation-test expectations whose injected schema callback is now rejected earlier. All seven were inspected against actual logs and changed to demand early rejection **without invoking the hostile callback** (source-path test [`a51850af`](https://github.com/Iam-2squared/ark-ai/commit/a51850af391380719a9645b4b1a66fe5e2dcba0e), witness ID [`3ac63db6`](https://github.com/Iam-2squared/ark-ai/commit/3ac63db6b23046cbe3ad64497fb19b5fa322cc38), revocation epochs [`730db6aa`](https://github.com/Iam-2squared/ark-ai/commit/730db6aacf2576107ad461ea34081304934e4f86), retained carrier [`54c16cd8`](https://github.com/Iam-2squared/ark-ai/commit/54c16cd853152b2a50e4f65c4ce49fb896a00fd3)). No privacy veto logic weakened, no user data inspected, no erasure/disclosure.

## D. Proactive SQLite witness privacy boundary

- [Source `6a6d0a06`](https://github.com/Iam-2squared/ark-ai/commit/6a6d0a067af9c5e5356c8102039b3a7487efd79e) pins the proactive history schema validator before SQLite reads. [Three synthetic regression cases `41649468`](https://github.com/Iam-2squared/ark-ai/commit/41649468cc1107dde62103c07f4a9d1d0ec2c704) exercise with/without retained witness and an injected path-resolution callback. No scheduled notification or real action is authorized.

- A proactive inherited schema-injection regression also expected late path retargeting. [Test correction `2de251b2`](https://github.com/Iam-2squared/ark-ai/commit/2de251b27e11295133257a5bd9d303fa1fe3b63f) instead requires the unreviewed callback to remain **uninvoked**, preserving private SQLite custody.

## Validation and known limits

- **New parameterized cases: 12** (WRITE 6 + Context revocation 3 + proactive 3), source modules changed: **3**, plus the exact Windows test fixture correction and **multiple inherited-test safety expectation corrections**.
- All new source/tests saved to Draft PR #8 through normal sequential GitHub Contents API writes; branch HEAD re-read before every write. **No local Ruff/pytest and no local Windows/PC verification.** Earlier-HEAD CI failures are real and documented. Latest source/test HEAD is not certified 6/6 GREEN; queued/IN PROGRESS workflows do not count as PASS.
- Local SHA, class/serializer identity, row hashes and SQLite witnesses are **not a secure Python sandbox, authenticated cross-store custody, trusted clock, human review, consent, real external READ/WRITE evidence or exactly-once side effects**. An uncertain WRITE is never automatically retried.
- All frozen V1/V2/Local UI/Launcher evidence and V3 Contract 1 remain unchanged. Protected final V2 evaluation, Candidate/weight generation, paid/external compute, new credentials, hardware action, destructive action, UI development, unauthorized main merge and Draft PR #5/#9 writes remain explicitly blocked.

## Prioritized next plan

1. Verify exact checkpoint-result HEAD Windows/Ubuntu × Python 3.11–3.13; use actual logs for any further correction, keep source-path packages independent from in-flight CI.
2. Strengthen Memory cross-scope event/CAS/ABA/COMMIT-UNKNOWN manual review while retaining independent-witness limitations.
3. Extend Planner durable READ manifest publication/independent retention and recovery journal evidence, never grant automatic replay from a local hash.
4. Review immutable Registry → exact-type PermissionGate → durable one-shot occurrence → audit-before-action → disconnected mock executor startup readiness only after exact-head GREEN.
5. Continue privacy revocation, proactive snapshot validation, fixture-only observation and free V3 identity/path/approval guards without opening protected gates.
