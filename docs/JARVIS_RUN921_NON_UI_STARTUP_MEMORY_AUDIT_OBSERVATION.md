# ARK AI Run921 — Four independent non-UI pre-access and continuity fixes

**Work basis:** `d282f05bd464aba41dedc82b64df099f77a8c939` on `research/jarvis-foundations` / Draft PR #8. **Complete source+test HEAD:** `c8c56834f83f9bece6115b2a589bc448f74556ee`. **ARK/JARVIS NOT_PASSED.** This document describes code/test changes, not target-PC or protected-model evaluation.

## A. Startup: no foreign dependency length callbacks

- Source [`5c9cc4e0`](https://github.com/Iam-2squared/ark-ai/commit/5c9cc4e0403fc3c3c23d782716a99e7b7a1309f7): `evaluate_startup_readiness` now checks `type(entry.dependencies) is tuple` **before** `len(entry.dependencies)` on a reflectively modified frozen `StartupComponent`. It also applies the per-component cap before summing graph edges. This prevents invoking untrusted `__len__` while constructing an inert readiness diagnostic.
- Tests [`759fb965`](https://github.com/Iam-2squared/ark-ai/commit/759fb965bcea49adc28559994932a2dc745464a4): four non-tuple/reflected traps, a 4,097-edge reflected tuple and a legitimate two-node readiness DAG. **Six cases authored**; CI result at latest HEAD is separately tracked.

## B. Memory: bounded AUTOINCREMENT high-water hydration

- Source [`411afc35`](https://github.com/Iam-2squared/ark-ai/commit/411afc353589e6807a0842fef3b19aa051fbdc6b): `_check_global_event_highwater` in read-only expiry preview now fetches **at most two** matching `sqlite_sequence` rows, sufficient to distinguish missing/single/duplicated markers without hydrating arbitrarily many forged duplicate metadata rows. The original compare against event-count/tail remains.
- Tests [`e906e6af`](https://github.com/Iam-2squared/ark-ai/commit/e906e6af01df1a264da20c99351476c6a54eaf16): empty and valid high-water, one/three/sixteen duplicates, non-integer sequence marker, event-id gap and traced `LIMIT 2`. **Eight cases authored**. Only disposable in-memory SQLite is exercised in authored tests. Never proof of source authenticity, deletion consent, or physical erasure.

## C. ActionAudit: reject hidden duplicate sequence markers in continuity witness

- Source [`96f118e1`](https://github.com/Iam-2squared/ark-ai/commit/96f118e116f02ebc0e2ebd9a9d837187edbf394c): the read-only continuity reviewer previously used `fetchone()` for a non-unique `sqlite_sequence.name` and could accept a forged second row when the first matched the audit tail. It now reads `LIMIT 2` and requires exactly one marker for nonempty histories, none for empty histories.
- Tests [`319dc60b`](https://github.com/Iam-2squared/ark-ai/commit/319dc60b9ebb1c6719deb5fe830b86465f1347bc): three second-marker values, two additional markers, and valid append/restart retained-prefix continuity. **Five cases authored** using disposable synthetic SQLite. A local high-water remains forgeable by anyone able to edit the same DB; it is **not** independent retention, human approval, or an external side-effect receipt.

## D. Observation: pinned raw-private-byte hasher

- Source [`bd6f6f55`](https://github.com/Iam-2squared/ark-ai/commit/bd6f6f55d84cbdf92f137d20510eef23104ea993): `make_disconnected_fixture` calls the import-pinned `_ORIGINAL_SHA256(payload)` rather than dynamically loading `hashlib.sha256` after metadata preflight. Its post-hash boundary check still refuses a changed module hasher. Neither camera, microphone, screen, network, external tool nor user-private ingestion is enabled.
- Tests [`c8c56834`](https://github.com/Iam-2squared/ark-ai/commit/c8c56834f83f9bece6115b2a589bc448f74556ee): a controlled reentrant hash replacement **after** preflight cannot receive the synthetic payload; a valid transcript fixture yields a content-only digest. **Two cases authored**. The callback fixture is a local test; this is not protection against a fully compromised interpreter.

## Test/evidence and preservation

**Total 4 source+test work packages; 21 new synthetic regression cases authored (6+8+5+2).** These are authored cases, **not** 21 proven PASS on the newest HEAD. Previous Run920 exact checkpoint `d282f05b` CI [#43891106990](https://github.com/Iam-2squared/ark-ai/actions/runs/43891106990) was **GREEN 6/6** (Windows/Ubuntu × Python 3.11–3.13) verified at this invocation's start. New source/test commits each trigger normal PR CI; no duplicate dispatch or assertion of latest-head GREEN. No full local ARK pytest, real GGUF, physical PC, model training or protected evaluation was run here.

**Frozen/blocked:** V1/V2/Local UI/Launcher contracts/evidence unchanged; protected V2 evaluation unopened; V3 PR #5 remains gated; UI PR #9 paused/unmodified; main untouched; PR #8 Draft/unmerged; no external/paid compute, new credential/account, automatic Candidate promotion, protected model testing, actual ToolBackend WRITE, new true once-only authorization, irreversible erasure, or automatic UNKNOWN replay. SQLite WAL/SHM interprocess last-close/alias fault and trusted-clock/PermissionGate persistence remain open.

## Next plan / 今後の方針

1. Verify the exact newest source/test/checkpoint CI across all six Windows/Ubuntu Python versions; if it fails, inspect the failing job and repair only via the permitted normal GitHub Contents path.
2. Continue bounded SQLite metadata audits and disposable WAL/SHM two-process fault isolation without deleting/retrying ambiguous work.
3. With verified lower-layer GREEN, strengthen Memory CAS/event continuity, Planner cold COMMIT-UNKNOWN, and inert Registry/PermissionGate/occurrence/audit/mock integration. Never equate local SQLite witnesses with cross-store atomicity or external effect confirmation.
4. Continue privacy-safe Personal Context/Observation/Proactive contracts, retain the V3 identity/reproducibility and approval gates, and keep UI work paused.
