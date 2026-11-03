import { useState } from 'react';
import {
  Search,
  ShieldCheck,
  FileSearch,
  Terminal,
  FolderOpen,
  ChevronRight,
  LockKeyhole,
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

type Tool = {
  id: string;
  name: string;
  access: 'READ' | 'WRITE';
  description: [string, string];
  scope: string;
  capability: string;
};

const examples: Tool[] = [
  {
    id: 'files.search',
    name: 'File search',
    access: 'READ',
    description: [
      'Find documents within an explicitly selected workspace.',
      '明示的に選択したワークスペース内の文書を検索します。',
    ],
    scope: 'workspace/documents/**',
    capability: 'filesystem.search',
  },
  {
    id: 'files.read',
    name: 'Read document',
    access: 'READ',
    description: [
      'Read a local document without modifying its contents.',
      'ローカル文書を変更せずに読み取ります。',
    ],
    scope: 'workspace/documents/**',
    capability: 'filesystem.read',
  },
  {
    id: 'files.write',
    name: 'Write document',
    access: 'WRITE',
    description: [
      'Propose a file change for explicit human review.',
      'ファイルの変更案を作成し、明示的な確認を求めます。',
    ],
    scope: 'workspace/drafts/**',
    capability: 'filesystem.write',
  },
  {
    id: 'python.sandbox',
    name: 'Python sandbox',
    access: 'WRITE',
    description: [
      'Proposed isolated computation. Execution is not connected.',
      '隔離された計算環境の構想です。実行機能は未接続です。',
    ],
    scope: 'isolated-session',
    capability: 'sandbox.execute',
  },
];

export function Tools({ demo, lang }: { demo: boolean; lang: Language }) {
  const [query, setQuery] = useState('');
  const [access, setAccess] = useState<'ALL' | 'READ' | 'WRITE'>('ALL');
  const [selected, setSelected] = useState(examples[0].id);
  const [preview, setPreview] = useState(false);
  const [decision, setDecision] = useState<string | null>(null);
  const current = examples.find((tool) => tool.id === selected) ?? examples[0];
  const filtered = examples.filter(
    (tool) =>
      (access === 'ALL' || tool.access === access) &&
      `${tool.name} ${tool.id} ${tool.scope} ${tool.capability}`
        .toLowerCase()
        .includes(query.toLowerCase()),
  );
  if (!demo)
    return (
      <div className="screen-stack">
        <Notice>
          {word(
            lang,
            'Tool execution is unavailable in this UI. The current backend exposes conversation APIs only.',
            'このUIではToolを実行できません。現行Backendが公開しているのは会話APIのみです。',
          )}
        </Notice>
        <Panel
          title={word(lang, 'Tools & permissions', 'Toolと権限')}
          action={<Badge>{word(lang, 'Unavailable', '利用不可')}</Badge>}
        >
          <EmptyState
            title={word(lang, 'Registry not connected', 'Registryは未接続です')}
            icon={<LockKeyhole size={24} />}
          >
            {word(
              lang,
              'A reviewed registry and approval API are required before real capabilities, scopes or audits can be shown. No tool requests are sent.',
              '実際のCapability・Scope・監査を表示するには、レビュー済みのRegistryと承認APIが必要です。Toolリクエストは送信されません。',
            )}
          </EmptyState>
        </Panel>
      </div>
    );
  return (
    <div className="screen-stack">
      <DemoNotice lang={lang} />
      {decision && <Notice>{decision}</Notice>}
      <div className="two-columns ws-tool-grid">
        <Panel
          title={word(lang, 'Tool registry', 'Tool Registry')}
          eyebrow="DEMO REGISTRY"
          action={<Badge tone="cyan">4 {word(lang, 'samples', 'サンプル')}</Badge>}
        >
          <div className="toolbar ws-toolbar">
            <label className="search-field">
              <Search size={16} />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder={word(lang, 'Search tools or scopes…', 'Tool・Scopeを検索…')}
                aria-label={word(lang, 'Search tools', 'Toolを検索')}
              />
            </label>
          </div>
          <div
            className="tabs ws-tabs"
            aria-label={word(lang, 'Filter tool access', '権限で絞り込み')}
          >
            {(['ALL', 'READ', 'WRITE'] as const).map((value) => (
              <button
                key={value}
                className={`tab ${access === value ? 'active' : ''}`}
                aria-pressed={access === value}
                onClick={() => setAccess(value)}
              >
                {value === 'ALL' ? word(lang, 'All tools', 'すべて') : value}
              </button>
            ))}
          </div>
          <div className="ws-record-list">
            {filtered.length ? (
              filtered.map((tool) => (
                <button
                  key={tool.id}
                  className={`list-row ws-record ${selected === tool.id ? 'selected' : ''}`}
                  onClick={() => setSelected(tool.id)}
                  aria-pressed={selected === tool.id}
                >
                  <span className="ws-record-icon">
                    {tool.id.includes('search') ? (
                      <FileSearch size={19} />
                    ) : tool.id.includes('python') ? (
                      <Terminal size={19} />
                    ) : (
                      <FolderOpen size={19} />
                    )}
                  </span>
                  <span className="ws-record-copy">
                    <strong>{tool.name}</strong>
                    <span className="mono muted">{tool.id}</span>
                  </span>
                  <Badge tone={tool.access === 'WRITE' ? 'amber' : 'cyan'}>{tool.access}</Badge>
                  <ChevronRight size={15} />
                </button>
              ))
            ) : (
              <EmptyState title={word(lang, 'No matching tools', '該当するToolはありません')}>
                {word(
                  lang,
                  'Try a different name, scope or access filter.',
                  '名前・Scope・権限の条件を変更してください。',
                )}
              </EmptyState>
            )}
          </div>
          <p className="demo-note">
            {word(
              lang,
              'Sample capabilities only. Nothing in this registry can execute.',
              'サンプルCapabilityです。このRegistryから実行される処理はありません。',
            )}
          </p>
        </Panel>
        <Panel
          title={current.name}
          eyebrow="CAPABILITY DETAIL"
          action={
            <Badge tone={current.access === 'WRITE' ? 'amber' : 'cyan'}>{current.access}</Badge>
          }
        >
          <p className="muted ws-intro">{word(lang, ...current.description)}</p>
          <dl className="detail-list">
            <div>
              <dt>{word(lang, 'Tool ID', 'Tool ID')}</dt>
              <dd className="mono">{current.id}</dd>
            </div>
            <div>
              <dt>Capability</dt>
              <dd className="mono">{current.capability}</dd>
            </div>
            <div>
              <dt>Scope</dt>
              <dd className="mono">{current.scope}</dd>
            </div>
            <div>
              <dt>{word(lang, 'Execution', '実行')}</dt>
              <dd>{word(lang, 'Unavailable · Demo only', '利用不可 · Demoのみ')}</dd>
            </div>
            <div>
              <dt>{word(lang, 'Approval policy', '承認方針')}</dt>
              <dd>
                {word(
                  lang,
                  'Explicit review before any future WRITE',
                  '将来のWRITE実行前に明示的に確認',
                )}
              </dd>
            </div>
          </dl>
          <div className="ws-card-note">
            <ShieldCheck size={18} />
            <p>
              {word(
                lang,
                'Inspect the approval experience without granting a capability or executing an action.',
                '権限の付与やActionの実行をせずに、承認画面を確認できます。',
              )}
            </p>
          </div>
          <Button onClick={() => setPreview(true)}>
            <ShieldCheck size={16} />
            {word(lang, 'Preview approval', '承認画面をプレビュー')}
          </Button>
        </Panel>
      </div>
      <Panel
        title={word(lang, 'Action audit', 'Action監査')}
        eyebrow="DEMO EVENT"
        action={<Badge>Demo</Badge>}
      >
        <div className="ws-audit-row">
          <span className="ws-record-icon">
            <FileSearch size={19} />
          </span>
          <div className="ws-record-copy">
            <strong>files.search</strong>
            <span className="muted">
              {word(
                lang,
                'Sample request · workspace/documents/**',
                'サンプル要求 · workspace/documents/**',
              )}
            </span>
          </div>
          <Badge>{word(lang, 'Preview only', 'プレビューのみ')}</Badge>
        </div>
        <dl className="detail-list">
          <div>
            <dt>{word(lang, 'Sample result', 'サンプル結果')}</dt>
            <dd>
              {word(
                lang,
                '3 example document references. No files were read.',
                '文書参照のサンプル3件。ファイルは読み取っていません。',
              )}
            </dd>
          </div>
          <div>
            <dt>{word(lang, 'Provenance', '出所')}</dt>
            <dd>
              {word(
                lang,
                'UI fixture · not an execution record',
                'UIサンプル · 実行記録ではありません',
              )}
            </dd>
          </div>
        </dl>
      </Panel>
      {preview && (
        <Modal
          title={word(lang, 'Approval preview · Demo', '承認プレビュー · Demo')}
          onClose={() => setPreview(false)}
          closeLabel={word(lang, 'Close', '閉じる')}
        >
          <Notice tone="warning">
            {word(
              lang,
              'This is a UI rehearsal. Confirming records an in-memory preview decision only. It grants no permission and runs no tool.',
              'これはUIの確認です。確定してもメモリ内にプレビュー結果を記録するだけです。権限付与やTool実行は行いません。',
            )}
          </Notice>
          <dl className="detail-list">
            <div>
              <dt>Tool</dt>
              <dd className="mono">{current.id}</dd>
            </div>
            <div>
              <dt>Scope</dt>
              <dd className="mono">{current.scope}</dd>
            </div>
            <div>
              <dt>{word(lang, 'Effect', '効果')}</dt>
              <dd>{word(lang, 'None · Preview only', 'なし · プレビューのみ')}</dd>
            </div>
          </dl>
          <div className="modal-actions">
            <Button onClick={() => setPreview(false)}>{word(lang, 'Dismiss', '閉じる')}</Button>
            <Button
              variant="primary"
              onClick={() => {
                setPreview(false);
                setDecision(
                  word(
                    lang,
                    `Demo preview decision recorded for ${current.id}. No permission was granted and no action was executed.`,
                    `${current.id}のDemoプレビュー結果を記録しました。権限の付与・Actionの実行は行っていません。`,
                  ),
                );
              }}
            >
              {word(lang, 'Confirm preview', 'プレビューを確定')}
            </Button>
          </div>
        </Modal>
      )}
    </div>
  );
}
