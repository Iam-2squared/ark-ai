# Windows CPU-only setup and final gate

Status (2026-09-08): **V1 final gate pending. V2 locked.**
Target: Intel Core i5 8th Gen, 16 GB RAM, no dedicated GPU.
User-reported evidence: Python 3.12.10, `.venv`, VS Build Tools 2022,
MSVC 19.44.35228 x64 / NMAKE 14.44.35228, llama-cpp-python 0.3.35 native
build/import, and `pip install -e . --no-deps` succeeded. Real GGUF is not yet tested.

## Preserve the working installation

For the current user, do not rebuild the runtime. Use VS Code's PowerShell terminal:

```powershell
Set-Location 'C:\Users\Owner\Desktop\Git Ark\ark-ai'
git status --short
git pull --ff-only origin main
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -c "import llama_cpp; print(llama_cpp.__version__)"
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
```

Expected: Python 3.12.10, llama_cpp 0.3.35, successful ARK installation.
If pull reports local conflicts, stop and show the output; do not discard local files.
Using explicit `.venv` executables avoids activation-policy and interpreter ambiguity.

## First-time native setup (only when rebuilding on another PC)

Install Python 3.12 x64 and Visual Studio Build Tools 2022 with **Desktop development
with C++**, MSVC x64/x86 tools, and a Windows SDK. The project's previous generic
`pip install -e ".[local]"` command selected a source distribution; a compiler is
required when no matching CPU wheel is selected. This is also described by the
[upstream installation documentation](https://github.com/abetlen/llama-cpp-python#installation).

Open **Command Prompt (cmd.exe)**, not PowerShell, for this block:

```bat
cd /d "C:\Users\Owner\Desktop\Git Ark\ark-ai"
py -3.12 -m venv .venv
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
call .venv\Scripts\activate.bat
cl
nmake /?
python -m pip install --no-cache-dir llama-cpp-python==0.3.35
python -c "import llama_cpp; print('llama_cpp OK:', llama_cpp.__version__)"
python -m pip install -e . --no-deps
```

These reproduce the user-reported successful path. On a new PC, verify the pip output
actually says `Successfully built llama-cpp-python`; do not count installation alone
as an import or inference pass. Build Tools are not needed for every chat startup.

Rejected on this target: the `v0.3.35-hip-radeon` release wheel
`llama_cpp_python-0.3.35-py3-none-win_amd64.whl` installed but failed to load `llama.dll`.
Do not reuse it as an Intel CPU setup solution. Earlier source-build errors
(`nmake` missing, C/CXX compiler not set) were resolved by the x64 developer environment.

## VS Code interpreter

Use Ctrl+Shift+P -> Python: Select Interpreter -> Enter interpreter path ->
`C:\Users\Owner\Desktop\Git Ark\ark-ai\.venv\Scripts\python.exe`.
Open a new terminal and check `python -c "import sys; print(sys.executable)"`.
The explicit commands in this guide remain valid regardless of VS Code selection.
Both `.venv/` and `.venv-*/` are ignored by Git. Do not delete `.venv-1` until you have
confirmed it contains only a disposable environment and no needed project files.
There is no need to delete it to finish V1.

## Selected model and fixed download

Use **Qwen3-4B-Instruct-2507, Q4_K_M**, 4.0B parameters, Apache-2.0 base-model
license. Quantization is from bartowski (a community quantizer, not Qwen's own GGUF).
Selection rationale and alternatives: [MODEL_SELECTION.md](MODEL_SELECTION.md).

The filename below is from the actual file tree, which differs from the model-card
link label. Fixed repository revision:
`ae44f08e1392f39c0e474af10c3ff8355c8b6688`.
File size: **2,497,280,736 bytes**. Download only this file, not the whole repository.

In **PowerShell**, while online:

```powershell
New-Item -ItemType Directory -Force models | Out-Null
$arkModelFile = 'models/Qwen_Qwen3-4B-Instruct-2507-Q4_K_M.gguf'
$arkModelUrl = 'https://huggingface.co/bartowski/Qwen_Qwen3-4B-Instruct-2507-GGUF/resolve/ae44f08e1392f39c0e474af10c3ff8355c8b6688/Qwen_Qwen3-4B-Instruct-2507-Q4_K_M.gguf?download=true'
curl.exe --fail --location --retry 3 --continue-at - --output $arkModelFile $arkModelUrl
if ($LASTEXITCODE -ne 0) { throw 'Download failed. Retry before continuing.' }
$arkDigest = (Get-FileHash $arkModelFile -Algorithm SHA256).Hash.ToLowerInvariant()
if ($arkDigest -ne '2fde00ce69dd4899c70d020845e2638353015bba0fdf161b3eb965f2bca4464e') { throw 'SHA256 mismatch: do not load this file.' }
(Get-Item $arkModelFile).Length
```

Expected: no hash error; length `2497280736`. If downloading in a browser instead,
use the same fixed URL and run the hash verification before model loading.

Create the configuration once (preserves any existing config):

```powershell
if (!(Test-Path config.toml)) { Copy-Item config.windows-qwen3.toml config.toml }
Get-Content config.toml
```

It should match `config.windows-qwen3.toml`: exact model path, family, parameter size,
Q4_K_M, context 4096, threads 4, max_tokens 256, temperature 0.2, top_p 0.95, seed 42.
If `ARK_MODEL_PATH` is set it overrides the file: inspect `$env:ARK_MODEL_PATH`.
For this test, remove an unintended override from this terminal only:
`Remove-Item Env:ARK_MODEL_PATH -ErrorAction SilentlyContinue`.

## Real-model and physical offline test

Run:

```powershell
.\.venv\Scripts\ark.exe --config config.toml
```

Expected: `ARK V1 ready` with the GGUF filename (never `echo-test-backend`).
Ask these as separate turns:

1. `日本語で短く自己紹介してください。`
2. `この会話の合言葉は青いりんごです。覚えてください。`
3. `先ほどの合言葉は何ですか？`
4. `/reset` (expect `Conversation reset.`)
5. `日本語で「新しい会話です」と答えてください。`
6. `/exit`

Check natural Japanese and correct recall before reset. A blank answer, error,
repeated gibberish or incorrect recall is not a pass. If context fills, use `/reset`;
V1 reports overflow instead of silently deleting conversation history.

**Now disable Wi-Fi and disconnect Ethernet and other network connections.**
Restart `ark` using the same command, repeat the conversation and `/exit`.
This cold restart is essential: a prior online session is not offline evidence.
ARK uses local file loading and does not download a model at runtime.

With the network still disconnected, run the benchmark twice in separate processes:

```powershell
.\.venv\Scripts\ark-bench.exe --config config.toml --offline-attested --ram-gib 16 --output benchmark-results/v1-offline-1.json
.\.venv\Scripts\ark-bench.exe --config config.toml --offline-attested --ram-gib 16 --output benchmark-results/v1-offline-2.json
```

Expected: exit code 0; startup_success true, failure_count 0, six nonempty responses,
positive memory measurement. `--offline-attested` records your observation; it does
not turn off networking or automatically certify offline operation. Review the Japanese
and memory_recall answers in both JSON files. Nonempty output is not semantic success.

The benchmark writes hash/size/filename, declared family/parameters/quantization,
configuration/seed, runtime versions, OS/CPU, user-reported installed RAM, model load
latency, first visible token latency, estimated output tokens/sec, peak resident RAM,
wall time and failures. Model metadata from TOML is declared, not inferred from weights.
If CPU identification is empty, supply the actual CPU name using `--cpu "..."`.
Peak working set is not total system RAM or committed virtual memory. Token counts
are re-tokenized visible output estimates; speed includes prompt processing.
Timings vary with load, caching and power mode, even with the same seed.

## Evidence to return

Keep both benchmark JSON files and the two relevant local `logs/session_*.jsonl` files.
Create a local `benchmark-results/v1-review.txt` containing:

```text
Date/time:
Git commit (git rev-parse HEAD):
CPU exact model:
RAM installed:
Online Japanese conversation: PASS / FAIL (reason)
Online multi-turn recall and reset: PASS / FAIL (reason)
All network interfaces disconnected before cold restart: YES / NO
Offline startup: PASS / FAIL (reason)
Offline Japanese conversation: PASS / FAIL (reason)
Offline multi-turn recall and reset: PASS / FAIL (reason)
Benchmark 1: filename, exit code, reviewed Japanese/recall result
Benchmark 2: filename, exit code, reviewed Japanese/recall result
CLI crashes/errors observed:
```

Reconnect after testing. Share the two JSONs, review text and test conversation logs
in ChatGPT. Do not commit private chat logs or model files to the public repository.
V1 remains pending until all six real-model gates in V1_VERIFICATION.md are reviewed.
