import { Check, Globe, Palette, Shield, SlidersHorizontal } from 'lucide-react';
import { Badge, Panel, word, type Language } from '../components/ui';
import type { LocalStatus } from '../data/contracts';

export interface Preferences {
  language: Language;
  theme: 'graphite' | 'navy';
  reducedMotion: boolean;
}
export function Settings({
  preferences,
  onChange,
  status,
}: {
  preferences: Preferences;
  onChange: (next: Preferences) => void;
  status: LocalStatus | null;
}) {
  const lang = preferences.language;
  return (
    <div className="screen-stack">
      <div className="page-intro">
        <div>
          <div className="eyebrow">MAKE IT YOURS</div>
          <h1>
            {word(lang, 'Settings', '設定')}
            <span className="heading-period">.</span>
          </h1>
          <p>
            {word(
              lang,
              'A workspace that feels like your own.',
              'あなたらしく、使いやすいワークスペースに。',
            )}
          </p>
        </div>
        <Badge tone="cyan">{word(lang, 'Browser preferences', 'ブラウザ設定')}</Badge>
      </div>
      <div className="settings-grid">
        <Panel title={word(lang, 'Appearance', '外観')} action={<Palette size={18} />}>
          <p className="muted">
            {word(
              lang,
              'Quiet colors. Clear hierarchy. Choose your atmosphere.',
              '落ち着いた色と、明確な情報の階層。好みの雰囲気を選べます。',
            )}
          </p>
          <div className="theme-options">
            {(['graphite', 'navy'] as const).map((theme) => (
              <button
                className={`theme-option ${preferences.theme === theme ? 'selected' : ''}`}
                aria-pressed={preferences.theme === theme}
                key={theme}
                onClick={() => onChange({ ...preferences, theme })}
              >
                <span className={`theme-swatch swatch-${theme}`}>
                  <span />
                  <span />
                  <span />
                </span>
                <span>
                  {theme === 'graphite' ? 'Graphite' : 'Deep Navy'}
                  {preferences.theme === theme && <Check size={15} />}
                </span>
              </button>
            ))}
          </div>
          <label className="setting-row">
            <span>
              <strong>{word(lang, 'Reduce motion', '動きを抑える')}</strong>
              <small>
                {word(
                  lang,
                  'Keep transitions and ambient motion still.',
                  'アニメーションと画面遷移の動きを抑えます。',
                )}
              </small>
            </span>
            <input
              type="checkbox"
              checked={preferences.reducedMotion}
              onChange={(event) =>
                onChange({ ...preferences, reducedMotion: event.target.checked })
              }
            />
          </label>
        </Panel>
        <Panel title={word(lang, 'Language & region', '言語')} action={<Globe size={18} />}>
          <label className="form-field">
            {word(lang, 'Interface language', '表示言語')}
            <select
              value={lang}
              onChange={(event) =>
                onChange({ ...preferences, language: event.target.value as Language })
              }
            >
              <option value="en">English</option>
              <option value="ja">日本語</option>
            </select>
          </label>
          <p className="muted small">
            {word(
              lang,
              'These settings apply to this browser. They do not modify the model’s response policy.',
              'このブラウザに適用されます。モデルの応答方針は変更しません。',
            )}
          </p>
        </Panel>
        <Panel
          title={word(lang, 'Model & context', 'モデルとContext')}
          action={<SlidersHorizontal size={18} />}
        >
          <Badge>
            {word(lang, 'Backend configuration · read only', 'Backend設定 · 読み取り専用')}
          </Badge>
          <dl className="detail-list">
            <div>
              <dt>{word(lang, 'Model', 'モデル')}</dt>
              <dd>{status?.model?.name || '—'}</dd>
            </div>
            <div>
              <dt>{word(lang, 'Runtime', 'ランタイム')}</dt>
              <dd>
                {status?.model?.local_model ? 'llama-cpp' : status?.model ? 'Mock / no model' : '—'}
              </dd>
            </div>
            <div>
              <dt>{word(lang, 'Context capacity', 'Context容量')}</dt>
              <dd>{status?.model?.context_capacity || '—'}</dd>
            </div>
            <div>
              <dt>{word(lang, 'Response policy', '応答方針')}</dt>
              <dd>V2 · concise</dd>
            </div>
          </dl>
          <p className="muted small">
            {word(
              lang,
              'Model, context and storage are configured in your existing TOML file. Restart the local runner after changing that file.',
              'モデル・Context・保存先は既存のTOMLで設定します。変更後にローカルランナーを再起動してください。',
            )}
          </p>
        </Panel>
        <Panel
          title={word(lang, 'Privacy & storage', 'プライバシーと保存')}
          action={<Shield size={18} />}
        >
          <dl className="detail-list">
            <div>
              <dt>{word(lang, 'Device capture', 'デバイス取得')}</dt>
              <dd>{word(lang, 'Disabled', '無効')}</dd>
            </div>
            <div>
              <dt>{word(lang, 'External tools', '外部Tool')}</dt>
              <dd>{word(lang, 'Disabled', '無効')}</dd>
            </div>
            <div>
              <dt>{word(lang, 'Analytics', 'アクセス解析')}</dt>
              <dd>{word(lang, 'None', 'なし')}</dd>
            </div>
            <div>
              <dt>{word(lang, 'Session logs', 'セッションログ')}</dt>
              <dd>{!status ? '—' : status.logging ? 'Local JSONL' : word(lang, 'Off', 'オフ')}</dd>
            </div>
            <div>
              <dt>{word(lang, 'Browser storage', 'ブラウザ保存')}</dt>
              <dd>{word(lang, 'Appearance & language only', '外観と言語のみ')}</dd>
            </div>
          </dl>
          <p className="muted small">
            {word(
              lang,
              'The frontend does not persist conversation text or API tokens. The backend may write chat logs according to your configuration. Reset does not erase those files.',
              'フロントエンドは会話本文とAPIトークンを永続保存しません。Backendは設定に従い会話ログを保存する場合があります。Resetでログは削除されません。',
            )}
          </p>
        </Panel>
      </div>
    </div>
  );
}
