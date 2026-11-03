import { beforeAll, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import type { ArkConnection } from '../data/useArk';
import type { LocalStatus } from '../data/contracts';
import { Conversation } from './Conversation';

beforeAll(() => {
  // jsdom does not implement top-layer dialogs; native focus/IME needs browser QA.
  HTMLDialogElement.prototype.showModal = function () {
    this.setAttribute('open', '');
  };
  HTMLDialogElement.prototype.close = function () {
    this.removeAttribute('open');
  };
});

function status(changes: Partial<LocalStatus> = {}): LocalStatus {
  return {
    state: 'ready',
    revision: 1,
    intelligence: 'V2',
    model: {
      name: 'test-local.gguf',
      local_model: true,
      context_capacity: 4096,
      quantization: 'Q4_K_M',
    },
    messages: [],
    pending_message: null,
    error: null,
    warning: null,
    dropped_turns: 0,
    logging: true,
    token: 'test-token',
    ...changes,
  };
}
function connection(changes: Partial<ArkConnection> = {}): ArkConnection {
  return {
    status: status(),
    connected: true,
    loading: false,
    error: null,
    pending: false,
    uncertain: false,
    recoveredDraft: null,
    clearRecoveredDraft: vi.fn(),
    refresh: vi.fn(async () => {}),
    send: vi.fn(async () => true),
    reset: vi.fn(async () => true),
    stop: vi.fn(async () => true),
    canStop: false,
    ...changes,
  };
}

describe('conversation input and recovery', () => {
  it('sends one accepted Enter turn and clears only the submitted draft', async () => {
    const ark = connection();
    render(<Conversation ark={ark} demo={false} lang="en" />);
    const input = screen.getByRole('textbox', { name: 'Message ARK' });
    fireEvent.change(input, { target: { value: 'Hello ARK' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter', keyCode: 13 });
    expect(ark.send).toHaveBeenCalledExactlyOnceWith('Hello ARK');
    await waitFor(() => expect(input).toHaveValue(''));
  });

  it('does not send Shift+Enter or IME confirmation including Windows keyCode 229', async () => {
    const ark = connection();
    render(<Conversation ark={ark} demo={false} lang="ja" />);
    const input = screen.getByRole('textbox', { name: 'ARKへのメッセージ' });
    fireEvent.change(input, { target: { value: '日本語を変換中' } });
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: true });
    fireEvent.keyDown(input, { key: 'Enter', isComposing: true });
    fireEvent.compositionStart(input);
    fireEvent.keyDown(input, { key: 'Enter', keyCode: 13 });
    fireEvent.click(screen.getByRole('button', { name: 'メッセージを送信' }));
    fireEvent.compositionEnd(input);
    fireEvent.keyDown(input, { key: 'Enter', keyCode: 229 });
    expect(ark.send).not.toHaveBeenCalled();
    expect(input).toHaveValue('日本語を変換中');
    fireEvent.keyDown(input, { key: 'Enter', keyCode: 13 });
    expect(ark.send).toHaveBeenCalledExactlyOnceWith('日本語を変換中');
    await waitFor(() => expect(input).toHaveValue(''));
  });

  it('preserves a rejected draft and never replays it automatically', async () => {
    const ark = connection({ send: vi.fn(async () => false) });
    render(<Conversation ark={ark} demo={false} lang="en" />);
    const input = screen.getByRole('textbox', { name: 'Message ARK' });
    fireEvent.change(input, { target: { value: 'Keep this draft' } });
    fireEvent.click(screen.getByRole('button', { name: 'Send message' }));
    await waitFor(() => expect(ark.send).toHaveBeenCalledTimes(1));
    expect(input).toHaveValue('Keep this draft');
  });

  it('requires an explicit click to restore a generation-failure draft', () => {
    const ark = connection({ recoveredDraft: 'A turn that failed generation' });
    render(<Conversation ark={ark} demo={false} lang="en" />);
    const input = screen.getByRole('textbox', { name: 'Message ARK' });
    expect(input).toHaveValue('');
    expect(ark.send).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Restore draft' }));
    expect(input).toHaveValue('A turn that failed generation');
    expect(ark.clearRecoveredDraft).toHaveBeenCalledOnce();
    expect(ark.send).not.toHaveBeenCalled();
  });

  it.each([
    { connected: false },
    { pending: true },
    { status: status({ state: 'loading', model: null }) },
    { status: status({ state: 'error', error: 'Runtime unavailable' }) },
  ])('disables input and reset when not ready: %j', (changes) => {
    const ark = connection(changes);
    render(<Conversation ark={ark} demo={false} lang="en" />);
    expect(screen.getByRole('textbox', { name: 'Message ARK' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Send message' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Reset' })).toBeDisabled();
    expect(ark.send).not.toHaveBeenCalled();
    expect(ark.reset).not.toHaveBeenCalled();
  });
});

describe('conversation destructive and unavailable controls', () => {
  it('calls Reset only after reviewing the shared-session dialog', async () => {
    const ark = connection();
    render(<Conversation ark={ark} demo={false} lang="en" />);
    fireEvent.click(screen.getByRole('button', { name: 'Reset' }));
    let dialog = screen.getByRole('dialog', { name: 'Reset this conversation?' });
    expect(within(dialog).getByText(/All tabs share this conversation/)).toBeInTheDocument();
    expect(ark.reset).not.toHaveBeenCalled();
    fireEvent.click(within(dialog).getByRole('button', { name: 'Keep conversation' }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(ark.reset).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Reset' }));
    dialog = screen.getByRole('dialog');
    fireEvent.click(within(dialog).getByRole('button', { name: 'Reset conversation' }));
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    expect(ark.reset).toHaveBeenCalledOnce();
  });

  it('keeps the reset dialog open if the adapter refuses the action', async () => {
    const ark = connection({ reset: vi.fn(async () => false) });
    render(<Conversation ark={ark} demo={false} lang="en" />);
    fireEvent.click(screen.getByRole('button', { name: 'Reset' }));
    fireEvent.click(
      within(screen.getByRole('dialog')).getByRole('button', { name: 'Reset conversation' }),
    );
    await waitFor(() => expect(ark.reset).toHaveBeenCalledOnce());
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  it('does not offer cancellation for the frozen local API', () => {
    const ark = connection({ status: status({ state: 'generating', pending_message: 'Pending' }) });
    render(<Conversation ark={ark} demo={false} lang="en" />);
    const stop = screen.getByRole('button', { name: 'Stop response' });
    expect(stop).toBeDisabled();
    expect(stop).toHaveAttribute('title', 'Stop unavailable in the current API');
    fireEvent.click(stop);
    expect(ark.stop).not.toHaveBeenCalled();
    expect(screen.getByRole('button', { name: 'Attachments unavailable' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Microphone unavailable' })).toBeDisabled();
  });

  it('allows only the explicit demonstration adapter to stop its response', () => {
    const ark = connection({
      status: status({ state: 'generating', pending_message: 'Pending' }),
      canStop: true,
    });
    render(<Conversation ark={ark} demo lang="en" />);
    const stop = screen.getByRole('button', { name: 'Stop response' });
    expect(stop).toBeEnabled();
    expect(stop).toHaveAttribute('title', 'Stop demo response');
    fireEvent.click(stop);
    expect(ark.stop).toHaveBeenCalledOnce();
  });
});

describe('source honesty and safe response rendering', () => {
  it('labels the Python --mock backend as MOCK, with no local inference claim', () => {
    const ark = connection({
      status: status({
        model: { name: 'Echo — deterministic mock', local_model: false, context_capacity: 4096 },
        logging: false,
        messages: [{ role: 'assistant', content: 'Echo response' }],
      }),
    });
    render(<Conversation ark={ark} demo={false} lang="en" />);
    expect(screen.getAllByText('MOCK · NO MODEL')).toHaveLength(2);
    expect(screen.getByText('Mock · no model')).toBeInTheDocument();
    expect(screen.getByText('Echo — deterministic mock')).toBeInTheDocument();
    expect(screen.queryByText('Local model')).not.toBeInTheDocument();
    expect(screen.queryByText('DEMO')).not.toBeInTheDocument();
  });

  it('renders Markdown and code while treating HTML, scripts, and URLs as inert text', () => {
    const text =
      '**Safe emphasis** and `inline_code`\n\n<script>alert("x")</script><img src=x onerror=alert(1)>\n\n[unsafe](javascript:alert(1))\n\n```html\n<div onclick="alert(1)">literal code</div>\n```';
    const ark = connection({
      status: status({ messages: [{ role: 'assistant', content: text }] }),
    });
    const { container } = render(<Conversation ark={ark} demo={false} lang="en" />);
    const markdown = container.querySelector('.markdown');
    expect(markdown?.querySelector('strong')).toHaveTextContent('Safe emphasis');
    expect(markdown?.querySelector('p code')).toHaveTextContent('inline_code');
    expect(markdown?.querySelector('pre code')).toHaveTextContent(
      '<div onclick="alert(1)">literal code</div>',
    );
    expect(markdown?.textContent).toContain('<script>alert("x")</script>');
    expect(markdown?.textContent).toContain('[unsafe](javascript:alert(1))');
    expect(markdown?.querySelector('script, img, a, [onclick], [onerror]')).toBeNull();
  });
});
