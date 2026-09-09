# ARK Local UI v1

Status: **REVIEWED PASS / OFFICIAL UPON PR #6 MERGE**.
Branch: `feature/local-ui`, based on main at
`6195beec55a2f97f68c53a1fef890f1f1422d6f1` (V2 official freeze).
V1 freeze remains `7e46a4529879243b4a5bd52bb6575d11c1ec0183`.
V3 Draft PR #5 and its branch are not part of this change.

## Architecture and behavior

Browser → local HTTP adapter → existing `Intelligence.chat()` / `reset()` →
existing model backend. `load_config()` and `local_engine()` are reused directly.
V1/V2 source, fixed fixtures, scorer, policy, configuration semantics and frozen
evidence are unchanged. No training, model download or weight update is added.

- `ark-ui --config config.toml` binds **127.0.0.1 only**, default port 8765.
  `--port 8766` selects another loopback port. There is no public-bind option.
- A background worker loads one model after the HTTP listener starts. Loading
  and load failures are available in the UI. The same model instance serves all
  turns. Restart the server after fixing a configuration/model load error.
- One server process owns one conversation. Tabs share that conversation;
  refreshing a tab retrieves its current display history. There are no accounts
  or independent tab sessions. Closing a tab does not stop the server.
- Only `Intelligence` owns inference context. The adapter's display transcript
  contains up to 100 successful turns and is never fed back into the model.
  V2 may truncate older complete turns from inference context before the visible
  transcript is trimmed. The UI reports when this happens.
- UI requests send a message and a conversation revision, never system prompts,
  roles, history or generation controls. V2's existing default **concise** policy
  applies. No per-model prompt or capability inference is added.
- One generation at a time; both client and server block duplicate sends and
  reset during generation. Stale tabs receive a conflict and refresh state.
- Responses appear when V2 completes a successful turn. This version does not
  stream partial answers or expose hidden reasoning. No automatic write retry.
- **Reset conversation** calls V2 reset and clears the display transcript.
  It does not delete existing JSONL logs. Slash commands typed in the message box
  are ordinary model input; use the reset button. Ctrl+C stops the server.
- Errors are rendered as text. A failed generation preserves the previous V2
  context. On a logging failure after generation, the committed answer stays
  visible and new writes stop until restart; it is not silently discarded.
- Real sessions use the existing configured JSONL logger, including start,
  user/assistant, error and reset events. `logs/` remains Git-ignored. The process
  does not persist or automatically restore conversation context after restart.
  Shutdown is not a generation-cancellation protocol; wait for a response before
  Ctrl+C when preserving the final turn's log matters.

`src/ark/ui` uses Python's standard library, vanilla JS/CSS and an original SVG
mark. No added Python runtime dependency; Node.js is used only by developer/CI
client tests. No CDN, remote fonts, telemetry, API keys or remote inference calls.
HTML/CSS/JS are shipped in the Python wheel and served from a fixed asset allowlist.

Same-origin/Host checks, a per-process request token, body limits and CSP protect
the loopback API against cross-site browser requests and injected HTML. It is a
single-user local application, not an authenticated service for other users on
the PC. Do not proxy or expose it to a LAN/cloud. Open the printed **127.0.0.1**
URL; `localhost` is intentionally not an accepted Host alias.

`LOCAL MODEL` means the configured llama-cpp inference path is loaded. It is **not**
an automatic claim that Wi-Fi/Ethernet is disconnected. `--mock` explicitly shows
`MOCK · NO MODEL`; it uses Echo and cannot demonstrate real-model ability. `--mock`
cannot be combined with `--config`.

## Windows: install and start

Use the existing Python 3.12 `.venv`, native llama-cpp-python 0.3.35, configuration
and Qwen GGUF. No model/runtime re-download is needed. Run the install while online;
pip may need build tooling. Normal application startup afterward needs no network.

```powershell
Set-Location 'C:\Users\Owner\Desktop\Git Ark\ark-ai'
git status --short
```

If tracked/untracked work is shown, preserve it before switching; do not run
`git reset --hard` or `git clean`. Ignored GGUF/config/logs/venvs are retained.

```powershell
git fetch origin
git switch feature/local-ui
git pull --ff-only origin feature/local-ui
git rev-parse HEAD
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
.\.venv\Scripts\ark-ui.exe --config config.toml
```

When the branch does not exist locally, Git normally creates it from the uniquely
matching `origin/feature/local-ui`. If any command fails, stop and share that error.
No V3 branch merge is needed. Keep the terminal open. Expected:

```text
ARK Local UI ready
http://127.0.0.1:8765
Model loading; see the browser for status. Ctrl+C stops the server.
```

Open that URL in Edge/Chrome. The ready message means the HTTP listener is ready;
wait for the UI to change from **Loading model** to **Ready**. Qwen's model filename,
Q4_K_M, ARK V2 and **LOCAL MODEL** must be shown. No browser auto-launch is required.

If port 8765 is already occupied, stop the previous ARK UI process or use:

```powershell
.\.venv\Scripts\ark-ui.exe --config config.toml --port 8766
```

Do not grant public-network access or change binding to solve a port conflict.
One process per model is sufficient; parallel UI/CLI/benchmark processes would
load separate models and consume additional RAM.

## Target-PC gate (required before merge)

Use only these test messages in the evidence session. Keep private chats out of
public PRs. Do not edit failed answers or overwrite existing benchmark reports.

1. **Online browser check.** Confirm the screen fits the window and the model
   metadata/loading/ready states are correct. Type Japanese with the Windows IME:
   converting/confirming text must not send; Enter after confirmation sends.
   Shift+Enter adds a newline. Click Send as well. During generation, sending
   again and resetting must be disabled. Refresh a tab and verify the same
   conversation is shown without reloading the model.
2. **Conversation and reset.** Send the following messages individually, clicking
   Reset conversation at the indicated step. Check Japanese meaning and recall.

```text
日本語で短く自己紹介してください。
この会話の合言葉は青いりんごです。覚えてください。
先ほどの合言葉は何ですか？
```

Click **Reset conversation**. The visible conversation must clear. Then send:

```text
この新しい会話で合言葉をまだ伝えていない場合は「未指定」と答えてください。
```

Reset is verified using the UI result, reset log event and unit-tested empty V2
history together; a model answer by itself does not prove context deletion.

3. **Offline cold start.** Wait for generation to finish, then stop the UI with
   Ctrl+C and close its browser tab. Physically disconnect Wi-Fi/Ethernet/other
   network connections. Start a **new process** with the same command, open a
   fresh tab at 127.0.0.1, and repeat step 2. Confirm the entire screen loads and
   Japanese inference/recall/reset work. Browser developer-tools offline emulation
   is not the physical-disconnection attestation.
4. **Error display.** Stop the normal UI, then start with an intentionally absent
   configuration filename (verify that filename is absent):

```powershell
Test-Path .\ui-missing-config.toml
.\.venv\Scripts\ark-ui.exe --config .\ui-missing-config.toml
```

Expected: `False` from Test-Path; UI serves normally but shows a load error,
disabled input and no `LOCAL MODEL` claim. Stop this process afterward. The real
`config.toml` is not modified. If Test-Path returns True, choose another absent name.

5. **V1/V2 regression on the UI branch.** Stop all UI/model processes first.
   Run sequentially with the unchanged V1-tested config and physical network
   disconnection. The timestamp creates new output filenames:

```powershell
$uiGateStamp = Get-Date -Format 'yyyyMMdd-HHmmss'
.\.venv\Scripts\ark-bench.exe --config config.toml --offline-attested --cpu 'Intel64 Family 6 Model 142 Stepping 10, GenuineIntel' --ram-gib 16 --output "benchmark-results/ui-v1-$uiGateStamp.json"
.\.venv\Scripts\ark-eval.exe --backend llama-cpp --config config.toml --offline-attested --output "benchmark-results/ui-v2-$uiGateStamp.json"
.\.venv\Scripts\ark-compare.exe evidence/v2/raw/v2-real-1.json "benchmark-results/ui-v2-$uiGateStamp.json" --output "benchmark-results/ui-v2-comparison-$uiGateStamp.json"
```

Use `--offline-attested` only when disconnected. V1 expects startup success,
zero failures and meaningful Japanese/recall. V2 uses the frozen 12-question suite:
the reviewed baseline is 11/12 with math-02's format FAIL. Preserve all failures;
do not alter fixtures/scoring to obtain green. New runtime/semantic regressions
or incompatible comparison require review and block merge.

Return the branch head SHA, browser/version, screenshots (ready/chat/error), the
two UI test-session JSONL files from configured `logs/`, the three new regression
JSON files, and your observations on Japanese IME, Enter/Shift+Enter, multi-turn,
reset, duplicate prevention and physical offline cold start. Logs from general
private conversations should not be attached. No benchmark numbers are claimed
until these originals have been reviewed.

## Automated verification and limits

```bash
python -m pip install -e '.[dev]'
ruff check .
pytest
node --test tests/ui/client.test.cjs
python scripts/ui_smoke.py
```

HTTP tests run on actual ephemeral loopback sockets with deterministic backends
and the real V2 engine. They cover loading/model reuse, multi-turn/reset, errors,
logging failure, conflicting/stale requests, origin/token/body checks and packaged
assets. JS tests exercise the shipped client with DOM/fetch doubles, including
composition events, double-submit, error/draft recovery and safe text rendering.
They are **not** a browser-render or native-IME test. CI also installs the wheel and
starts the packaged mock UI, while preserving V1 benchmark/V2 mock regression.

The Work browser could not open 127.0.0.1 (`ERR_BLOCKED_BY_CLIENT`). Therefore visual
layout, actual browser interaction, Windows IME and real/offline UI evidence remain
target-PC gates. Passing tests does not set Local UI to official PASS.

Those target-PC gates were subsequently completed and independently reviewed from
the submitted originals. See [the frozen Local UI evidence](../evidence/local-ui/REVIEW.md).
The historical procedure and limitations above remain for reproducibility.

| Completion item | Evidence required |
| --- | --- |
| Loopback listener, V2 integration, reset, errors, metadata, bundled assets | Unit/HTTP/JS tests + CI |
| Existing V1/V2 regression | Frozen-source tests + target regression JSON review |
| Screen, Japanese input, Enter/Shift+Enter, generating/loading behavior | Target browser review |
| Real Qwen load, Japanese response, multi-turn, reset, logs | Target UI sessions |
| Disconnected UI startup and inference | Physical-offline cold-start attestation + session |
| Final CI green | All jobs on final PR head |
| Merge / Local UI official PASS | All preceding evidence reviewed; otherwise keep Draft |
