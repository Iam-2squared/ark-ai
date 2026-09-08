# V2 実機評価 — Windows / 既存Qwen GGUF

V1はPR #4の原本レビューで正式PASS。固定点:
`7e46a4529879243b4a5bd52bb6575d11c1ec0183`。
V2は未PASS。以下の結果をレビューするまでPR #3はDraft・merge禁止。
これは実機でこれから検証する手順であり、実行済みという主張ではない。

## 1. 更新（ネットワーク接続中、PowerShell）

```powershell
Set-Location 'C:\Users\Owner\Desktop\Git Ark\ark-ai'
git status --short
```

変更が表示されたら止める。上書き・reset・cleanはしない。
`.venv`、既存の `config.toml`、GGUFをそのまま使う。追加モデルの取得は不要。

```powershell
git fetch origin
git switch research/v2-ark-intelligence
git pull --ff-only origin research/v2-ark-intelligence
git rev-parse HEAD
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
.\.venv\Scripts\python.exe -c "import llama_cpp; print(llama_cpp.__version__)"
```

branchがローカルに未作成なら `git switch` は通常originの同名branchから作成する。
エラー時は停止して出力を共有。成功済みCPU runtimeを再buildしない。
`git rev-parse HEAD` のSHAを結果と一緒に返す。

設定はV1と同じ：llama-cpp、Qwen3-4B-Instruct-2507 Q4_K_M、context 4096、
threads 4、max_tokens 256、temperature 0.2、top_p 0.95、seed 42。
モデルSHAは `2fde00ce69dd4899c70d020845e2638353015bba0fdf161b3eb965f2bca4464e`。
評価JSONが実ファイルを再hashする。ARK_MODEL_PATH環境変数を設定している場合は
TOMLより優先されるので、JSONのモデル名・hash・設定も確認する。

## 2. V2会話・reset・logging

Wi-Fi/Ethernetなどを切断してから、新しいprocessとして起動する。
ネット切断は手動確認であり、CLIが自動証明するものではない。

```powershell
.\.venv\Scripts\ark-v2.exe --backend llama-cpp --config config.toml
```

以下はCLI内で1行ずつ入力する。一般の個人的会話は混ぜない。

```text
日本語で短く自己紹介してください。
この会話の合言葉は青いりんごです。覚えてください。
先ほどの合言葉は何ですか？
/reset
この新しい会話で合言葉をまだ伝えていない場合は「未指定」と答えてください。
/exit
```

期待する証拠：正常起動、意味の通る日本語、reset前の正しい合言葉、
reset表示・その後の会話、正常終了、画面に出たsession JSONL。
V2ログには開始/reset/終了eventも残る。回答が違ってもログを修正しない。
reset後の応答のみで履歴消去を断定せず、eventとunit testと合わせてレビューする。

## 3. 固定12問を2回実行

初回出力を上書きしない。同名ファイルがすでにある場合は別の出力名を使う。
オフライン状態のまま、各コマンドの終了を待って次へ進む。

```powershell
.\.venv\Scripts\ark-eval.exe --backend llama-cpp --config config.toml --offline-attested --output benchmark-results/v2-real-1.json
.\.venv\Scripts\ark-eval.exe --backend llama-cpp --config config.toml --offline-attested --output benchmark-results/v2-real-2.json
.\.venv\Scripts\ark-compare.exe benchmark-results/v2-real-1.json benchmark-results/v2-real-2.json --output benchmark-results/v2-real-comparison.json
```

`--offline-attested` は実際に全接続を切った場合のみ付ける。
会話2問（日本語形式/JSON）、context2問、Math3問、Reasoning2問、Coding3問。
CPUでは時間がかかる。12問全部が終わるまで待ち、失敗・中断も報告する。
モデル不正答はそのままBaselineに残す。評価exit 0は全問正解やV2 PASSではなく、
実行完了を意味する。比較exit 1やruntime errorも、隠さずJSON・consoleを共有する。
Codingは制限付きAST評価であり、生成されたPythonをOS上で自動実行しない。

## 4. V1 regression確認（同じbranchで）

V1 CLI/Coreはコード変更していないが、同じ環境での確認を残す。

```powershell
.\.venv\Scripts\ark.exe --config config.toml
```

V1と同じ日本語→合言葉→recall→`/reset`→新しい会話→`/exit`を確認。
そのsession JSONLと実機での結果も保存する。

```powershell
.\.venv\Scripts\ark-bench.exe --config config.toml --offline-attested --cpu 'Intel64 Family 6 Model 142 Stepping 10, GenuineIntel' --ram-gib 16 --output benchmark-results/v1-on-v2-regression.json
```

期待：startup true、test_backend false、failure_count 0、正しいモデルhash、
日本語/recallが意味的に正常。これはV2固定12問とは異なるV1 suiteなので、
`ark-compare` でV1 JSONとV2 JSONを混ぜない。

## 5. 返すEvidence

- `git rev-parse HEAD`、Windows/Python/runtime、設定変更の有無。
- V2 JSON 2本、comparison JSON、V1 regression JSON。
- V2とV1のテスト専用session JSONL。
- ネット切断後の新規起動、日本語、recall、reset、exitの確認結果。
- エラーがあればconsole全文（個人情報や秘密は除く）。

こちらで原本・固定suite/hash・score・runtime failure・V1 regressionを監査する。
問題がなければ実モデルBaselineを固定し、最終headのCI GREEN確認後にだけPR #3を
merge判定する。V2測定前に性能値を推測したりPASSへ変更したりしない。
