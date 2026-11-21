import { Component, useEffect, useRef, useState, type ReactNode } from 'react';
import {
  Activity,
  ArrowUpRight,
  Bell,
  ChevronDown,
  Command,
  Database,
  LayoutDashboard,
  Menu,
  MessageSquare,
  Search,
  Settings2,
  Shield,
  ShieldCheck,
  Workflow,
  ScanEye,
  X,
  RefreshCw,
} from 'lucide-react';
import { useArk } from './data/useArk';
import type { AdapterMode } from './data/contracts';
import { Badge, Button, Modal, Notice, word, type Language } from './components/ui';
import { Dashboard } from './screens/Dashboard';
import { Conversation } from './screens/Conversation';
import { Memory } from './screens/Memory';
import { Agents } from './screens/Agents';
import { Tools } from './screens/Tools';
import { Vision } from './screens/Vision';
import { Settings, type Preferences } from './screens/Settings';

const navigation = [
  {
    id: 'dashboard',
    en: 'Command Center',
    ja: 'コマンドセンター',
    icon: LayoutDashboard,
    shortcut: '1',
  },
  { id: 'conversation', en: 'Conversation', ja: '会話', icon: MessageSquare, shortcut: '2' },
  { id: 'memory', en: 'Memory', ja: '記憶', icon: Database, shortcut: '3' },
  { id: 'agents', en: 'Agent Workspace', ja: 'Agentワークスペース', icon: Workflow, shortcut: '4' },
  { id: 'tools', en: 'Tools & Permissions', ja: 'Toolと権限', icon: Shield, shortcut: '5' },
  { id: 'vision', en: 'Vision & Voice', ja: '視覚と音声', icon: ScanEye, shortcut: '6' },
  { id: 'settings', en: 'Settings', ja: '設定', icon: Settings2, shortcut: '7' },
] as const;
function screenFromHash() {
  const id = location.hash.slice(1);
  return navigation.some((item) => item.id === id) ? id : 'dashboard';
}
function loadPreferences(): Preferences {
  try {
    const value: unknown = JSON.parse(localStorage.getItem('ark-ui-preferences') || 'null');
    if (value && typeof value === 'object') {
      const p = value as Record<string, unknown>;
      return {
        language: p.language === 'ja' ? 'ja' : 'en',
        theme: p.theme === 'navy' ? 'navy' : 'graphite',
        reducedMotion: p.reducedMotion === true,
      };
    }
  } catch {
    /* Storage is optional. */
  }
  return { language: 'en', theme: 'graphite', reducedMotion: false };
}
class ErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? (
      <div className="fatal-error">
        <img src="/ark.svg" alt="ARK" />
        <h1>The workspace needs a refresh.</h1>
        <p>画面を再読み込みしてください。実行中のBackend処理は自動再送信されません。</p>
        <Button onClick={() => location.reload()}>Reload workspace</Button>
      </div>
    ) : (
      this.props.children
    );
  }
}
function Shell() {
  const [preferences, setPreferences] = useState<Preferences>(loadPreferences);
  const lang: Language = preferences.language;
  const [mode, setMode] = useState<AdapterMode>(import.meta.env.DEV ? 'demo' : 'local');
  const [screen, setScreen] = useState(screenFromHash);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [palette, setPalette] = useState(false);
  const [query, setQuery] = useState('');
  const [notices, setNotices] = useState(false);
  const sidebar = useRef<HTMLElement>(null);
  const menuButton = useRef<HTMLButtonElement>(null);
  const ark = useArk(mode);
  const demo = mode === 'demo';
  const heading = useRef<HTMLDivElement>(null);
  const current = navigation.find((item) => item.id === screen) || navigation[0];
  useEffect(() => {
    const change = () => {
      setScreen(screenFromHash());
      setMobileOpen(false);
    };
    window.addEventListener('hashchange', change);
    return () => window.removeEventListener('hashchange', change);
  }, []);
  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dataset.theme = preferences.theme;
    document.documentElement.dataset.reducedMotion = String(preferences.reducedMotion);
    try {
      localStorage.setItem('ark-ui-preferences', JSON.stringify(preferences));
    } catch {
      /* Works without persistence. */
    }
  }, [preferences, lang]);
  useEffect(() => {
    const handle = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setPalette((value) => !value);
      }
      if (event.key === 'Escape') {
        setMobileOpen(false);
        menuButton.current?.focus();
      }
    };
    window.addEventListener('keydown', handle);
    return () => window.removeEventListener('keydown', handle);
  }, []);
  useEffect(() => {
    if (mobileOpen) sidebar.current?.querySelector<HTMLButtonElement>('[data-close-nav]')?.focus();
  }, [mobileOpen]);
  const closeNav = () => {
    setMobileOpen(false);
    menuButton.current?.focus();
  };
  const navigate = (id: string) => {
    location.hash = id;
    setScreen(id);
    setMobileOpen(false);
    setPalette(false);
    setQuery('');
    heading.current?.focus({ preventScroll: true });
    window.scrollTo({ top: 0, behavior: 'instant' });
  };
  const phase = ark.loading
    ? word(lang, 'Connecting', '接続中')
    : !ark.connected
      ? word(lang, 'Disconnected', '未接続')
      : ark.status?.state === 'loading'
        ? word(lang, 'Loading runtime', 'ランタイム準備中')
        : ark.status?.state === 'generating'
          ? word(lang, 'Responding', '応答中')
          : ark.status?.state === 'error'
            ? word(lang, 'Needs attention', '確認が必要')
            : demo
              ? word(lang, 'Demo ready', 'Demo準備完了')
              : ark.status?.model?.local_model
                ? word(lang, 'Local model ready', 'モデル準備完了')
                : word(lang, 'Mock · no model', 'Mock · モデルなし');
  const changeLocked = ark.pending || ark.status?.state === 'generating';
  return (
    <div className="app-shell">
      <a
        className="skip-link"
        href="#main-content"
        onClick={(event) => {
          event.preventDefault();
          heading.current?.focus();
        }}
      >
        {word(lang, 'Skip to content', '本文へ移動')}
      </a>
      {mobileOpen && (
        <button
          className="sidebar-backdrop"
          aria-label={word(lang, 'Close navigation', 'メニューを閉じる')}
          onClick={closeNav}
        />
      )}
      <aside
        ref={sidebar}
        id="workspace-navigation"
        className={`sidebar ${mobileOpen ? 'is-open' : ''}`}
        role={mobileOpen ? 'dialog' : undefined}
        aria-modal={mobileOpen ? true : undefined}
        onKeyDown={(event) => {
          if (event.key !== 'Tab' || !mobileOpen) return;
          const items = Array.from(
            sidebar.current?.querySelectorAll<HTMLElement>('a[href],button:not([disabled])') || [],
          ).filter((item) => item.getClientRects().length);
          const first = items[0],
            last = items[items.length - 1];
          if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last?.focus();
          } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first?.focus();
          }
        }}
        aria-label={word(lang, 'Application navigation', 'アプリのナビゲーション')}
      >
        <button
          data-close-nav
          className="icon-button sidebar-close"
          onClick={closeNav}
          aria-label={word(lang, 'Close navigation', 'メニューを閉じる')}
        >
          <X size={18} />
        </button>
        <a className="brand" href="#dashboard" onClick={() => navigate('dashboard')}>
          <img src="/ark.svg" alt="" />
          <span>
            ARK<span className="brand-ai">AI</span>
            <small>PERSONAL INTELLIGENCE</small>
          </span>
        </a>
        <button className="workspace-selector" onClick={() => setNotices(true)}>
          <span className="workspace-avatar">P</span>
          <span>
            <strong>{word(lang, 'Personal workspace', '個人ワークスペース')}</strong>
            <small>{word(lang, 'Local-first environment', 'ローカル優先の環境')}</small>
          </span>
          <ChevronDown size={13} />
        </button>
        <div className="nav-group-label">WORKSPACE</div>
        <nav>
          {navigation.slice(0, 6).map((item) => (
            <a
              key={item.id}
              href={`#${item.id}`}
              className={`nav-item ${screen === item.id ? 'active' : ''}`}
              aria-current={screen === item.id ? 'page' : undefined}
              onClick={() => navigate(item.id)}
            >
              <item.icon size={18} />
              <span>{word(lang, item.en, item.ja)}</span>
              {screen === item.id && <span className="active-dot" />}
            </a>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-status">
            <div>
              <span className={`session-dot ${!ark.connected ? 'offline' : ''}`} />
              <strong>{phase}</strong>
            </div>
            <p>
              {demo
                ? word(lang, 'Demo · no model or devices', 'Demo · モデル・デバイス未接続')
                : word(lang, '127.0.0.1 · single shared session', '127.0.0.1 · 単一共有セッション')}
            </p>
            <div className="status-lines">
              <span />
              <span />
              <span />
              <span />
              <span />
              <span />
              <span />
              <span />
              <span />
              <span />
              <span />
              <span />
            </div>
          </div>
          <a
            className={`nav-item ${screen === 'settings' ? 'active' : ''}`}
            href="#settings"
            onClick={() => navigate('settings')}
            aria-current={screen === 'settings' ? 'page' : undefined}
          >
            <Settings2 size={18} />
            <span>{word(lang, 'Settings', '設定')}</span>
          </a>
          <div className="sidebar-profile">
            <span className="profile-avatar">Y</span>
            <div>
              <strong>{word(lang, 'Your space', 'あなたの空間')}</strong>
              <small>ARK AI · UI FOUNDATION</small>
            </div>
            <span className="profile-dot" />
          </div>
        </div>
      </aside>
      <div className="app-main" inert={mobileOpen ? true : undefined}>
        <header className="topbar">
          <div className="breadcrumb">
            <button
              ref={menuButton}
              aria-expanded={mobileOpen}
              aria-controls="workspace-navigation"
              className="icon-button mobile-menu"
              aria-label={word(lang, 'Open navigation', 'メニューを開く')}
              onClick={() => setMobileOpen(true)}
            >
              <Menu size={20} />
            </button>
            <span className="breadcrumb-home">Workspace</span>
            <span className="breadcrumb-divider">/</span>
            <span>{word(lang, current.en, current.ja)}</span>
          </div>
          <div className="topbar-actions">
            <button className="command-search" onClick={() => setPalette(true)}>
              <Search size={14} />
              <span>{word(lang, 'Quick navigation', '画面を検索')}</span>
              <kbd>
                <Command size={11} /> K
              </kbd>
            </button>
            <div className="mode-control">
              <label className="sr-only" htmlFor="adapter-mode">
                {word(lang, 'Data source', 'データソース')}
              </label>
              <select
                id="adapter-mode"
                value={mode}
                disabled={changeLocked}
                onChange={(event) => setMode(event.target.value as AdapterMode)}
              >
                <option value="demo">Demo</option>
                <option value="local">Local API</option>
              </select>
            </div>
            <button
              className="language-button"
              onClick={() =>
                setPreferences({ ...preferences, language: lang === 'en' ? 'ja' : 'en' })
              }
            >
              {lang === 'en' ? '日本語' : 'EN'}
            </button>
            <button
              className="icon-button notifications-button"
              onClick={() => setNotices(true)}
              aria-label={word(lang, 'System notices', 'システム通知')}
            >
              <Bell size={18} />
              <span />
            </button>
            <span className="topbar-avatar">Y</span>
          </div>
        </header>
        <main id="main-content" className="main-content" ref={heading} tabIndex={-1}>
          <div className={`environment-strip ${demo ? 'demo-strip' : ''}`}>
            <div>
              <span className="environment-symbol">
                {demo ? <LayersIcon /> : <ShieldCheck size={13} />}
              </span>
              <strong>
                {demo
                  ? 'DEMO WORKSPACE'
                  : !ark.connected
                    ? 'LOCAL API · DISCONNECTED'
                    : ark.status?.model?.local_model
                      ? 'LOCAL MODEL'
                      : ark.status?.model
                        ? 'MOCK · NO MODEL'
                        : 'LOCAL API · LOADING'}
              </strong>
              <span>
                {demo
                  ? word(
                      lang,
                      'Sample data · no real actions, metrics or model inference',
                      'サンプルデータ · 実操作・実測値・モデル推論なし',
                    )
                  : word(
                      lang,
                      'Conversation only · all other services unavailable',
                      '会話のみ接続 · その他のサービスは利用不可',
                    )}
              </span>
            </div>
            <span className="environment-phase">
              <span className="status-dot" />
              {phase}
            </span>
          </div>
          {(ark.error || ark.status?.error || ark.status?.warning) && (
            <div className="connection-notice">
              <Notice tone="error">
                {ark.error || ark.status?.error || ark.status?.warning}{' '}
                {ark.uncertain &&
                  word(
                    lang,
                    'Check the conversation before retrying.',
                    '再操作の前に会話を確認してください。',
                  )}
              </Notice>
              <Button onClick={() => void ark.refresh()}>
                <RefreshCw size={14} />
                {word(lang, 'Refresh status', '状態を再取得')}
              </Button>
            </div>
          )}
          {ark.loading && (
            <div className="loading-state" role="status">
              <span className="pulse-dot" />
              {word(
                lang,
                'Connecting to the selected adapter…',
                '選択したAdapterに接続しています…',
              )}
            </div>
          )}
          {screen === 'dashboard' && (
            <Dashboard ark={ark} demo={demo} lang={lang} navigate={navigate} />
          )}
          {screen === 'conversation' && (
            <>
              <div className="page-intro compact-intro">
                <div>
                  <div className="eyebrow">THINK TOGETHER</div>
                  <h1>
                    {word(lang, 'Conversation', '会話')}
                    <span className="heading-period">.</span>
                  </h1>
                  <p>
                    {word(
                      lang,
                      'An open channel for your next idea.',
                      '次のアイデアへつながる対話を。',
                    )}
                  </p>
                </div>
                <Badge tone="cyan">{word(lang, 'One shared session', '単一共有セッション')}</Badge>
              </div>
              <Conversation key={mode} ark={ark} demo={demo} lang={lang} />
            </>
          )}
          {['memory', 'agents', 'tools', 'vision'].includes(screen) && (
            <div className="page-intro compact-intro">
              <div>
                <div className="eyebrow">ARK WORKSPACE</div>
                <h1>
                  {word(lang, current.en, current.ja)}
                  <span className="heading-period">.</span>
                </h1>
                <p>
                  {word(
                    lang,
                    'Understand the details. Stay in control.',
                    '詳細を把握し、主導権を保つ。',
                  )}
                </p>
              </div>
              <Badge tone={demo ? 'amber' : 'neutral'}>
                {demo ? 'Demo' : word(lang, 'Unavailable', '利用不可')}
              </Badge>
            </div>
          )}
          {screen === 'memory' && <Memory key={mode} demo={demo} lang={lang} />}
          {screen === 'agents' && <Agents key={mode} demo={demo} lang={lang} />}
          {screen === 'tools' && <Tools key={mode} demo={demo} lang={lang} />}
          {screen === 'vision' && <Vision key={mode} demo={demo} lang={lang} />}
          {screen === 'settings' && (
            <Settings preferences={preferences} onChange={setPreferences} status={ark.status} />
          )}
          <footer className="app-footer">
            <span>
              ARK AI <span className="footer-dot">·</span>{' '}
              {word(lang, 'Built for your world.', 'あなたの世界のために。')}
            </span>
            <span>
              <ShieldCheck size={12} />
              {word(lang, 'Local-first. Human in control.', 'ローカル優先。主導権はあなたに。')}
            </span>
          </footer>
        </main>
      </div>
      {palette && (
        <Modal
          title={word(lang, 'Go to workspace', '画面に移動')}
          onClose={() => setPalette(false)}
          closeLabel={word(lang, 'Close', '閉じる')}
        >
          <label className="search-field palette-search">
            <Search size={17} />
            <input
              autoFocus
              placeholder={word(lang, 'Search workspaces…', '画面を検索…')}
              aria-label={word(lang, 'Search workspaces', '画面を検索')}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>
          <div className="palette-list">
            {navigation
              .filter((item) => `${item.en} ${item.ja}`.toLowerCase().includes(query.toLowerCase()))
              .map((item) => (
                <button key={item.id} onClick={() => navigate(item.id)}>
                  <item.icon size={17} />
                  <span>{word(lang, item.en, item.ja)}</span>
                  <ArrowUpRight size={15} />
                </button>
              ))}
            {!navigation.some((item) =>
              `${item.en} ${item.ja}`.toLowerCase().includes(query.toLowerCase()),
            ) && (
              <p className="muted">
                {word(lang, 'No workspaces found.', '該当する画面がありません。')}
              </p>
            )}
          </div>
        </Modal>
      )}
      {notices && (
        <Modal
          title={word(lang, 'Workspace status', 'ワークスペースの状態')}
          onClose={() => setNotices(false)}
        >
          <Badge tone={demo ? 'amber' : 'cyan'}>{phase}</Badge>
          <p>
            {word(
              lang,
              'This UI foundation connects the existing V2 conversation contract. Memory, agent, tools and multimodal service integration is planned separately.',
              'このUI基盤は既存のV2会話契約に接続します。Memory・Agent・Tool・マルチモーダルのサービス統合は今後の作業です。',
            )}
          </p>
          <Notice>
            {word(
              lang,
              'No real tools, WRITE approvals, training, model promotion, camera or microphone access is enabled here.',
              '実Tool・WRITE承認・学習・モデル昇格・カメラ・マイク取得は無効です。',
            )}
          </Notice>
          <div className="modal-actions">
            <Button onClick={() => setNotices(false)}>{word(lang, 'Got it', '閉じる')}</Button>
          </div>
        </Modal>
      )}
    </div>
  );
}
function LayersIcon() {
  return <Activity size={13} />;
}
export default function App() {
  return (
    <ErrorBoundary>
      <Shell />
    </ErrorBoundary>
  );
}
