import { useState } from 'react';
import {
  Check,
  Circle,
  GitBranch,
  Layers3,
  RotateCcw,
  ShieldCheck,
  Square,
  Terminal,
  ChevronRight,
  AlertCircle,
} from 'lucide-react';
import {
  Badge,
  Button,
  DemoNotice,
  EmptyState,
  Modal,
  Notice,
  Panel,
  word,
  type Language,
} from '../components/ui';
import './workspaces.css';

type TaskState = 'review' | 'failed' | 'completed';
type StepState = 'completed' | 'blocked' | 'failed' | 'pending';
interface Task {
  id: string;
  title: [string, string];
  description: [string, string];
  state: TaskState;
}
const tasks: Task[] = [
  {
    id: 'demo-task-001',
    title: ['Prepare workspace briefing', 'ワークスペース概要の作成'],
    description: [
      'Summarize project notes and prepare a reviewable briefing.',
      'プロジェクトのノートを要約し、確認用の概要を準備する。',
    ],
    state: 'review',
  },
  {
    id: 'demo-task-002',
    title: ['Build a knowledge index', '知識インデックスの作成'],
    description: [
      'Read approved documents and prepare an index preview.',
      '承認済み文書を読み取り、索引のプレビューを準備する。',
    ],
    state: 'failed',
  },
  {
    id: 'demo-task-003',
    title: ['Organize daily notes', '日次ノートの整理'],
    description: [
      'Group sample notes and draft a daily summary.',
      'サンプルノートを分類し、日次要約を作成する。',
    ],
    state: 'completed',
  },
];
const steps: [string, string][] = [
  ['Inspect sources', 'ソースを確認'],
  ['Extract context', '文脈を抽出'],
  ['Draft briefing', '概要を作成'],
  ['Review checkpoint', 'レビューGate'],
  ['Finalize output', '出力を確定'],
];

export function Agents({ demo, lang }: { demo: boolean; lang: Language }) {
  const [selectedId, setSelectedId] = useState(tasks[0].id);
  const [selectedStep, setSelectedStep] = useState(3);
  const [action, setAction] = useState<'retry' | 'cancel' | null>(null);
  const [notice, setNotice] = useState('');
  const task = tasks.find((item) => item.id === selectedId) ?? tasks[0];
  const ix = lang === 'ja' ? 1 : 0;
  const stateLabel = (state: TaskState) =>
    ({
      review: word(lang, 'Awaiting review', 'レビュー待ち'),
      failed: word(lang, 'Failed', '失敗'),
      completed: word(lang, 'Completed', '完了'),
    })[state];
  const stepState = (index: number): StepState =>
    task.state === 'completed'
      ? 'completed'
      : task.state === 'failed'
        ? index === 1
          ? 'failed'
          : index > 1
            ? 'pending'
            : 'completed'
        : index < 3
          ? 'completed'
          : index === 3
            ? 'blocked'
            : 'pending';
  const stepLabel = (state: StepState) =>
    ({
      completed: word(lang, 'Complete', '完了'),
      blocked: word(lang, 'Review required', '確認が必要'),
      failed: word(lang, 'Failed', '失敗'),
      pending: word(lang, 'Pending', '未実行'),
    })[state];
  if (!demo)
    return (
      <div className="screen-stack">
        <Notice>
          {word(
            lang,
            'Planner, execution logs and crash recovery are not exposed by the current backend API.',
            '現在のBackend APIはPlanner・実行ログ・Crash Recoveryを公開していません。',
          )}
        </Notice>
        <Panel
          title={word(lang, 'Agent workspace', 'Agentワークスペース')}
          action={<Badge>{word(lang, 'Unavailable', '利用不可')}</Badge>}
        >
          <EmptyState
            title={word(lang, 'No agent runtime connected', 'Agent Runtimeは未接続です')}
            icon={<GitBranch size={24} />}
          >
            {word(
              lang,
              'This interface cannot start, retry, cancel or recover real tasks. Explore a sample plan in Demo mode.',
              'このUIから実際のタスクの開始・再試行・キャンセル・復旧は行えません。Demoでサンプル計画を確認できます。',
            )}
          </EmptyState>
        </Panel>
      </div>
    );

  return (
    <div className="screen-stack">
      <DemoNotice lang={lang} />
      {notice && <Notice>{notice}</Notice>}
      <div className="ws-agent-layout">
        <Panel
          title={word(lang, 'Tasks', 'タスク')}
          eyebrow={word(lang, 'SAMPLE WORKSPACE', 'サンプルワークスペース')}
          action={<Badge>Demo · 3</Badge>}
        >
          <div className="ws-task-list">
            {tasks.map((item) => (
              <button
                key={item.id}
                className={`ws-task-item ${item.id === selectedId ? 'is-selected' : ''}`}
                aria-pressed={item.id === selectedId}
                onClick={() => {
                  setSelectedId(item.id);
                  setSelectedStep(item.state === 'failed' ? 1 : 3);
                }}
              >
                <span className="ws-task-icon">
                  <Layers3 size={18} />
                </span>
                <span className="ws-task-main">
                  <strong>{item.title[ix]}</strong>
                  <span className={`ws-task-state ws-task-state-${item.state}`}>
                    <span className="ws-state-dot" />
                    {stateLabel(item.state)}
                  </span>
                  <span className="mono muted">{item.id}</span>
                </span>
                <ChevronRight size={15} />
              </button>
            ))}
          </div>
          <div className="ws-panel-foot">
            {word(lang, 'Sample plans · No active agent', 'サンプル計画 · 実際のAgent稼働なし')}
          </div>
        </Panel>
        <Panel
          title={task.title[ix]}
          eyebrow={word(lang, 'PLAN INSPECTOR', '計画インスペクター')}
          action={
            <Badge
              tone={
                task.state === 'failed' ? 'red' : task.state === 'completed' ? 'green' : 'amber'
              }
            >
              Demo · {stateLabel(task.state)}
            </Badge>
          }
        >
          <div className="ws-plan-detail">
            <p className="muted">{task.description[ix]}</p>
            <div className="ws-plan-toolbar">
              <span className="mono muted">{task.id} / revision 1</span>
              <div className="ws-button-row">
                <Button
                  disabled={task.state !== 'failed'}
                  title={word(
                    lang,
                    'Preview only · available for the failed sample',
                    'プレビューのみ · 失敗サンプルで利用可能',
                  )}
                  onClick={() => setAction('retry')}
                >
                  <RotateCcw size={14} />
                  {word(lang, 'Review retry', '再試行を確認')}
                </Button>
                <Button
                  variant="ghost"
                  disabled={task.state === 'completed'}
                  onClick={() => setAction('cancel')}
                >
                  <Square size={13} />
                  {word(lang, 'Review cancel', 'キャンセルを確認')}
                </Button>
              </div>
            </div>
            <div
              className="ws-dag"
              aria-label={word(lang, 'Sample plan dependency graph', 'サンプル計画の依存グラフ')}
            >
              <div className="ws-dag-label">
                <GitBranch size={14} />
                {word(lang, 'PLAN DAG', '計画DAG')}
                <span>{word(lang, 'Select a step to inspect', 'Stepを選択して詳細を確認')}</span>
              </div>
              <ol className="ws-dag-nodes">
                {steps.map((step, index) => {
                  const state = stepState(index);
                  return (
                    <li key={step[0]}>
                      <button
                        className={`ws-dag-node ws-dag-${state} ${index === selectedStep ? 'is-focused' : ''}`}
                        aria-pressed={index === selectedStep}
                        onClick={() => setSelectedStep(index)}
                      >
                        <span className="ws-step-number">
                          {state === 'completed' ? (
                            <Check size={13} />
                          ) : state === 'failed' ? (
                            <AlertCircle size={13} />
                          ) : (
                            index + 1
                          )}
                        </span>
                        <strong>{step[ix]}</strong>
                        <span>{stepLabel(state)}</span>
                      </button>
                    </li>
                  );
                })}
              </ol>
            </div>
            <div className="ws-step-inspector">
              <div>
                <span className="eyebrow">
                  {word(
                    lang,
                    `STEP ${String(selectedStep + 1).padStart(2, '0')}`,
                    `STEP ${String(selectedStep + 1).padStart(2, '0')}`,
                  )}
                </span>
                <h3>{steps[selectedStep][ix]}</h3>
              </div>
              <Badge
                tone={
                  stepState(selectedStep) === 'failed'
                    ? 'red'
                    : stepState(selectedStep) === 'blocked'
                      ? 'amber'
                      : 'neutral'
                }
              >
                {stepLabel(stepState(selectedStep))}
              </Badge>
            </div>
            <p className="ws-step-description">
              {stepState(selectedStep) === 'failed'
                ? word(
                    lang,
                    'Sample failure: the source document is unavailable. The plan stopped before any output was written. Inspect the source before reviewing a retry.',
                    'サンプル障害：ソース文書が利用できません。出力を書き込む前に停止しています。ソースを確認してから再試行を検討してください。',
                  )
                : stepState(selectedStep) === 'blocked'
                  ? word(
                      lang,
                      'Sample checkpoint: the draft requires human review. No approval has been granted and no tool action will run from this interface.',
                      'サンプル確認Gate：下書きには人のレビューが必要です。実行承認は与えられておらず、この画面からTool操作は実行しません。',
                    )
                  : stepState(selectedStep) === 'pending'
                    ? word(
                        lang,
                        'This sample step depends on the preceding checkpoint. It has not been executed.',
                        '前の確認Gateに依存するサンプルStepです。未実行です。',
                      )
                    : word(
                        lang,
                        'Sample result retained for inspection. This is a UI fixture, not evidence from a real agent run.',
                        '確認用のサンプル結果を表示しています。UI用データであり、実際のAgent実行Evidenceではありません。',
                      )}
            </p>
          </div>
        </Panel>
      </div>
      <div className="two-columns">
        <Panel
          title={word(lang, 'Execution log', '実行ログ')}
          eyebrow={word(lang, 'SAMPLE TRACE', 'サンプルトレース')}
          action={<Terminal size={17} />}
        >
          <ol className="ws-console">
            <li>
              <span>00:00.000</span>
              <Badge>Demo</Badge>
              <code>
                {word(
                  lang,
                  'Plan snapshot loaded · revision 1',
                  '計画スナップショット読込 · revision 1',
                )}
              </code>
            </li>
            <li>
              <span>00:00.240</span>
              <Circle size={10} />
              <code>{word(lang, 'Inspect sources → complete', 'ソース確認 → 完了')}</code>
            </li>
            <li>
              <span>00:00.680</span>
              {task.state === 'failed' ? <AlertCircle size={13} /> : <Circle size={10} />}
              <code>
                {task.state === 'failed'
                  ? word(
                      lang,
                      'SOURCE_UNAVAILABLE · paused at step 02',
                      'SOURCE_UNAVAILABLE · Step 02で停止',
                    )
                  : word(
                      lang,
                      'Context extracted · sample result retained',
                      '文脈抽出 · サンプル結果を保持',
                    )}
              </code>
            </li>
            <li>
              <span>00:01.120</span>
              <ShieldCheck size={13} />
              <code>
                {task.state === 'completed'
                  ? word(
                      lang,
                      'Sample plan completed · no real execution',
                      'サンプル計画完了 · 実実行なし',
                    )
                  : word(
                      lang,
                      'Execution halted · no automatic retry',
                      '実行停止 · 自動再試行なし',
                    )}
              </code>
            </li>
          </ol>
        </Panel>
        <Panel
          title={word(lang, 'Crash recovery', 'Crash Recovery')}
          eyebrow={word(lang, 'CHECKPOINT INSPECTOR', '確認点インスペクター')}
          action={<Badge>Demo snapshot</Badge>}
        >
          <div className="ws-recovery">
            <div className="ws-recovery-symbol">
              <ShieldCheck size={23} />
            </div>
            <div>
              <h3>{word(lang, 'Sample checkpoint available', 'サンプル確認点あり')}</h3>
              <p>
                {word(
                  lang,
                  'Inspect the saved plan before resuming. This UI does not restore or start an agent process.',
                  '再開前に保存済み計画を確認します。このUIはAgentプロセスの復元・開始を行いません。',
                )}
              </p>
            </div>
          </div>
          <dl className="detail-list">
            <div>
              <dt>{word(lang, 'Snapshot', 'スナップショット')}</dt>
              <dd className="mono">demo-checkpoint-001</dd>
            </div>
            <div>
              <dt>{word(lang, 'Recovery', '復旧')}</dt>
              <dd>
                {word(lang, 'Unavailable · adapter not connected', '利用不可 · Adapter未接続')}
              </dd>
            </div>
          </dl>
        </Panel>
      </div>
      {action && (
        <Modal
          title={
            action === 'retry'
              ? word(lang, 'Review sample retry', 'サンプル再試行を確認')
              : word(lang, 'Review sample cancellation', 'サンプルキャンセルを確認')
          }
          onClose={() => setAction(null)}
          closeLabel={word(lang, 'Close', '閉じる')}
        >
          <Badge tone="amber">Demo · {word(lang, 'Preview only', 'プレビューのみ')}</Badge>
          <p className="ws-modal-subject">{task.title[ix]}</p>
          <p className="ws-modal-copy">
            {word(
              lang,
              'This records a preview decision in this view only. No task will run, stop, resume or change state. Real execution requires a reviewed planner API and backend approval gate.',
              'この画面内にプレビューの判断だけを記録します。タスクの実行・停止・再開・状態変更は行いません。実行にはレビュー済みPlanner APIとBackend承認Gateが必要です。',
            )}
          </p>
          <dl className="detail-list">
            <div>
              <dt>{word(lang, 'Requested intent', '確認する意図')}</dt>
              <dd>
                {action === 'retry'
                  ? word(lang, 'Retry failed sample step', '失敗したサンプルStepを再試行')
                  : word(lang, 'Cancel sample plan', 'サンプル計画をキャンセル')}
              </dd>
            </div>
            <div>
              <dt>{word(lang, 'Execution authority', '実行権限')}</dt>
              <dd>{word(lang, 'None · Demo cannot authorize', 'なし · Demoで実行承認は不可')}</dd>
            </div>
          </dl>
          <div className="modal-actions">
            <Button onClick={() => setAction(null)}>{word(lang, 'Back', '戻る')}</Button>
            <Button
              variant="primary"
              onClick={() => {
                setNotice(
                  word(
                    lang,
                    `Demo only · ${action === 'retry' ? 'Retry' : 'Cancel'} preview recorded. No task state or agent process changed.`,
                    `Demoのみ · ${action === 'retry' ? '再試行' : 'キャンセル'}のプレビューを記録しました。タスクの状態・Agentプロセスは変更していません。`,
                  ),
                );
                setAction(null);
              }}
            >
              {word(lang, 'Record preview only', 'プレビューのみ記録')}
            </Button>
          </div>
        </Modal>
      )}
    </div>
  );
}
