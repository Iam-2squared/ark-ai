# ARK AI Command Center: next-generation UI foundation

This UI is an additive frontend foundation. It does not replace the reviewed
Local UI, change an official milestone, or attest target-PC performance.

## Repository audit and branch boundary

Implementation starts from `main` at
`7a843f17eb96ed13d66f23b58b06406b3002e405`.
The audit inspected PR #8's `research/jarvis-foundations` snapshot at
`221a81db8548b0d25a52bee7da3bc2709a800b57` without merging it. PR #5's
`research/v3-learning-evaluation` remains separate. These branches continue to
evolve independently; the hashes identify what was inspected, not a claim about
their later heads.

| Area | Existing implementation | UI integration in this change |
| --- | --- | --- |
| Intelligence | `src/ark/intelligence/engine.py`: transactional `Intelligence.chat()` and `reset()`, V2 context budget/policy | Reuse through existing Local UI API; frontend never constructs inference history or system prompts |
| Local UI | `src/ark/ui/session.py` and `server.py`: one process/model/conversation, revision checks, display transcript, per-process request token | Import unchanged session/server/handler; replace only presentation assets in an additive runner |
| Memory | PR #8: `MemoryBackend` protocol and `SQLiteMemoryStore`, owner/namespace scope, source identity, revision, hashes and event history | Demo records only; no stable HTTP API exists on main |
| Planner | PR #8: `PlanGraph`, acyclic dependencies, revision-guarded states and `ready_steps()` | Demo DAG, step detail, failure/recovery illustrations; no worker dispatch |
| ToolRegistry | PR #8: immutable `ToolRegistry`, `ToolRegistration`, registry-bound action identity | Demo READ/WRITE registry and capability/scope detail; no tool execution |
| Permission layer | PR #8: `PermissionGate`, exact-scope grants and one-shot checks; explicitly not durable execution authority | UI approval previews confer no backend authorization |
| Action Audit | PR #8: `SQLiteActionAudit`, argument digests instead of raw arguments, schema/integrity checks | Demo audit examples only; no claim that an actual action was approved or executed |
| Vision/Voice | No corresponding main HTTP API | Unavailable; camera/microphone/screen acquisition is never requested |
| Telemetry | No CPU/GPU/RAM telemetry endpoint | Unavailable; no simulated numeric utilization displayed as measurements |

No frozen V1/V2/Local UI source, contract, evidence, evaluator, scorer or policy is
modified. The original `ark-ui` entrypoint and packaged assets retain their
behavior. Start one UI/model process at a time to avoid loading duplicate models.

## Technology decision

React + strict TypeScript + Vite provide reusable components, explicit data
contracts, isolated adapters, error boundaries and meaningful component/adapter
tests for seven growing screens. A static build avoids introducing a Node server
or cloud service into daily local use. No hosted inference, paid API, CDN,
telemetry or remote font is required.

| Option | Fit and tradeoff |
| --- | --- |
| Extend existing vanilla Local UI | Smallest dependency surface, but expanding frozen assets would couple new screens to reviewed evidence and increase regression risk |
| React + TypeScript + Vite, separate directory | Selected: maintainable screen/component boundaries and build-time type checking; introduces development dependencies and a larger static bundle |
| Full server-rendered framework / hosted app | Additional runtime/deployment and authentication complexity without value for a local desktop command center |
| Native shell such as Tauri/Electron | Possible later packaging layer; adds platform build/runtime work before backend contracts are ready |

The frontend is built in `frontend/`. The additive
`python -m ark.command_center` runner serves its compiled files and the existing
conversation API from the same loopback origin. The frontend's data adapters own
all fetch/protocol details; components use typed state. Demo state is in memory
and cannot mutate ARK's stores, policies or model configuration.

## Local startup

Run from the repository root with your existing Python environment. Dependency
installation requires connectivity; built app startup does not.

```bash
python -m pip install -e . --no-deps
cd frontend
npm ci
npm run build
cd ..
python -m ark.command_center --config config.toml
```

Open **http://127.0.0.1:8766**. Use the existing configured GGUF; this task does not
download or train models. No Node process is needed after the static build.
With an already installed Windows environment, the final command can be:

```powershell
.\.venv\Scripts\python.exe -m ark.command_center --config config.toml
```

For a deterministic protocol/integration demonstration without weights:

```bash
python -m ark.command_center --mock
```

This uses the real HTTP/session/V2 integration with the Echo backend, explicitly
identified as mock/no model. It is not real-model evidence. `--mock` cannot be
combined with `--config`. `--dist /absolute/path/to/frontend/dist` selects a built
directory when running outside the repository root. `--port 8767` selects another
loopback port. There is deliberately no public-host option.

Keep the terminal open. Ctrl+C stops the server; it is not a generation
cancellation protocol. The static asset snapshot is captured at startup, so
restart this runner after rebuilding frontend assets. The standalone browser
Demo adapter can be used to explore screens without an ARK backend; changing
adapters must never turn Demo records into live data.

## Existing API contract

| Endpoint | Request | Response / behavior |
| --- | --- | --- |
| `GET /api/status` | Same-origin read | Snapshot: state, revision, intelligence, model metadata, display messages, pending message, error/warning, dropped turns, logging and per-process token |
| `POST /api/chat` | Exactly `{ "message": string, "revision": integer }`, JSON, same-origin Origin and `X-ARK-Token` | `202 { "accepted": true }`; poll status for completion; no automatic write retry |
| `POST /api/reset` | Exactly `{ "revision": integer }`, same checks | `200 { "reset": true }`; resets V2 context and display history, not JSONL logs |

Only `loading`, `ready`, `generating` and `error` are backend session states.
Duplicate or stale writes return 409. There is one conversation shared across
tabs. Model information comes only from backend metadata; the frontend does not
infer successful load from a selected model name. `local_model: false` must stay
visibly marked mock. `local_model: true` identifies the configured local runtime,
not physical network disconnection.

The current backend returns completed responses, not tokens. The UI's message
structure allows future streaming events without pretending that polling is
streaming. Backend Stop/cancellation is unavailable. Reset and Send stay blocked
while generation is pending. A lost response must lead to a status refresh and
manual recovery, never an automatic resubmission that could duplicate work.

There are no Memory, Tool, approval, Agent, telemetry, media, training or Candidate
HTTP endpoints in this change. Unknown API paths fail closed with 404.

## Presentation server safety

`CommandCenterServer` subclasses the unchanged `LocalServer`. It retains its
127.0.0.1 bind, Host/origin checks, request token, body limits, JSON validation,
non-CORS behavior and response security headers. It inherits the existing API
POST implementation rather than duplicating permission-sensitive code.

Built assets are read into an immutable startup allowlist. Only `index.html`,
supported root presentation assets and supported files beneath `assets/` are
served. Symlinks are rejected; source maps, arbitrary JSON, source files and
unknown paths are not served. There is no filesystem or SPA-route fallback.
Hash-based client navigation keeps browser routes on the one HTML entrypoint.
The existing strict CSP is preserved; no inline script/style exception is added.

This remains a single-user local app. It must not be exposed through a public or
LAN proxy. No change relaxes the original Local UI's trust boundary.

## Verification and next integration

`tests/command_center/test_command_center_server.py` exercises real loopback sockets, startup
asset validation, source-map/path exclusion, snapshot semantics, the existing V2
chat/reset flow, stale revisions, origin/token checks and rejection of new write
capabilities. Existing frozen-evidence and Local UI tests remain applicable.
Frontend checks and browser screenshots are documented with the frontend.

For reproducible frontend-to-Python protocol verification, start a dedicated
`--mock` command-center process, then run from `frontend/`:

```bash
npm run test:local-api -- http://127.0.0.1:8766
```

The script transpiles the actual TypeScript local adapter/contracts into an OS
temporary directory, calls the real HTTP server, checks a Japanese Echo response,
verifies stale-revision 409 rejection, and resets only that verified mock session.
It rejects non-loopback URLs and refuses writes unless the backend reports the
exact Echo/mock identity with logging disabled. Server identity is checked again
before each write. Temporary compilation files are removed afterward. This
protocol check does not constitute real-model or physical-offline evidence.

The next safe backend integration is read-only, scoped contracts for memory
search/detail/events, plan/task snapshots, registry metadata and digest-only audit
views. Each should carry a schema version, provenance, freshness, bounded
pagination and explicit unavailable/error results. Real CPU/GPU/RAM measurements
need a separate telemetry adapter with timestamp/unit/source metadata. A missing
measurement must remain missing.

Mutation requires a later reviewed backend protocol binding exact scope,
revision, request identity and durable approval semantics. A visual confirmation
dialog by itself must never authorize Memory writes, Tool execution, Retry or
Cancel. Streaming/cancellation similarly needs an explicit generation identity,
terminal outcome and context/logging behavior before activation. Camera, screen
and microphone integration needs an independent explicit acquisition/stop/privacy
lifecycle. Training and Candidate promotion remain outside this UI task.
