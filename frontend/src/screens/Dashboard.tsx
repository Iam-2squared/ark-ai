import {
  Activity,
  ArrowRight,
  ArrowUpRight,
  Cpu,
  Database,
  Layers,
  MessageSquare,
  ShieldCheck,
  Workflow,
  Zap,
  Check,
  Circle,
} from 'lucide-react';
import { Badge, Button, Panel, word, type Language } from '../components/ui';
import type { ArkConnection } from '../data/useArk';

export function Dashboard({
  ark,
  demo,
  lang,
  navigate,
}: {
  ark: ArkConnection;
  demo: boolean;
  lang: Language;
  navigate: (screen: string) => void;
}) {
  const { status, connected } = ark;
  const stateLabel = !connected
    ? word(lang, 'Disconnected', '未接続')
    : demo
      ? word(lang, 'Demo environment', 'Demo環境')
      : status?.state === 'ready'
        ? word(lang, 'Ready for conversation', '会話の準備完了')
        : status?.state === 'generating'
          ? word(lang, 'Generating response', '回答を生成中')
          : status?.state === 'error'
            ? word(lang, 'Needs attention', '確認が必要')
            : word(lang, 'Loading runtime', 'ランタイム準備中');
  const now = new Date();
  return (
    <div className="screen-stack dashboard">
      <div className="page-intro">
        <div>
          <div className="eyebrow">YOUR PERSONAL AI WORKSPACE</div>
          <h1>
            {word(lang, 'Command Center', 'コマンドセンター')}
            <span className="heading-period">.</span>
          </h1>
          <p>
            {word(
              lang,
              'Everything you need. A little more in focus.',
              '必要な情報をひとつに。次の一歩を、もっと明確に。',
            )}
          </p>
        </div>
        <div className="date-label">
          {now.toLocaleDateString(lang === 'ja' ? 'ja-JP' : 'en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
            year: 'numeric',
          })}
        </div>
      </div>
      <section className="command-hero">
        <div className="hero-content">
          <Badge tone={demo ? 'amber' : connected ? 'cyan' : 'neutral'}>
            <span className="status-dot" />
            {stateLabel}
          </Badge>
          <h2>
            {word(lang, 'A quiet space.', '落ち着いた空間。')}
            <br />
            <span>{word(lang, 'A capable companion.', '頼れるパートナー。')}</span>
          </h2>
          <p>
            {word(
              lang,
              'Think, create and move forward with ARK. Your intelligence, connected in one place.',
              'ARKと考え、つくり、前へ進む。あなたのための知能を、ひとつの場所に。',
            )}
          </p>
          <Button variant="primary" onClick={() => navigate('conversation')}>
            <MessageSquare size={16} />
            {word(lang, 'Start a conversation', '会話を始める')}
            <ArrowUpRight size={16} />
          </Button>
          <div className="hero-footnote">
            <ShieldCheck size={13} />
            {demo
              ? word(lang, 'Interface demonstration · no model connected', 'UIデモ · モデル未接続')
              : word(
                  lang,
                  'Loopback session · no offline attestation',
                  'Loopbackセッション · オフライン証明ではありません',
                )}
          </div>
        </div>
        <div className="core-visual" aria-hidden="true">
          <div className="orbit orbit-one" />
          <div className="orbit orbit-two" />
          <div className="orbit orbit-three" />
          <div className="core-cross core-cross-h" />
          <div className="core-cross core-cross-v" />
          <div className="core-center">
            <img src="/ark.svg" alt="" />
          </div>
          <span className="core-coordinate coordinate-one">ARK / INTELLIGENCE</span>
          <span className="core-coordinate coordinate-two">
            {demo ? 'INTERFACE DEMO' : 'LOCAL SESSION'}
          </span>
          <span className="orbit-point point-one" />
          <span className="orbit-point point-two" />
        </div>
      </section>
      <div className="metrics-grid">
        {[
          {
            icon: <Cpu size={17} />,
            label: word(lang, 'Inference runtime', '推論ランタイム'),
            value: demo
              ? 'Demo'
              : !connected
                ? '—'
                : status?.model?.local_model
                  ? 'Local'
                  : status?.model
                    ? 'Mock'
                    : '—',
            note: demo
              ? word(lang, 'No LLM inference', 'LLM推論なし')
              : status?.model?.name ||
                word(lang, 'Connect a local runtime', 'ローカルランタイムに接続'),
            screen: 'settings',
          },
          {
            icon: <Activity size={17} />,
            label: word(lang, 'System resources', 'システム資源'),
            value: word(lang, 'Unavailable', '利用不可'),
            note: word(lang, 'CPU / GPU / RAM not exposed', 'CPU / GPU / RAM API未公開'),
            screen: 'settings',
          },
          {
            icon: <Database size={17} />,
            label: word(lang, 'Long-term memory', '長期記憶'),
            value: demo ? word(lang, 'Explore', '見る') : word(lang, 'Unavailable', '利用不可'),
            note: demo
              ? word(lang, 'Demo dataset · preview only', 'Demoデータ · プレビュー専用')
              : word(lang, 'No Memory API on main', 'mainにMemory APIなし'),
            screen: 'memory',
          },
          {
            icon: <Workflow size={17} />,
            label: word(lang, 'Agent workspace', 'Agentワークスペース'),
            value: demo
              ? word(lang, 'Preview', 'プレビュー')
              : word(lang, 'Unavailable', '利用不可'),
            note: demo
              ? word(lang, 'Sample plans · no execution', 'サンプル計画 · 実行なし')
              : word(lang, 'Agent runtime not connected', 'Agentランタイム未接続'),
            screen: 'agents',
          },
        ].map((item) => (
          <button
            className="metric-card"
            key={item.screen + item.label}
            onClick={() => navigate(item.screen)}
          >
            <div className="metric-label">
              {item.icon}
              <span>{item.label}</span>
              <ArrowUpRight size={14} />
            </div>
            <div className="metric-value">{item.value}</div>
            <div className="metric-note">{item.note}</div>
          </button>
        ))}
      </div>
      <div className="dashboard-grid">
        <Panel
          title={word(lang, 'Workspace overview', 'ワークスペース概要')}
          eyebrow="AT A GLANCE"
          action={<Badge tone="neutral">{demo ? 'DEMO' : 'LOCAL API'}</Badge>}
        >
          <div className="capability-list">
            {[
              [
                <MessageSquare size={18} />,
                word(lang, 'Conversation', '会話'),
                word(lang, 'Your direct line to ARK', 'ARKと直接対話する'),
                demo ? 'Demo' : connected ? 'API' : 'Unavailable',
                'conversation',
              ],
              [
                <Layers size={18} />,
                word(lang, 'Memory & context', '記憶とContext'),
                word(lang, 'Keep what matters within reach', '大切な情報に、いつでも届く'),
                demo ? 'Demo' : 'Unavailable',
                'memory',
              ],
              [
                <Workflow size={18} />,
                word(lang, 'Planning & execution', '計画と実行'),
                word(lang, 'Follow every step of the process', '計画の各ステップを確認する'),
                demo ? 'Demo' : 'Unavailable',
                'agents',
              ],
            ].map(([icon, title, description, badge, screen]) => (
              <button
                className="capability-row"
                key={String(screen)}
                onClick={() => navigate(String(screen))}
              >
                <span className="capability-icon">{icon}</span>
                <span>
                  <strong>{title}</strong>
                  <small>{description}</small>
                </span>
                <Badge tone={badge === 'API' ? 'cyan' : badge === 'Demo' ? 'amber' : 'neutral'}>
                  {badge}
                </Badge>
                <ArrowRight size={15} />
              </button>
            ))}
          </div>
          <div className="panel-footer">
            <ShieldCheck size={14} />
            {word(
              lang,
              'Tool execution and device capture are disabled.',
              'Tool実行とデバイス取得は無効です。',
            )}
          </div>
        </Panel>
        <Panel
          title={word(lang, 'Runtime details', 'ランタイム詳細')}
          eyebrow="CONNECTED INTELLIGENCE"
          action={<Zap size={17} className="accent" />}
        >
          <div className="runtime-identity">
            <span className="runtime-mark">
              <img src="/ark.svg" alt="" />
            </span>
            <div>
              <strong>
                {demo ? 'ARK Demo Adapter' : status?.model?.family || 'ARK Local Runtime'}
              </strong>
              <p>
                {demo
                  ? word(lang, 'Deterministic · no model', '定型応答 · モデルなし')
                  : status?.model?.quantization || word(lang, 'Awaiting backend', 'Backend待機中')}
              </p>
            </div>
          </div>
          <dl className="runtime-grid">
            <div>
              <dt>{word(lang, 'Intelligence', '推論基盤')}</dt>
              <dd>{status?.intelligence || '—'}</dd>
            </div>
            <div>
              <dt>{word(lang, 'Context capacity', 'Context容量')}</dt>
              <dd>
                {status?.model?.context_capacity.toLocaleString() || '—'}
                <small>{status?.model ? ' tokens' : ''}</small>
              </dd>
            </div>
            <div>
              <dt>{word(lang, 'Session logging', 'セッションログ')}</dt>
              <dd>{!status ? '—' : status.logging ? 'Local JSONL' : word(lang, 'Off', 'オフ')}</dd>
            </div>
            <div>
              <dt>{word(lang, 'Network isolation', 'ネットワーク分離')}</dt>
              <dd>{word(lang, 'Not attested', '未証明')}</dd>
            </div>
          </dl>
          <button className="panel-link" onClick={() => navigate('settings')}>
            {word(lang, 'View runtime settings', 'ランタイム設定を見る')}
            <ArrowRight size={14} />
          </button>
        </Panel>
      </div>
      <div className="dashboard-grid lower-grid">
        <Panel
          title={word(lang, 'Recent activity', '最近のアクティビティ')}
          action={
            <Badge>
              {demo
                ? word(lang, 'Sample timeline', 'サンプル履歴')
                : word(lang, 'Session only', '現セッションのみ')}
            </Badge>
          }
        >
          <div className="activity-list">
            {demo ? (
              [
                [
                  word(lang, 'Command Center preview opened', 'Command Centerプレビューを開始'),
                  word(lang, 'UI demonstration · sample event', 'UIデモ · サンプルイベント'),
                  'UI',
                ],
                [
                  word(lang, 'Conversation adapter is available', '会話Adapterを利用可能'),
                  word(
                    lang,
                    'Demo responses are generated in memory',
                    'Demo応答はメモリ内で生成されます',
                  ),
                  'CHAT',
                ],
                [
                  word(lang, 'Permission boundaries preserved', '権限の境界を維持'),
                  word(
                    lang,
                    'No tools, camera or microphone connected',
                    'Tool・カメラ・マイクは未接続',
                  ),
                  'SAFETY',
                ],
              ].map(([title, description, tag]) => (
                <div className="activity-item" key={tag}>
                  <span className="activity-symbol">
                    <Check size={13} />
                  </span>
                  <div>
                    <strong>{title}</strong>
                    <p>{description}</p>
                  </div>
                  <span className="activity-tag">{tag}</span>
                </div>
              ))
            ) : status?.messages.length ? (
              status.messages.slice(-3).map((m, i) => (
                <div className="activity-item" key={i}>
                  <span className="activity-symbol">
                    <MessageSquare size={13} />
                  </span>
                  <div>
                    <strong>
                      {m.role === 'user'
                        ? word(lang, 'Message sent', 'メッセージ送信')
                        : word(lang, 'Response received', '回答受信')}
                    </strong>
                    <p>{m.content.slice(0, 100)}</p>
                  </div>
                </div>
              ))
            ) : (
              <p className="muted padded">
                {word(
                  lang,
                  'No conversation activity in this session.',
                  'このセッションの会話履歴はありません。',
                )}
              </p>
            )}
          </div>
        </Panel>
        <Panel
          title={word(lang, 'System notices', 'システム通知')}
          action={
            <span className="notification-count">
              {status?.error || status?.warning ? '2' : '1'}
            </span>
          }
        >
          <div className="system-notice">
            <span className="notice-symbol">
              <Circle size={16} />
            </span>
            <div>
              <h3>{word(lang, 'A foundation for what’s next', '次の進化のための基盤')}</h3>
              <p>
                {word(
                  lang,
                  'Memory, agents and multimodal services await backend integration. Explore their workspaces in Demo.',
                  'Memory・Agent・マルチモーダルはBackend統合待ちです。Demoで操作を確認できます。',
                )}
              </p>
              <button className="text-button" onClick={() => navigate('tools')}>
                {word(lang, 'Review permissions', '権限を確認')}
                <ArrowRight size={13} />
              </button>
            </div>
          </div>
          {(status?.error || status?.warning) && (
            <p className="alert-text padded" role="alert">
              {status.error || status.warning}
            </p>
          )}
          <div className="panel-footer">
            <ShieldCheck size={14} />
            {word(lang, 'No external tool actions enabled', '外部Tool操作は無効です')}
          </div>
        </Panel>
      </div>
    </div>
  );
}
