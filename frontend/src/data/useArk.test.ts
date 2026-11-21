import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { LocalStatus } from './contracts';
import { useArk } from './useArk';

const initial = (changes: Partial<LocalStatus> = {}): LocalStatus => ({
  state: 'ready',
  revision: 1,
  intelligence: 'V2',
  model: { name: 'real-model.gguf', local_model: true, context_capacity: 4096 },
  token: 'server-process',
  messages: [],
  pending_message: null,
  error: null,
  warning: null,
  dropped_turns: 0,
  logging: true,
  ...changes,
});
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe('connection safety and state coordination', () => {
  it('blocks a stale-tab mutation until the changed revision has been reviewed', async () => {
    let state = initial();
    const fetcher = vi.fn<typeof fetch>().mockImplementation(async (_url, options) => {
      if (options?.method === 'POST') return json({ accepted: true }, 202);
      return json(state);
    });
    vi.stubGlobal('fetch', fetcher);
    const { result } = renderHook(() => useArk('local'));
    await waitFor(() => expect(result.current.connected).toBe(true));
    state = initial({
      revision: 3,
      messages: [
        { role: 'user', content: 'other tab' },
        { role: 'assistant', content: 'response' },
      ],
    });
    let accepted: boolean | undefined;
    await act(async () => {
      accepted = await result.current.reset();
    });
    expect(accepted).toBe(false);
    expect(fetcher.mock.calls.filter(([, options]) => options?.method === 'POST')).toHaveLength(0);
    expect(result.current.status?.revision).toBe(3);
    expect(result.current.error).toContain('conversation changed');
  });
  it('rejects a changed server token before sending', async () => {
    let state = initial();
    const fetcher = vi.fn<typeof fetch>().mockImplementation(async () => json(state));
    vi.stubGlobal('fetch', fetcher);
    const { result } = renderHook(() => useArk('local'));
    await waitFor(() => expect(result.current.connected).toBe(true));
    state = initial({ token: 'restarted-server' });
    await act(async () => {
      expect(await result.current.send('hello')).toBe(false);
    });
    expect(fetcher.mock.calls.filter(([, options]) => options?.method === 'POST')).toHaveLength(0);
  });
  it('blocks rapid duplicate sends synchronously and keeps local stop unavailable', async () => {
    let state = initial();
    let finish: (() => void) | undefined;
    const fetcher = vi.fn<typeof fetch>().mockImplementation(async (_url, options) => {
      if (options?.method === 'POST') {
        await new Promise<void>((resolve) => {
          finish = resolve;
        });
        state = initial({ revision: 2, state: 'generating', pending_message: 'hello' });
        return json({ accepted: true }, 202);
      }
      return json(state);
    });
    vi.stubGlobal('fetch', fetcher);
    const { result } = renderHook(() => useArk('local'));
    await waitFor(() => expect(result.current.connected).toBe(true));
    let first: Promise<boolean>;
    act(() => {
      first = result.current.send('hello');
    });
    await waitFor(() => expect(finish).toBeTypeOf('function'));
    await act(async () => {
      expect(await result.current.send('duplicate')).toBe(false);
      expect(await result.current.reset()).toBe(false);
      finish?.();
      expect(await first).toBe(true);
    });
    expect(fetcher.mock.calls.filter(([, options]) => options?.method === 'POST')).toHaveLength(1);
    expect(result.current.canStop).toBe(false);
    expect(await result.current.stop()).toBe(false);
  });
  it('does not send when status polling failed and never replaces local state with demo', async () => {
    const fetcher = vi.fn<typeof fetch>().mockRejectedValue(new TypeError('offline'));
    vi.stubGlobal('fetch', fetcher);
    const { result } = renderHook(() => useArk('local'));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.status).toBeNull();
    await act(async () => {
      expect(await result.current.send('hello')).toBe(false);
    });
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
  it('reports ambiguous acceptance without an automatic write retry', async () => {
    const fetcher = vi.fn<typeof fetch>().mockImplementation(async (_url, options) => {
      if (options?.method === 'POST') throw new DOMException('Timed out', 'AbortError');
      return json(initial());
    });
    vi.stubGlobal('fetch', fetcher);
    const { result } = renderHook(() => useArk('local'));
    await waitFor(() => expect(result.current.connected).toBe(true));
    await act(async () => {
      expect(await result.current.send('hello')).toBe(false);
    });
    expect(result.current.uncertain).toBe(true);
    expect(result.current.error).toContain('Acceptance is unknown');
    expect(fetcher.mock.calls.filter(([, options]) => options?.method === 'POST')).toHaveLength(1);
  });
  it('restores draft after generation error, but not a committed turn with log warning', async () => {
    let state = initial();
    const fetcher = vi.fn<typeof fetch>().mockImplementation(async (_url, options) => {
      if (options?.method === 'POST') {
        state = initial({
          state: 'generating',
          revision: state.revision + 1,
          pending_message: 'hello',
        });
        return json({ accepted: true }, 202);
      }
      return json(state);
    });
    vi.stubGlobal('fetch', fetcher);
    const { result } = renderHook(() => useArk('local'));
    await waitFor(() => expect(result.current.connected).toBe(true));
    await act(async () => {
      await result.current.send('hello');
    });
    state = initial({ revision: 3, error: 'Generation failed' });
    await act(async () => {
      await result.current.refresh();
    });
    expect(result.current.recoveredDraft).toBe('hello');
    const fullHistory: LocalStatus['messages'] = Array.from({ length: 200 }, (_, index) => ({
      role: index % 2 ? 'assistant' : 'user',
      content: 'old',
    }));
    state = initial({ revision: 3, messages: fullHistory });
    await act(async () => {
      await result.current.refresh();
    });
    await act(async () => {
      result.current.clearRecoveredDraft();
      await result.current.send('hello');
    });
    state = initial({
      revision: 5,
      state: 'error',
      warning: 'Log save failed',
      messages: [
        ...fullHistory.slice(2),
        { role: 'user', content: 'hello' },
        { role: 'assistant', content: 'completed' },
      ],
    });
    await act(async () => {
      await result.current.refresh();
    });
    expect(result.current.recoveredDraft).toBeNull();
  });
  it('does not apply an old reset result after switching adapter mode', async () => {
    let finish: (() => void) | undefined;
    const fetcher = vi.fn<typeof fetch>().mockImplementation(async (_url, options) => {
      if (options?.method === 'POST') {
        await new Promise<void>((resolve) => {
          finish = resolve;
        });
        return json({ reset: true });
      }
      return json(initial());
    });
    vi.stubGlobal('fetch', fetcher);
    const { result, rerender } = renderHook(
      ({ mode }: { mode: 'local' | 'demo' }) => useArk(mode),
      { initialProps: { mode: 'local' } },
    );
    await waitFor(() => expect(result.current.connected).toBe(true));
    let resetting: Promise<boolean>;
    act(() => {
      resetting = result.current.reset();
    });
    await waitFor(() => expect(finish).toBeTypeOf('function'));
    rerender({ mode: 'demo' });
    await waitFor(() => expect(result.current.status?.model?.local_model).toBe(false));
    await act(async () => {
      finish?.();
      expect(await resetting).toBe(false);
    });
    expect(result.current.status?.model?.name).toContain('demonstration');
    expect(result.current.pending).toBe(false);
    expect(result.current.error).toBeNull();
  });
  it('rejects a regressed snapshot and disables writes', async () => {
    let state = initial({ revision: 3 });
    vi.stubGlobal(
      'fetch',
      vi.fn<typeof fetch>().mockImplementation(async () => json(state)),
    );
    const { result } = renderHook(() => useArk('local'));
    await waitFor(() => expect(result.current.connected).toBe(true));
    state = initial({ revision: 2 });
    await act(async () => {
      await result.current.refresh();
    });
    expect(result.current.connected).toBe(false);
    expect(result.current.status?.revision).toBe(3);
    expect(result.current.error).toContain('stale status');
  });
});
