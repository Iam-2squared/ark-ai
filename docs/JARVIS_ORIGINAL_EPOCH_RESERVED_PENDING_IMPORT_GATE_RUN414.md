# ARK JARVIS foundations — write-source custody, Memory ingress and replay-safe offline boundary (Run414)

**Evidence class:** disconnected, local-fixture engineering note for Draft PR #8; never an authenticated approval, clock attestation, external outcome proof, real execution PASS or permission to dispatch. No frozen schema/contract or main change. All work uses the ordinary GitHub Contents path and existing CI only; no paid/external compute.

## Exact work basis and coherent packages

Work started at **Run413 canonical** `0f9c923117cc56d77dcc5cde47a73b63b37ed57b` (CI **#1014 / 40171243516 SUCCESS all six**). These packages add **30 parametrized pytest cases** to the prior 2245-case baseline. The last 11 safety-import cases require their own exact-head run before treating 2275 as confirmed.

| Work package | Source/write SHA(s) | Test SHA(s) | Correctness boundary |
| --- | --- | --- | --- |
| Synthetic Audit Link append custody (+10) | `6ae4cbf7537ab4fe88e914b7ce204fd1716d0d1f` | `5e73d00b3da3dbba243845f9db24788e51d59bc5`; test readback-only correction `0e6c5ac1b481e4b28ccb3f5659c0b82db95e2721` | Pin original link/reservation/audit sources and original call/reservation/event/retained witness carriers before any registry bind, hash, SQLite read or append; check at each transaction phase and after COMMIT. No external ToolBackend. |
| Memory multi-namespace early ingress (+5) | `6a13adbc132f231695d5d9cb438cc7a8ccfefb38` | `a06f93fbfd99b73159ad821a859637819d5a09b2` | Pin initial Memory Path, owner and namespace **before** constructing copied MemoryScopes and computing each scope digest. Reject mutation/restoration between two digest callbacks. No Memory v1 SQL/schema edits. |
| Four-store reserved-PENDING crash prefix (+4) | Existing unchanged recovery implementation | `0b2198ded348014509c0309b0af6150b1495e1b6` | Local PENDING root WRITE already has an occurrence, pre-action audit and link; an independent RUNNING WRITE cannot resolve it or unblock its transitive WRITE dependent. Each separately cloned four-store DB loses one row in turn, and retained evidence must reject it. Original SQLite fixture preserved; zero backend calls. |
| Direct external import gate (+11) | Existing disconnected modules unchanged | `7be562f0f787a4b38aa734ea328ee2ffa82678a3` | AST guard on 10 explicitly scoped pure review modules against direct imports of external networking, paid API/GPU and hardware interfaces; plus guard that target files exist. **Narrow syntax test**, not sandbox, transitive-import proof or global billing guarantee. |

## Specific phase fault matrix

| Attack / failure | Expected response |
| --- | --- |
| Audit-link `_connect` returns a connection but swaps link/ledger/audit source to an equal-valued new Path | Refuse original epoch and close handle, no link append. |
| Sidecar BEGIN callback retargets link path | Reject *before* sidecar replay/insert. |
| Pre-action digest, reservation schema callback or audit `events()` callback substitutes original receipt/event carriers | Reject even if field values compare equal; no synthetic link receipt. |
| Retained link-witness tail digest rebound by sidecar replay callback | Reject, preserving caller-retained history. |
| Sidecar COMMIT succeeds, then callback retargets original audit path | Return rejection, but **do not erase the committed link**. Caller must retain/re-read durable evidence rather than retry. |
| Memory `_scope_digest` callback mutates the original MemoryScope or source Path | Stop at the *first* hash, before a second callback could restore the original identity. |
| MemoryScope constructor callback retargets original owner during copy | Refuse prior to any hash; never review another owner under initial scope. |
| Reserved-PENDING has a pre-action receipt and an independent RUNNING marker | Both held UNKNOWN/uncertain; dependent WRITE held through READ bridge; no replay. |
| Clone separately loses a Planner, Occurrence, ActionAudit or audit-link row | Separately retained cross-store evidence detects lost prefix; no backend invocation. |
| Future synthetic reviewer directly imports named external API/GPU/network/hardware entry points | AST CI test fails. Dynamic/transitive use is **not** covered. |

## Verification provenance (time-local, exact-head only)

- Initial **#1018 / 40172255311** test HEAD failed: the write-path test left an attack hook installed for its own post-rejection readback, which correctly triggered the read-only source fence. This was a *test harness* error, not permission weakening. Narrow normal Contents correction `0e6c5ac1b481e4b28ccb3f5659c0b82db95e2721` restores the benign connector for the durability assertion. Preserve the original FAIL evidence.
- Post-correction **#1020 / 40172359979** at `0b2198ded348014509c0309b0af6150b1495e1b6`: Ubuntu 3.13 reported **Ruff All checks passed and 2264 pytest passed in 52.27s**; all Ubuntu jobs GREEN, Windows outcomes must be individually checked. This is the **three-package** source/test HEAD, not the last import-guard HEAD.
- **#1021 / 40172594181** at exact four-package HEAD `7be562f0f787a4b38aa734ea328ee2ffa82678a3`: in progress at initial engineering write. No all-six GREEN or 2275 passed claim is made until its own jobs/logs are checked.
- Exact nontruncated Git Trees at four-package HEAD against unchanged `main` `7a843f17eb96ed13d66f23b58b06406b3002e405`: **94 main blobs, 473 branch blobs, 379 added, zero main-existing modified, zero deleted**. This engineering note/checkpoint will be branch-exclusive.

## Limits, ownership and next plan

- The source epoch checks cannot pin filesystem inodes, signed disk contents, malicious process-local monkeypatches or a shared SQLite snapshot. A sidecar audit link is not a verified external effect; post-COMMIT failure can leave durable link state.
- The static import guard only inspects direct imports in listed modules. It cannot prevent dynamic imports, network access through a transitive dependency or all future code paths. Future integration needs enforceable runtime/network/credential controls and independently verified results.
- Continue exact-head six-environment CI and narrow regressions first; preserve failures. Next: strengthen sidecar ledger read-only source/row provenance and retained multi-write history; Memory CAS/expiry and privacy veto; clock/issuer diagnostics; observation/scheduler contracts, all disconnected.
- Frozen V1/V2/Local UI/Launcher evidence, V3 Contract 1 and evaluation gates, Memory v1 and ActionAudit v1 SQL schemas remain unchanged. **PR #5 Draft/unmerged/NOT_PASSED**, **PR #8 Draft/unmerged**, main unmerged. No preflight/full paid GPU, Candidate weights, protected V2 evaluation, secrets/account connections, live ToolBackend, real notification/sensor, user-data export/erasure, or approval/authorization escalation.

**Required before any real autonomous WRITE:** authenticated human issuer/consent, trusted timestamp provenance, atomically custodied authorization/occurrence, verified real ToolBackend receipts and recovery semantics, device/privacy controls, exact-head integration GREEN and explicit user approval at the applicable gates. None is established by this note.
