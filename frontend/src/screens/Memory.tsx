import { useId, useState } from 'react';
import {
  BookOpen,
  Search,
  Database,
  Pencil,
  Trash2,
  GitBranch,
  Clock3,
  FileText,
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

interface MemoryRecord {
  id: string;
  namespace: 'projects' | 'preferences' | 'knowledge';
  title: [string, string];
  content: [string, string];
  tags: string[];
  source: [string, string];
  history: [string, string][];
  revision: number;
}
const samples: MemoryRecord[] = [
  {
    id: 'demo-mem-001',
    namespace: 'projects',
    title: ['ARK AI · Design principles', 'ARK AI · 設計原則'],
    content: [
      'Build a local-first personal assistant. Keep inference, memory, tools and planning modular. Every capability should have a measurable completion gate.',
      'ローカル優先のパーソナルAIを開発する。推論・記憶・Tool・計画を分離し、各機能には測定可能な完了Gateを設ける。',
    ],
    tags: ['ARK AI', 'architecture', 'local-first'],
    source: ['Sample conversation · architecture review', 'サンプル会話 · 設計レビュー'],
    history: [['Sample record created', 'サンプル記録を作成']],
    revision: 1,
  },
  {
    id: 'demo-mem-002',
    namespace: 'preferences',
    title: ['Communication preferences', 'コミュニケーションの好み'],
    content: [
      'Use concise answers for quick questions. Explain decisions and practical limits when discussing engineering work.',
      '短い質問には簡潔に回答する。技術的な作業では判断の理由と実用上の制限を説明する。',
    ],
    tags: ['communication', 'preferences'],
    source: ['Sample conversation · preferences', 'サンプル会話 · 好み'],
    history: [['Sample record created', 'サンプル記録を作成']],
    revision: 1,
  },
  {
    id: 'demo-mem-003',
    namespace: 'knowledge',
    title: ['Memory provenance', '記憶の出典管理'],
    content: [
      'A useful memory retains its source and revision history. Retrieved content is context, never permission to run an action.',
      '有用な記憶には出典と変更履歴を保持する。取得した内容は文脈であり、操作を実行する権限ではない。',
    ],
    tags: ['provenance', 'safety'],
    source: ['Sample note · memory architecture', 'サンプルノート · 記憶設計'],
    history: [['Sample record created', 'サンプル記録を作成']],
    revision: 1,
  },
  {
    id: 'demo-mem-004',
    namespace: 'projects',
    title: ['Next interface integration', '次のUI統合'],
    content: [
      'Connect read-only memory and planner endpoints once their contracts are reviewed. Preserve the existing conversation API boundary.',
      '契約のレビュー完了後にMemoryとPlannerの読み取りAPIを接続する。既存の会話APIの境界を維持する。',
    ],
    tags: ['UI', 'integration'],
    source: ['Sample plan · interface roadmap', 'サンプル計画 · UIロードマップ'],
    history: [['Sample record created', 'サンプル記録を作成']],
    revision: 1,
  },
];

export function Memory({ demo, lang }: { demo: boolean; lang: Language }) {
  const [records, setRecords] = useState<MemoryRecord[]>(samples);
  const [query, setQuery] = useState('');
  const [namespace, setNamespace] = useState('all');
  const [selectedId, setSelectedId] = useState(samples[0].id);
  const [action, setAction] = useState<'edit' | 'delete' | null>(null);
  const [draft, setDraft] = useState('');
  const [notice, setNotice] = useState('');
  const searchId = useId();
  const namespaceId = useId();
  const editId = useId();
  const ix = lang === 'ja' ? 1 : 0;
  const filtered = records.filter(
    (record) =>
      (namespace === 'all' || record.namespace === namespace) &&
      `${record.title.join(' ')} ${record.content.join(' ')} ${record.tags.join(' ')}`
        .toLowerCase()
        .includes(query.toLowerCase()),
  );
  const selected = filtered.find((record) => record.id === selectedId) ?? filtered[0];
  const nsLabel = (value: string) =>
    ({
      projects: word(lang, 'Projects', 'プロジェクト'),
      preferences: word(lang, 'Preferences', '好み'),
      knowledge: word(lang, 'Knowledge', '知識'),
    })[value];

  if (!demo)
    return (
      <div className="screen-stack">
        <Notice>
          {word(
            lang,
            'Memory API is not available in the current backend. No memory store has been connected.',
            '現在のBackendにはMemory APIがありません。記憶ストアには接続していません。',
          )}
        </Notice>
        <Panel
          title={word(lang, 'Long-term memory', '長期記憶')}
          action={<Badge>{word(lang, 'Unavailable', '利用不可')}</Badge>}
        >
          <EmptyState
            title={word(lang, 'Your memory workspace is waiting', '記憶ワークスペースは未接続です')}
            icon={<Database size={24} />}
          >
            {word(
              lang,
              'Search, provenance and review controls will become available after a reviewed memory adapter is connected. Switch to Demo to explore sample records.',
              'レビュー済みのMemory Adapter接続後に、検索・出典・レビュー機能を利用できます。Demoではサンプル記録を確認できます。',
            )}
          </EmptyState>
        </Panel>
      </div>
    );

  function commit() {
    if (!selected || !action) return;
    if (action === 'delete') {
      setRecords((previous) => previous.filter((record) => record.id !== selected.id));
      setNotice(
        word(
          lang,
          'Demo only · Sample record removed from this view. No stored memory was deleted.',
          'Demoのみ · この画面からサンプルを削除しました。実際の記憶は削除していません。',
        ),
      );
    } else {
      setRecords((previous) =>
        previous.map((record) =>
          record.id === selected.id
            ? {
                ...record,
                content:
                  ix === 1 ? [record.content[0], draft.trim()] : [draft.trim(), record.content[1]],
                revision: record.revision + 1,
                history: [
                  ...record.history,
                  ['Demo edit reviewed in this view', 'この画面でDemo編集を確認'],
                ],
              }
            : record,
        ),
      );
      setNotice(
        word(
          lang,
          'Demo only · Sample change applied in memory. No backend memory was updated.',
          'Demoのみ · サンプルの変更を画面内に反映しました。Backendの記憶は更新していません。',
        ),
      );
    }
    setAction(null);
  }

  return (
    <div className="screen-stack">
      <DemoNotice lang={lang} />
      {notice && <Notice>{notice}</Notice>}
      <div className="ws-memory-layout">
        <Panel
          title={word(lang, 'Memory library', '記憶ライブラリ')}
          eyebrow={word(lang, 'KNOWLEDGE & CONTEXT', '知識と文脈')}
          action={<Badge tone="cyan">Demo · {records.length}</Badge>}
        >
          <div className="ws-memory-controls">
            <label className="ws-search" htmlFor={searchId}>
              <Search size={16} />
              <input
                id={searchId}
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder={word(lang, 'Search memories…', '記憶を検索…')}
                aria-label={word(lang, 'Search memories', '記憶を検索')}
              />
            </label>
            <label className="ws-namespace" htmlFor={namespaceId}>
              <span>{word(lang, 'Namespace', 'Namespace')}</span>
              <select
                id={namespaceId}
                value={namespace}
                onChange={(event) => setNamespace(event.target.value)}
              >
                <option value="all">{word(lang, 'All namespaces', 'すべて')}</option>
                {['projects', 'preferences', 'knowledge'].map((value) => (
                  <option key={value} value={value}>
                    {nsLabel(value)}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div
            className="ws-memory-list"
            aria-label={word(lang, 'Sample memories', 'サンプル記憶')}
          >
            {filtered.length ? (
              filtered.map((record) => (
                <button
                  key={record.id}
                  className={`ws-memory-item ${selected?.id === record.id ? 'is-selected' : ''}`}
                  onClick={() => setSelectedId(record.id)}
                  aria-pressed={selected?.id === record.id}
                >
                  <span className="ws-record-symbol">
                    <BookOpen size={17} />
                  </span>
                  <span className="ws-record-main">
                    <strong>{record.title[ix]}</strong>
                    <span>{record.content[ix]}</span>
                    <span className="ws-record-meta">
                      <span className="ws-namespace-dot" />
                      {nsLabel(record.namespace)}
                      <span>·</span>
                      <span>v{record.revision}</span>
                    </span>
                  </span>
                </button>
              ))
            ) : (
              <EmptyState title={word(lang, 'No matching memories', '一致する記憶がありません')}>
                {word(
                  lang,
                  'Try another search or namespace.',
                  '検索語やNamespaceを変更してください。',
                )}
              </EmptyState>
            )}
          </div>
          <div className="ws-panel-foot">
            <span>
              {word(
                lang,
                `${filtered.length} sample records shown`,
                `${filtered.length}件のサンプルを表示`,
              )}
            </span>
            <span>{word(lang, 'Session only', '画面内のみ')}</span>
          </div>
        </Panel>
        <Panel
          title={word(lang, 'Memory detail', '記憶の詳細')}
          eyebrow={word(lang, 'INSPECT & REVIEW', '詳細とレビュー')}
          action={<Badge>Demo</Badge>}
        >
          {selected ? (
            <div className="ws-detail">
              <div className="ws-detail-top">
                <span className="ws-namespace-label">{nsLabel(selected.namespace)}</span>
                <span className="mono muted">{selected.id}</span>
              </div>
              <h3 className="ws-detail-title">{selected.title[ix]}</h3>
              <p className="ws-memory-content">{selected.content[ix]}</p>
              <div className="ws-tag-row">
                {selected.tags.map((tag) => (
                  <span className="ws-tag" key={tag}>
                    {tag}
                  </span>
                ))}
              </div>
              <div className="ws-detail-section">
                <h4>
                  <FileText size={15} />
                  {word(lang, 'Provenance', '出典')}
                </h4>
                <dl className="detail-list">
                  <div>
                    <dt>{word(lang, 'Source', 'ソース')}</dt>
                    <dd>{selected.source[ix]}</dd>
                  </div>
                  <div>
                    <dt>{word(lang, 'Origin', '由来')}</dt>
                    <dd>
                      {word(
                        lang,
                        'UI fixture · not a user memory',
                        'UI用サンプル · 実際のユーザー記憶ではありません',
                      )}
                    </dd>
                  </div>
                  <div>
                    <dt>{word(lang, 'Revision', 'リビジョン')}</dt>
                    <dd className="mono">v{selected.revision}</dd>
                  </div>
                </dl>
              </div>
              <div className="ws-detail-section">
                <h4>
                  <GitBranch size={15} />
                  {word(lang, 'Revision history', '変更履歴')}
                </h4>
                <ol className="ws-history">
                  {selected.history.map((item, index) => (
                    <li key={index}>
                      <Clock3 size={13} />
                      <span>{item[ix]}</span>
                      <span className="mono muted">v{index + 1}</span>
                    </li>
                  ))}
                </ol>
              </div>
              <div className="ws-detail-actions">
                <Button
                  onClick={() => {
                    setDraft(selected.content[ix]);
                    setAction('edit');
                  }}
                >
                  <Pencil size={14} />
                  {word(lang, 'Review sample edit', 'サンプル編集を確認')}
                </Button>
                <Button variant="ghost" onClick={() => setAction('delete')}>
                  <Trash2 size={14} />
                  {word(lang, 'Delete sample', 'サンプル削除')}
                </Button>
              </div>
              <p className="ws-inline-note">
                {word(
                  lang,
                  'Changes here are temporary and reset when this screen is reopened.',
                  'この画面内の変更は一時的です。画面を開き直すとリセットされます。',
                )}
              </p>
            </div>
          ) : (
            <EmptyState title={word(lang, 'Select a memory', '記憶を選択')}>
              {word(
                lang,
                'A matching sample will appear here.',
                '一致するサンプルを選択すると詳細を表示します。',
              )}
            </EmptyState>
          )}
        </Panel>
      </div>
      {action && selected && (
        <Modal
          title={
            action === 'edit'
              ? word(lang, 'Review sample edit', 'サンプル編集の確認')
              : word(lang, 'Delete this sample?', 'サンプルを削除しますか？')
          }
          closeLabel={word(lang, 'Close', '閉じる')}
          onClose={() => setAction(null)}
        >
          <Badge tone="amber">Demo · {word(lang, 'No backend action', 'Backend操作なし')}</Badge>
          <p className="ws-modal-copy">
            {action === 'edit'
              ? word(
                  lang,
                  'Review the proposed text before applying it to this temporary sample. This does not approve or update a real memory.',
                  '一時的なサンプルに反映する文章を確認してください。実際の記憶の承認・更新は行いません。',
                )
              : word(
                  lang,
                  'Only this in-memory sample will disappear from the view. No file, database or real memory is changed.',
                  'この画面内のサンプルだけを削除します。ファイル・データベース・実際の記憶は変更しません。',
                )}
          </p>
          <p className="ws-modal-subject">{selected.title[ix]}</p>
          {action === 'edit' && (
            <label className="form-field" htmlFor={editId}>
              {word(lang, 'Sample content', 'サンプル内容')}
              <textarea
                id={editId}
                rows={6}
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                maxLength={4000}
              />
            </label>
          )}
          <div className="modal-actions">
            <Button onClick={() => setAction(null)}>{word(lang, 'Cancel', 'キャンセル')}</Button>
            <Button
              variant={action === 'delete' ? 'danger' : 'primary'}
              disabled={action === 'edit' && !draft.trim()}
              onClick={commit}
            >
              {action === 'delete'
                ? word(lang, 'Delete sample only', 'サンプルのみ削除')
                : word(lang, 'Apply sample edit', 'サンプル編集を反映')}
            </Button>
          </div>
        </Modal>
      )}
    </div>
  );
}
