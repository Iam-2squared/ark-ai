# ARK Launcher and Target-PC Gate Runner

Status: **IMPLEMENTED / TARGET-PC GATE PENDING / MERGE BLOCKED**.
The frozen contract is [USABILITY_CONTRACT.md](USABILITY_CONTRACT.md). Both tools
are presentation/evidence infrastructure over the Local UI v1 official freeze;
they do not change V1/V2 semantics or V3.

## Daily use

Install the branch into the existing Windows virtual environment once:

```powershell
Set-Location 'C:\Users\Owner\Desktop\Git Ark\ark-ai'
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
```

Start ARK thereafter with:

```powershell
.\.venv\Scripts\ark-launch.exe
```

`ark-launch` uses `config.toml`, starts the existing Local UI on 127.0.0.1:8765,
and opens the default browser only after the listener exists. If that port already
has a compatible ARK UI, it opens and reuses it instead of loading another model.
If an unrelated service owns 8765, it does not stop that process and tries the
fixed loopback fallback 8766. If both are occupied, it exits with a clear error.

The server remains useful when browser auto-open fails; open the printed URL.
Configuration/model load errors remain visible in Local UI. Normal startup has no
network dependency. Keep the terminal open and press **Ctrl+C** to stop a server
started by this command. Closing the browser tab alone does not stop it.

There is intentionally no public bind, service, tray process, auto-start, process
killing, model download, updater, telemetry, external API or cloud integration.

## Target-PC evidence workflow

The runner creates `evidence-bundles/local-ui-...`, which is Git-ignored and never
uploaded or committed automatically. Run it only on a clean tracked source tree.
Untracked local config/models/logs are recorded separately and do not change HEAD.

### 1. Start a unique bundle

```powershell
$gateOutput = .\.venv\Scripts\ark-gate.exe local-ui --start --config config.toml --browser 'Google Chrome 152.0.7977.83'
$bundle = Get-ChildItem .\evidence-bundles -Directory |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1 -ExpandProperty FullName
$bundle
```

The first command records Git, environment, config and model identity, including
the GGUF SHA-256. Keep `$bundle` for all later stages. If HEAD, tracked source,
config, model, fixed suite, scorer or policy changes, the runner marks the bundle
stale and refuses reuse.

### 2. Run existing regressions

Stop other ARK/model processes first. Physically disconnect networking if this run
is intended as offline evidence, then execute:

```powershell
.\.venv\Scripts\ark-gate.exe local-ui --regressions --bundle "$bundle" --offline-attested
```

This invokes the existing V1 `ark-bench`, V2 fixed real evaluation, and comparison
against the frozen V2 baseline. It preserves every result. The known `math-02`
numeric-only format failure must remain recorded; it is not rewritten or hidden.
Regression originals are never overwritten. A failed/partial run remains evidence;
start a new bundle instead of deleting or replacing it.

CI may exercise plumbing with `--mock`, but mock evidence can never become
`READY_FOR_REVIEW` and is not target-model performance.

### 3. Use the UI and select the correct session

Start `ark-launch`, perform only the dedicated test conversation, reset and
post-reset check, then stop ARK. Discover candidates created during this gate:

```powershell
.\.venv\Scripts\ark-gate.exe local-ui --collect-sessions --bundle "$bundle" --logs .\logs
```

The runner parses candidate contents and displays whether each contains the Local
UI start event, passphrase setup/recall, exact reset event and post-reset turn. It
does **not** copy whichever log is newest. After reviewing the list, explicitly
select the intended original:

```powershell
$session = '.\logs\session_YYYYMMDDTHHMMSS_ffffffZ.jsonl'
.\.venv\Scripts\ark-gate.exe local-ui --collect-sessions --bundle "$bundle" --logs .\logs --session "$session"
```

Only a valid UTF-8 JSONL inside the declared logs directory and gate time window is
accepted. Display mojibake in a terminal never causes the original to be rewritten.
Do not select a private/general conversation log.

### 4. Add screenshots and human observations

Prepare PNG/JPEG screenshots for the four checklist kinds. One image may support
multiple kinds when it visibly contains both states. Finalize interactively:

```powershell
.\.venv\Scripts\ark-gate.exe local-ui --finalize --bundle "$bundle" `
  --screenshot 'ready=C:\path\ready.png' `
  --screenshot 'conversation=C:\path\conversation.png' `
  --screenshot 'reset=C:\path\reset.png' `
  --screenshot 'error=C:\path\error.png'
```

The prompts deliberately keep physical disconnection, Windows IME, keyboard/button
behavior, generating controls, visual Loading→Ready and refresh retention separate
from automatic observations. Answering yes is a user attestation, not automated
proof. `--network-state` can record an OS observation but never substitutes for
the physical-offline attestation.

For automation, use `--non-interactive` and repeated `--attest NAME`; omitted items
remain false. Valid names are printed by `ark-gate local-ui --help` documentation:
`physical_offline`, `ime`, `enter`, `shift_enter`, `send_button`,
`generating_controls`, `loading_ready`, and `refresh_retention`.

The result contains `TARGET_PC_REPORT.md`, source reports, session originals,
screenshot metadata/files and `manifest.sha256`. Its status is only
`READY_FOR_REVIEW` or `INCOMPLETE`; **never OFFICIAL PASS**. Sharing, Git commits,
PR updates, merge and final judgment require an explicit separate review.

## Troubleshooting

- **Port occupied:** reuse occurs only for a compatible ARK UI. An unrelated 8765
  service causes fallback to 8766; no process is killed.
- **Missing config/model:** use the existing `config.toml` and GGUF. Local UI shows
  loader errors; no automatic download or replacement occurs.
- **Browser did not open:** manually open the printed 127.0.0.1 URL. The healthy
  server continues running.
- **Dirty tracked tree:** preserve/commit the user's work separately and start a
  new clean bundle. The runner will not label dirty-source evidence review-ready.
- **Regression failure:** keep the bundle unchanged for diagnosis. Do not edit the
  report, fixture, scorer or output to make it pass.
- **Stale bundle:** restore the exact recorded identity or start a new bundle. No
  evidence is silently reused across a changed HEAD/config/model/contract.

## Automated verification

Real Qwen is not loaded in CI. Tests cover loopback selection/reuse, browser failure,
fixed fallback, non-overwriting bundles, Git/environment/model identity, mock V1/V2
integration, content/time-window session validation, UTF-8 preservation, reset,
screenshots, manifest, attestations, resume and stale rejection. Existing V1/V2/
Local UI regressions remain in the Windows/Linux Python 3.11–3.13 matrix.
