import { Camera, Eye, LockKeyhole, Mic, Monitor, Volume2 } from 'lucide-react';
import {
  Badge,
  Button,
  DemoNotice,
  EmptyState,
  Notice,
  Panel,
  word,
  type Language,
} from '../components/ui';
import './workspaces.css';

export function Vision({ demo, lang }: { demo: boolean; lang: Language }) {
  return (
    <div className="screen-stack">
      {demo ? (
        <DemoNotice lang={lang} />
      ) : (
        <Notice>
          {word(
            lang,
            'Multimodal capture is unavailable. This screen does not request camera, microphone or screen permissions.',
            'マルチモーダル入力は利用できません。この画面はカメラ・マイク・画面共有の権限を要求しません。',
          )}
        </Notice>
      )}
      <div className="ws-privacy-banner">
        <span className="ws-record-icon">
          <LockKeyhole size={21} />
        </span>
        <div>
          <div className="eyebrow">PRIVACY INDICATOR</div>
          <h2>{word(lang, 'No capture', 'キャプチャなし')}</h2>
          <p className="muted">
            {word(
              lang,
              'Camera, microphone and screen sources are disconnected.',
              'カメラ・マイク・画面ソースは未接続です。',
            )}
          </p>
        </div>
        <Badge tone="green">{word(lang, 'Inactive', '非アクティブ')}</Badge>
      </div>
      <div className="three-columns ws-source-grid">
        <Panel
          title={word(lang, 'Voice input', '音声入力')}
          eyebrow="SPEECH TO TEXT"
          action={<Mic size={18} />}
        >
          <div className="ws-device-symbol">
            <Mic size={30} />
          </div>
          <Badge>{word(lang, 'Unavailable', '利用不可')}</Badge>
          <p className="muted ws-intro">
            {word(
              lang,
              'A local speech adapter and explicit consent are required.',
              'ローカル音声Adapterと明示的な同意が必要です。',
            )}
          </p>
          <Button disabled>
            <Mic size={15} />
            {word(lang, 'Start microphone', 'マイクを開始')}
          </Button>
        </Panel>
        <Panel
          title={word(lang, 'Voice output', '音声出力')}
          eyebrow="TEXT TO SPEECH"
          action={<Volume2 size={18} />}
        >
          <div className="ws-device-symbol">
            <Volume2 size={30} />
          </div>
          <Badge>{word(lang, 'Unavailable', '利用不可')}</Badge>
          <p className="muted ws-intro">
            {word(
              lang,
              'Speech playback and interruption are not connected.',
              '音声再生と割り込み機能は未接続です。',
            )}
          </p>
          <Button disabled>
            <Volume2 size={15} />
            {word(lang, 'Test voice', '音声をテスト')}
          </Button>
        </Panel>
        <Panel
          title={word(lang, 'Visual sources', '映像ソース')}
          eyebrow="VISION"
          action={<Eye size={18} />}
        >
          <div className="ws-device-symbol">
            <Monitor size={30} />
          </div>
          <Badge>{word(lang, 'Unavailable', '利用不可')}</Badge>
          <p className="muted ws-intro">
            {word(
              lang,
              'No background observation or device access.',
              'バックグラウンドの観測・デバイス接続は行いません。',
            )}
          </p>
          <div className="ws-device-actions">
            <Button disabled>
              <Camera size={15} />
              {word(lang, 'Camera', 'カメラ')}
            </Button>
            <Button disabled>
              <Monitor size={15} />
              {word(lang, 'Screen', '画面')}
            </Button>
          </div>
        </Panel>
      </div>
      <Panel
        title={word(lang, 'Observation history', '観測履歴')}
        eyebrow={demo ? 'DEMO OBSERVATIONS' : 'OBSERVATIONS'}
        action={<Badge>{demo ? 'Demo' : word(lang, 'Unavailable', '利用不可')}</Badge>}
      >
        {demo ? (
          <div className="ws-observations">
            <article className="list-row ws-observation">
              <span className="ws-record-icon">
                <Monitor size={19} />
              </span>
              <div className="ws-record-copy">
                <strong>{word(lang, 'Screen summary example', '画面要約のサンプル')}</strong>
                <p className="muted">
                  {word(
                    lang,
                    'A code editor and project notes. Example text supplied by the UI fixture.',
                    'コードエディタとプロジェクトメモ。UIサンプルとして用意された説明文です。',
                  )}
                </p>
                <span className="mono muted">fixture://vision/screen-summary</span>
              </div>
              <Badge>Demo</Badge>
            </article>
            <article className="list-row ws-observation">
              <span className="ws-record-icon">
                <Mic size={19} />
              </span>
              <div className="ws-record-copy">
                <strong>
                  {word(lang, 'Voice transcript example', '音声文字起こしのサンプル')}
                </strong>
                <p className="muted">
                  {word(
                    lang,
                    '“Show my project overview.” No audio was recorded or processed.',
                    '「プロジェクトの概要を見せて」。音声の録音・処理は行っていません。',
                  )}
                </p>
                <span className="mono muted">fixture://voice/transcript</span>
              </div>
              <Badge>Demo</Badge>
            </article>
            <p className="demo-note">
              {word(
                lang,
                'These are static examples, not observations of this device.',
                'このデバイスを観測した内容ではなく、静的なサンプルです。',
              )}
            </p>
          </div>
        ) : (
          <EmptyState
            title={word(lang, 'No observation source connected', '観測ソースは未接続です')}
            icon={<Eye size={24} />}
          >
            {word(
              lang,
              'Future adapters must expose source, retention and consent state before any capture begins.',
              '将来のAdapterでは、キャプチャ開始前にソース・保存方針・同意状態を明示します。',
            )}
          </EmptyState>
        )}
      </Panel>
    </div>
  );
}
