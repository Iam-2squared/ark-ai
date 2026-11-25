import { useEffect, useRef, useState, type FormEvent } from 'react';
import {
  ArrowUp,
  Square,
  RotateCcw,
  Paperclip,
  Mic,
  ArrowRight,
  MessageSquare,
  Copy,
  Check,
} from 'lucide-react';
import type { ArkConnection } from '../data/useArk';
import { Badge, Button, Modal, Notice, word, type Language } from '../components/ui';
import { Markdown } from '../components/Markdown';

export function Conversation({
  ark,
  demo,
  lang,
}: {
  ark: ArkConnection;
  demo: boolean;
  lang: Language;
}) {
  const [draft, setDraft] = useState('');
  const [confirmReset, setConfirmReset] = useState(false);
  const [copied, setCopied] = useState<number | null>(null);
  const composing = useRef(false);
  const input = useRef<HTMLTextAreaElement>(null);
  const scrollArea = useRef<HTMLDivElement>(null);
  const follow = useRef(true);
  const { status } = ark;
  const mockBackend = !!status?.model && !status.model.local_model;
  const generating = status?.state === 'generating';
  const ready = ark.connected && status?.state === 'ready' && !ark.pending;
  useEffect(() => {
    const area = scrollArea.current;
    if (area && follow.current) area.scrollTop = area.scrollHeight;
  }, [status?.messages.length, status?.pending_message]);
  const submit = async (event?: FormEvent) => {
    event?.preventDefault();
    if (!ready || composing.current || !draft.trim()) return;
    const value = draft;
    if (await ark.send(value)) setDraft((current) => (current === value ? '' : current));
  };
  const copy = async (text: string, index: number) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(index);
    } catch {
      setCopied(null);
    }
  };
  return (
    <div className="conversation-layout">
      <section className="conversation-main panel">
        <div className="conversation-toolbar">
          <div>
            <span className="session-dot" />
            <strong>{word(lang, 'Current conversation', '現在の会話')}</strong>
            <Badge tone={demo ? 'amber' : 'cyan'}>{demo ? 'DEMO' : 'V2'}</Badge>
          </div>
          <Button variant="ghost" disabled={!ready} onClick={() => setConfirmReset(true)}>
            <RotateCcw size={14} />
            {word(lang, 'Reset', 'リセット')}
          </Button>
        </div>
        <div
          className="message-scroll"
          ref={scrollArea}
          onScroll={() => {
            const area = scrollArea.current;
            if (area) follow.current = area.scrollHeight - area.scrollTop - area.clientHeight < 100;
          }}
          tabIndex={0}
          aria-label={word(lang, 'Conversation history', '会話履歴')}
        >
          {!status?.messages.length && !status?.pending_message && (
            <div className="chat-welcome">
              <div className="welcome-mark">
                <img src="/ark.svg" alt="" />
              </div>
              <div className="eyebrow">ARK INTELLIGENCE</div>
              <h2>{word(lang, 'What’s on your mind?', '何から始めましょうか？')}</h2>
              <p>
                {word(
                  lang,
                  'A little clarity. A new idea. A place to start.',
                  '考えを整理する。アイデアを広げる。次の一歩を見つける。',
                )}
              </p>
              {demo && (
                <span className="demo-note">
                  {word(
                    lang,
                    'Demo conversation · deterministic response, no LLM',
                    'Demo会話 · 定型応答、LLM未接続',
                  )}
                </span>
              )}
              <div className="prompt-grid">
                {[
                  ['Help me plan my day', '今日の計画を整理して'],
                  ['Explain a piece of code', 'コードの理解を手伝って'],
                  ['Turn an idea into a plan', 'アイデアを計画にして'],
                ].map(([en, ja]) => (
                  <button
                    key={en}
                    disabled={!ready}
                    onClick={() => {
                      setDraft(word(lang, en, ja));
                      input.current?.focus();
                    }}
                  >
                    <MessageSquare size={15} />
                    <span>{word(lang, en, ja)}</span>
                    <ArrowRight size={15} />
                  </button>
                ))}
              </div>
            </div>
          )}
          {status?.messages.map((message, index) => (
            <article className={`chat-message ${message.role}`} key={`${index}-${message.role}`}>
              <div className="message-avatar">
                {message.role === 'assistant' ? <img src="/ark.svg" alt="" /> : 'Y'}
              </div>
              <div className="message-body">
                <div className="message-label">
                  {message.role === 'assistant' ? 'ARK' : word(lang, 'You', 'あなた')}
                  {message.role === 'assistant' && (
                    <span>
                      {demo
                        ? 'DEMO'
                        : mockBackend
                          ? 'MOCK · NO MODEL'
                          : status.model?.quantization || 'LOCAL'}
                    </span>
                  )}
                </div>
                <Markdown text={message.content} />
                <button
                  className="copy-button"
                  aria-label={word(lang, 'Copy message', 'メッセージをコピー')}
                  onClick={() => void copy(message.content, index)}
                >
                  {copied === index ? <Check size={13} /> : <Copy size={13} />}
                </button>
              </div>
            </article>
          ))}
          {status?.pending_message && (
            <>
              <article className="chat-message user">
                <div className="message-avatar">Y</div>
                <div className="message-body">
                  <div className="message-label">{word(lang, 'You', 'あなた')}</div>
                  <Markdown text={status.pending_message} />
                </div>
              </article>
              <div className="generation-indicator" role="status">
                <span className="pulse-dot" />
                {word(lang, 'ARK is preparing a response…', 'ARKが回答を生成しています…')}
              </div>
            </>
          )}
        </div>
        <div className="composer-wrap">
          {ark.recoveredDraft && (
            <Notice tone="warning">
              {word(
                lang,
                'An unsuccessful turn can be restored.',
                '失敗した送信内容を復元できます。',
              )}{' '}
              <button
                className="text-button"
                onClick={() => {
                  setDraft(ark.recoveredDraft || '');
                  ark.clearRecoveredDraft();
                }}
              >
                {word(lang, 'Restore draft', '下書きを復元')}
              </button>
            </Notice>
          )}
          <form className="composer" onSubmit={(event) => void submit(event)}>
            <label className="sr-only" htmlFor="chat-input">
              {word(lang, 'Message ARK', 'ARKへのメッセージ')}
            </label>
            <textarea
              id="chat-input"
              ref={input}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder={word(lang, 'Message ARK…', 'ARKにメッセージを送る…')}
              disabled={!ready}
              rows={2}
              maxLength={32000}
              onCompositionStart={() => {
                composing.current = true;
              }}
              onCompositionEnd={() => {
                composing.current = false;
              }}
              onKeyDown={(event) => {
                if (
                  event.key === 'Enter' &&
                  !event.shiftKey &&
                  !event.nativeEvent.isComposing &&
                  !composing.current &&
                  event.nativeEvent.keyCode !== 229
                ) {
                  event.preventDefault();
                  void submit();
                }
              }}
            />
            <div className="composer-actions">
              <div>
                <button
                  type="button"
                  className="icon-button"
                  disabled
                  aria-label={word(lang, 'Attachments unavailable', '添付は利用不可')}
                  title={word(lang, 'Image input is not connected', '画像入力は未接続です')}
                >
                  <Paperclip size={17} />
                </button>
                <button
                  type="button"
                  className="icon-button"
                  disabled
                  aria-label={word(lang, 'Microphone unavailable', 'マイクは利用不可')}
                >
                  <Mic size={17} />
                </button>
                <span className="composer-model">
                  {demo
                    ? 'DEMO · NO MODEL'
                    : mockBackend
                      ? 'MOCK · NO MODEL'
                      : status?.model?.quantization || 'LOCAL API'}
                </span>
              </div>
              <div>
                {generating ? (
                  <button
                    type="button"
                    className="send-button"
                    disabled={!ark.canStop}
                    title={
                      demo
                        ? 'Stop demo response'
                        : word(
                            lang,
                            'Stop unavailable in the current API',
                            '現在のAPIは停止に未対応',
                          )
                    }
                    aria-label={word(lang, 'Stop response', '応答を停止')}
                    onClick={() => void ark.stop()}
                  >
                    <Square size={15} />
                  </button>
                ) : (
                  <button
                    type="submit"
                    className="send-button"
                    disabled={!ready || !draft.trim() || [...draft].length > 16000}
                    aria-label={word(lang, 'Send message', 'メッセージを送信')}
                  >
                    <ArrowUp size={19} />
                  </button>
                )}
              </div>
            </div>
          </form>
          <div className="composer-note">
            <span>
              {word(
                lang,
                'Enter to send · Shift + Enter for a new line',
                'Enterで送信 · Shift + Enterで改行',
              )}
            </span>
            <span>
              {generating
                ? word(lang, 'Complete response pending', '回答完了を待っています')
                : word(
                    lang,
                    'Your words stay in this workspace',
                    '会話はこのワークスペースで扱います',
                  )}
            </span>
          </div>
          {[...draft].length > 16000 && (
            <Notice tone="warning">
              {word(lang, 'Use at most 16,000 characters.', '16,000文字以内にしてください。')}
            </Notice>
          )}
        </div>
      </section>
      <aside className="conversation-aside">
        <div className="eyebrow">SESSION CONTEXT</div>
        <h3>{word(lang, 'In this conversation', 'この会話について')}</h3>
        <dl className="detail-list">
          <div>
            <dt>{word(lang, 'Runtime', 'ランタイム')}</dt>
            <dd>
              {demo
                ? 'Demo adapter'
                : status?.model?.local_model
                  ? 'Local model'
                  : status?.model
                    ? 'Mock · no model'
                    : word(lang, 'Unavailable', '利用不可')}
            </dd>
          </div>
          <div>
            <dt>{word(lang, 'Model', 'モデル')}</dt>
            <dd>{status?.model?.name || '—'}</dd>
          </div>
          <div>
            <dt>{word(lang, 'Context capacity', 'Context容量')}</dt>
            <dd>
              {status?.model?.context_capacity.toLocaleString() || '—'}{' '}
              {status?.model ? 'tokens' : ''}
            </dd>
          </div>
          <div>
            <dt>{word(lang, 'Dropped turns', '削除済みの古い往復')}</dt>
            <dd>{status?.dropped_turns ?? '—'}</dd>
          </div>
          <div>
            <dt>{word(lang, 'Logging', 'ログ')}</dt>
            <dd>{!status ? '—' : status.logging ? 'Local JSONL' : word(lang, 'Off', 'オフ')}</dd>
          </div>
          <div>
            <dt>{word(lang, 'Transport', '通信方式')}</dt>
            <dd>{word(lang, 'Complete responses · polling', '回答完了後に取得 · ポーリング')}</dd>
          </div>
        </dl>
        <div className="context-note">
          <span className="tiny-mark">↗</span>
          <h4>{word(lang, 'Space to think', '考えるための余白')}</h4>
          <p>
            {word(
              lang,
              'Visible chat history and model context are separate. Older turns may leave the context budget.',
              '表示履歴とモデルのContextは別です。古い往復は予算に応じてContextから除外されます。',
            )}
          </p>
        </div>
        <p className="muted small">
          {word(
            lang,
            'Reset clears this shared session, not existing log files. Live streaming and cancellation need a future backend contract.',
            'Resetは共有セッションをクリアします。既存ログは削除しません。Streaming・停止は今後のBackend契約が必要です。',
          )}
        </p>
      </aside>
      {confirmReset && (
        <Modal
          title={word(lang, 'Reset this conversation?', '会話をリセットしますか？')}
          onClose={() => setConfirmReset(false)}
        >
          <p>
            {word(
              lang,
              'All tabs share this conversation. Display history and model context will be cleared; existing logs remain.',
              'すべてのタブで共有する会話です。表示履歴とモデルのContextをクリアします。既存ログは残ります。',
            )}
          </p>
          <div className="modal-actions">
            <Button onClick={() => setConfirmReset(false)}>
              {word(lang, 'Keep conversation', '会話を続ける')}
            </Button>
            <Button
              variant="danger"
              disabled={!ready}
              onClick={async () => {
                if (await ark.reset()) setConfirmReset(false);
              }}
            >
              {word(lang, 'Reset conversation', '会話をリセット')}
            </Button>
          </div>
        </Modal>
      )}
    </div>
  );
}
