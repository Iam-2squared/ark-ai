import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { Memory } from './Memory';
import { Agents } from './Agents';
import { Tools } from './Tools';
import { Vision } from './Vision';

beforeAll(() => {
  // jsdom has no top-layer dialog implementation. Browser QA covers focus trapping.
  HTMLDialogElement.prototype.showModal = function () {
    this.setAttribute('open', '');
  };
  HTMLDialogElement.prototype.close = function () {
    this.removeAttribute('open');
  };
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('memory review boundary', () => {
  it('searches sample content and narrows it by namespace', () => {
    render(<Memory demo lang="en" />);
    fireEvent.change(screen.getByRole('textbox', { name: 'Search memories' }), {
      target: { value: 'architecture' },
    });
    expect(screen.getByRole('button', { name: /ARK AI · Design principles/ })).toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: /Communication preferences/ }),
    ).not.toBeInTheDocument();
    fireEvent.change(screen.getByRole('combobox', { name: 'Namespace' }), {
      target: { value: 'preferences' },
    });
    expect(screen.getByText('No matching memories')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Review sample edit' })).not.toBeInTheDocument();
  });

  it('requires review before editing a sample and records provenance without network writes', () => {
    const fetch = vi.fn();
    vi.stubGlobal('fetch', fetch);
    render(<Memory demo lang="en" />);
    fireEvent.click(screen.getByRole('button', { name: 'Review sample edit' }));
    const dialog = screen.getByRole('dialog');
    expect(within(dialog).getByText('Demo · No backend action')).toBeInTheDocument();
    fireEvent.change(within(dialog).getByRole('textbox', { name: 'Sample content' }), {
      target: { value: 'A reviewed sample change.' },
    });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Apply sample edit' }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(
      screen.getByText('A reviewed sample change.', { selector: '.ws-memory-content' }),
    ).toBeInTheDocument();
    expect(screen.getByText('Demo edit reviewed in this view')).toBeInTheDocument();
    expect(screen.getByText(/No backend memory was updated/)).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
  });

  it('does not remove a sample until the deletion review is confirmed', () => {
    render(<Memory demo lang="en" />);
    fireEvent.click(screen.getByRole('button', { name: 'Delete sample' }));
    fireEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Cancel' }));
    expect(screen.getByRole('button', { name: /ARK AI · Design principles/ })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Delete sample' }));
    fireEvent.click(
      within(screen.getByRole('dialog')).getByRole('button', { name: 'Delete sample only' }),
    );
    expect(
      screen.queryByRole('button', { name: /ARK AI · Design principles/ }),
    ).not.toBeInTheDocument();
    expect(screen.getByText(/No stored memory was deleted/)).toBeInTheDocument();
  });
});

describe('unavailable capabilities', () => {
  it('never presents memory, agent or registry fixtures as connected backend data', () => {
    const { rerender } = render(<Memory demo={false} lang="en" />);
    expect(screen.getByText('Unavailable')).toBeInTheDocument();
    expect(screen.queryByText('ARK AI · Design principles')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Review sample edit' })).not.toBeInTheDocument();
    rerender(<Agents demo={false} lang="en" />);
    expect(screen.getByText('No agent runtime connected')).toBeInTheDocument();
    expect(screen.queryByText('demo-task-001')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Review retry' })).not.toBeInTheDocument();
    rerender(<Tools demo={false} lang="en" />);
    expect(screen.getByText('Registry not connected')).toBeInTheDocument();
    expect(screen.queryByText('files.search')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Preview approval' })).not.toBeInTheDocument();
  });

  it.each([true, false])('leaves every device input disabled (demo=%s)', (demo) => {
    const fetch = vi.fn();
    vi.stubGlobal('fetch', fetch);
    render(<Vision demo={demo} lang="en" />);
    expect(screen.getByText('No capture')).toBeInTheDocument();
    for (const name of ['Start microphone', 'Test voice', 'Camera', 'Screen']) {
      const control = screen.getByRole('button', { name });
      expect(control).toBeDisabled();
      fireEvent.click(control);
    }
    expect(fetch).not.toHaveBeenCalled();
    if (!demo) expect(screen.queryByText('Screen summary example')).not.toBeInTheDocument();
  });
});

describe('execution previews', () => {
  it('records a tool review preview without granting permissions or executing', () => {
    const fetch = vi.fn();
    vi.stubGlobal('fetch', fetch);
    render(<Tools demo lang="en" />);
    fireEvent.click(screen.getByRole('button', { name: 'WRITE' }));
    expect(screen.queryByRole('button', { name: /File search/ })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Write document/ }));
    fireEvent.click(screen.getByRole('button', { name: 'Preview approval' }));
    const dialog = screen.getByRole('dialog');
    expect(within(dialog).getByText('None · Preview only')).toBeInTheDocument();
    fireEvent.click(within(dialog).getByRole('button', { name: 'Confirm preview' }));
    expect(
      screen.getByText(/No permission was granted and no action was executed/),
    ).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
  });

  it('inspects failed steps and records retry intent without changing the task state', () => {
    const fetch = vi.fn();
    vi.stubGlobal('fetch', fetch);
    render(<Agents demo lang="en" />);
    expect(screen.getByRole('button', { name: 'Review retry' })).toBeDisabled();
    fireEvent.click(screen.getByRole('button', { name: /Build a knowledge index/ }));
    expect(
      screen.getByText(/Sample failure: the source document is unavailable/),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Review retry' }));
    fireEvent.click(
      within(screen.getByRole('dialog')).getByRole('button', { name: 'Record preview only' }),
    );
    expect(screen.getByText(/No task state or agent process changed/)).toBeInTheDocument();
    expect(screen.getByText('Demo · Failed')).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
  });

  it('shows Japanese search and review controls', () => {
    render(<Memory demo lang="ja" />);
    fireEvent.change(screen.getByRole('textbox', { name: '記憶を検索' }), {
      target: { value: 'コミュニケーション' },
    });
    expect(screen.getByRole('button', { name: /コミュニケーションの好み/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'サンプル編集を確認' })).toBeInTheDocument();
  });
});
