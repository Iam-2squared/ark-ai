# ARK AI Command Center

A desktop-first, local-first UI foundation with seven workspaces. React, strict
TypeScript and Vite produce a static bundle; Python serves the app and the
unchanged V2 conversation API from one loopback origin. This is a new UI preview,
not a replacement for the reviewed Local UI or a new official roadmap PASS.

## Build and run

Requires Node **22.13+** for development/build and the repository's existing
Python **3.11+** environment. No Node server is needed for normal use after build.

```bash
# From the repository root; preserve your existing llama-cpp installation.
python -m pip install -e . --no-deps
cd frontend
npm ci
npm run build
cd ..
python -m ark.command_center --config config.toml
```

Open **http://127.0.0.1:8766**. On Windows, the final command can be:

```powershell
.\.venv\Scripts\python.exe -m ark.command_center --config config.toml
```

Use the existing TOML and GGUF. Stop another ARK UI/model process first to avoid
loading the same model twice. Rebuild and restart the runner after changing UI
source; its built assets are captured once at startup. Install dependencies while
online; ordinary built-app startup needs no CDN, external font, paid API or API key.
Physical-offline inference has not been re-attested for this new UI.

For the real HTTP/V2 session with the deterministic Echo backend:

```bash
python -m ark.command_center --mock
```

This is visibly **MOCK · NO MODEL**, never real-model evidence. `--mock` and
`--config` cannot be combined. `--port 8767` changes the loopback port;
`--dist /absolute/path/to/frontend/dist` selects the build directory.
Use the exact printed `127.0.0.1` URL. There is no public/LAN binding option,
CORS exception or development proxy. Do not expose this single-user session.

## Development

```bash
cd frontend
npm ci
npm run dev
```

Development starts in **Demo**. The production build starts in **Local API**.
The top-bar source selector is explicit and disabled during a pending generation.
A failed local connection stays disconnected; it never falls back to demo data.
Local API mode on the standalone Vite server is intentionally unavailable. Build
and use the Python runner to test real same-origin integration.

| Workspace | Working behavior | Backend boundary |
| --- | --- | --- |
| Command Center | Runtime status/model, context metadata, current-session activity, alerts and navigation | CPU/GPU/RAM unavailable; no invented measurements |
| Conversation | History, safe basic Markdown/code, Japanese IME, Send, guarded Reset, manual draft recovery | Existing status/chat/reset API; completed responses via polling |
| Memory | Demo search, namespace filters, provenance/history, reviewed sample edit/delete | No real store or memory mutation |
| Agent Workspace | Demo tasks, dependency graph, step detail, failure/recovery/log inspector | Retry/Cancel previews do not dispatch workers or change plan state |
| Tools & Permissions | Demo READ/WRITE registry, scope/capability detail, approval rehearsal and audit/result examples | No capability is granted and no tool executes |
| Vision & Voice | Privacy indicator and demo observation examples | Camera, screen, microphone and voice playback controls disabled |
| Settings | Graphite/Deep Navy, English/Japanese, reduced motion; read-only runtime/logging/storage details | Browser appearance/language preferences only; no TOML edits |

Demo state is temporary and resets on mode changes/reopening its workspace.
Only appearance/language/motion preferences are saved in browser local storage.
Chat text and request tokens are not persisted by the frontend. Backend JSONL
logging follows the existing TOML configuration. Reset does not delete log files.

The backend currently has **no streaming or cancellation contract**. Local Stop
is disabled; Demo Stop only interrupts the in-memory demonstration. No hidden
reasoning, token streaming, OS resource measurement or offline attestation is
fabricated. Switching tabs does not create independent server conversations.

## Structure and verification

```text
src/components/       Shared panels, buttons, badges, dialogs, safe Markdown
src/screens/          Seven workspaces and interaction tests
src/data/contracts.ts Frozen Local UI wire types and runtime validation
src/data/local.ts     Same-origin status/chat/reset transport only
src/data/demo.ts      Isolated in-memory demonstration
src/data/useArk.ts    Serialized polling, revision/token checks, mutation guard
scripts/              Mock-only real HTTP adapter smoke check
```

```bash
npm run typecheck
npm run lint
npm test
npm run build
# With a dedicated Python --mock runner already started:
npm run test:local-api -- http://127.0.0.1:8766
```

The smoke check refuses real-model sessions and non-loopback origins. It uses
the actual TypeScript adapter against the real Python API, including Japanese
Echo chat, stale revision rejection and Reset. Existing Python/Local UI tests
remain unchanged and run alongside new runner security tests.

Dialogs use native modal focus containment; the mobile drawer confines keyboard
focus and hides the underlying workspace while open. Navigation has a skip link,
current-page indication and English/Japanese labels. Motion respects system and
browser preference. Markdown deliberately supports paragraphs, headings, lists,
bold, inline code and fenced code without raw HTML or executable links.

See [architecture and backend audit](../docs/NEXT_UI_ARCHITECTURE.md),
[verification and screenshots](../docs/next-ui/README.md) and the root README.
The next integration phase is scoped read-only Memory/Planner/Registry/Audit
contracts. Real mutations, durable approvals, streaming/cancel and media capture
each need a separately reviewed backend lifecycle before enabling UI controls.
