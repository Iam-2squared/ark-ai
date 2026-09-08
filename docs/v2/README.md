# V2 ARK Intelligence - 先行開発

**V1: OFFICIAL PASS / V2: 実モデルBaselineレビュー完了。最終CI GREEN後のPR #3 mergeで正式PASS。**
[原本と最終レビュー](../../evidence/v2/REVIEW.md)：独立2runとも11/12、runtime failure 0。
以下のDraft運用・未測定表記は先行開発時の記録。現状は上記レビューとGATES.mdを参照。

mainはV1のまま使用する。V2は `research/v2-ark-intelligence` のDraft PRでレビューする。
自動mergeは有効化しない。Draft解除・mergeは、V2の実機結果をレビューした後の別作業。
DraftはGitHubの通常mergeを止めるが、リポジトリ管理者による操作を全面的に防ぐ
branch protectionではない。repositoryのアクセス設定は変更していない。

## 実装した範囲

| 部分 | 実装 | 制限 |
| --- | --- | --- |
| Contract | 不変のMessage / Request / Response / Capability | contract version 1 |
| Context | system保持、現在の入力保持、古い完全な会話往復を削除 | 現在の会話のみ、DBなし |
| Policy | concise / explanation / coding / structured | モードは出力方針、能力向上の保証ではない |
| Capability | context容量、chat対応、言語・coding根拠、generation controls | モデル名から推定しない |
| Math | 3問、数値正規化と厳密採点 | 小規模な固定development評価 |
| Reasoning | 2問、明示された答えとの一致 | 一般的推論力の網羅評価ではない |
| Conversation | 日本語形式1問・JSON形式1問 | 自然な会話品質は実機評価待ち |
| Context評価 | 合言葉、訂正後の情報を保持する2問 | 実モデルの保持能力は未測定 |
| Coding | 3関数、各3テスト、制限付きAST解釈 | 一般Python実行環境ではない |
| Regression | taskごとの退行/改善、設定差分、互換性検査 | mockとrealは混ぜず別々に比較 |

Architecture: [CONTRACT.md](CONTRACT.md) / [評価仕様](EVALUATION.md) /
[Completion Gate](GATES.md)。V1の `ark` / `ark-bench` と既存Coreはそのまま残す。
V2は新しい `ark-v2` / `ark-eval` / `ark-compare` で明示的に使う。

## 今PCが使えなくても確認できるもの

Draft PRのコード、GitHub Actionsのテスト結果、Actions artifactの評価JSONを確認できる。
実モデルCLIと評価adapterを追加。実機の正答率・性能はまだ未測定。

開発用環境では以下を実行する（ユーザーのV1用PCでbranch切替する必要はない）：

```bash
python -m pip install -e '.[dev]'
ruff check .
pytest
ark-v2 --mode concise
ark-eval --output benchmark-results/v2-baseline.json
ark-eval --output benchmark-results/v2-candidate.json
ark-compare benchmark-results/v2-baseline.json benchmark-results/v2-candidate.json
```

`ark-v2` はecho mock。`/reset` と `/exit` を使用できる。
`ark-eval` は固定scripted mock。12/12でもAIの正答率を意味しない。
`model_pass_rate`、モデルtokens/sec等は `null`、`NOT_MEASURED` を保持する。
fixture/scorerの結果・時間・context予算は `infrastructure_*` に保存する。

実機で実モデルを使う場合のみ `--backend llama-cpp --config config.toml` を指定する。
[Windows実機評価手順](REAL_MODEL.md)に従う。V1のモデル・runtimeをそのまま利用できる。

## Context動作

出力tokensと余裕分を先に予約する。systemと現在入力が収まらない場合はエラー。
履歴が多い場合は古いuser/assistantペアから外す。直近の入力を途中切断しない。
返答が正常な場合だけ、保持された履歴と新しい往復をcommitする。
空応答・backendエラー・budgetエラーは状態を変えない。resetは履歴を空にする。

標準token予算はUTF-8バイト数＋フレーム分の推定値。正確なtokenizerではなく、
chat templateごとの保証でもない。日本語では早めに履歴が外れる可能性がある。
計数関数を交換できるので、実機Gate時に正しいtemplate/tokenizerとの対応を検証する。

## V1で問題が見つかった場合

先にV1修正を別PRでmainへ入れる。V2 branchへそのmain変更を取り込み、全テストと
CIを再実行する。固定suiteを変更せず、比較可能性とV1のCLI動作を確認する。
