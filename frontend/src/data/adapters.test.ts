import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError, parseLocalStatus, type LocalStatus } from './contracts';
import { createDemoAdapter } from './demo';
import { createLocalAdapter } from './local';

const snapshot = (changes: Partial<LocalStatus> = {}): LocalStatus => ({
  state: 'ready',
  revision: 1,
  intelligence: 'V2',
  model: { name: 'test.gguf', local_model: true, context_capacity: 4096 },
  token: 'process-token',
  messages: [],
  pending_message: null,
  error: null,
  warning: null,
  dropped_turns: 0,
  logging: true,
  ...changes,
});
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
afterEach(() => {
  vi.useRealTimers();
});

describe('frozen status contract validation', () => {
  it('accepts local metadata/loading without manufacturing telemetry', () => {
    expect(parseLocalStatus(snapshot()).model?.local_model).toBe(true);
    expect(parseLocalStatus(snapshot())).not.toHaveProperty('cpu');
    expect(parseLocalStatus(snapshot({ model: null, state: 'loading' })).model).toBeNull();
  });
  it.each([
    { token: '' },
    { token: 'invalid\ntoken' },
    { revision: -1 },
    { revision: 1.2 },
    { state: 'approved' },
    { logging: 'true' },
    { model: null },
    { messages: [{ role: 'system', content: 'hidden instructions' }] },
    { model: { name: 'not-model', local_model: 'true', context_capacity: 4096 } },
    { model: { name: 'model', local_model: true, context_capacity: 0 } },
    { dropped_turns: -3 },
    { intelligence: 'V3' },
  ])('rejects malformed data %j', (change) => {
    expect(() => parseLocalStatus({ ...snapshot(), ...change })).toThrow(ApiError);
  });
  it('drops uncontracted fields rather than displaying them as real', () => {
    expect(parseLocalStatus({ ...snapshot(), cpu: 42, approvals: ['approved'] })).toEqual(
      snapshot(),
    );
  });
});

describe('same-origin local adapter', () => {
  it('sends exact frozen requests, no history/generation controls, no stop capability', async () => {
    const fetcher = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(json(snapshot()))
      .mockResolvedValueOnce(json({ accepted: true }, 202))
      .mockResolvedValueOnce(json({ reset: true }));
    const adapter = createLocalAdapter(fetcher);
    await adapter.status();
    await adapter.chat('こんにちは', 1, 'process-token');
    await adapter.reset(3, 'process-token');
    expect(fetcher.mock.calls.map(([path]) => path)).toEqual([
      '/api/status',
      '/api/chat',
      '/api/reset',
    ]);
    expect(fetcher.mock.calls[0][1]).toMatchObject({
      method: 'GET',
      credentials: 'same-origin',
      cache: 'no-store',
      redirect: 'error',
    });
    expect(fetcher.mock.calls[1][1]).toMatchObject({
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-ARK-Token': 'process-token' },
      body: JSON.stringify({ message: 'こんにちは', revision: 1 }),
    });
    expect(fetcher.mock.calls[2][1]?.body).toBe(JSON.stringify({ revision: 3 }));
    expect(adapter.stop).toBeUndefined();
  });
  it('never retries failed writes or falls back to demo', async () => {
    const fetcher = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(json({ error: 'Stale revision' }, 409));
    const adapter = createLocalAdapter(fetcher);
    await expect(adapter.chat('hello', 1, 'token')).rejects.toMatchObject({ status: 409 });
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(adapter.mode).toBe('local');
    fetcher.mockRejectedValueOnce(new TypeError('Network failed'));
    await expect(adapter.reset(1, 'token')).rejects.toThrow('Network failed');
    expect(fetcher).toHaveBeenCalledTimes(2);
  });
  it('requires explicit acceptance and validates text length', async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(json({ state: 'ok' }));
    const adapter = createLocalAdapter(fetcher);
    await expect(adapter.chat('hello', 1, 'token')).rejects.toThrow('did not confirm acceptance');
    await expect(adapter.chat(' ', 1, 'token')).rejects.toThrow();
    await expect(adapter.chat('x'.repeat(16001), 1, 'token')).rejects.toThrow();
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
  it('aborts a timed-out write once and leaves acceptance unknown', async () => {
    vi.useFakeTimers();
    const fetcher = vi.fn<typeof fetch>().mockImplementation(async (_url, options) => {
      return new Promise<Response>((_resolve, reject) => {
        options?.signal?.addEventListener(
          'abort',
          () => reject(new DOMException('Timed out', 'AbortError')),
          { once: true },
        );
      });
    });
    const request = createLocalAdapter(fetcher).chat('hello', 1, 'token');
    const outcome = request.catch((cause: unknown) => cause);
    await vi.advanceTimersByTimeAsync(15_000);
    expect(await outcome).toMatchObject({ name: 'AbortError' });
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
  it('propagates read abortion', async () => {
    const fetcher = vi.fn<typeof fetch>().mockImplementation(async (_path, options) => {
      expect(options?.signal?.aborted).toBe(true);
      throw new DOMException('Aborted', 'AbortError');
    });
    await expect(createLocalAdapter(fetcher).status(AbortSignal.abort())).rejects.toMatchObject({
      name: 'AbortError',
    });
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
});

describe('explicit in-memory demo adapter', () => {
  it('labels no-model data and never fetches resources', async () => {
    const fetcher = vi.spyOn(globalThis, 'fetch');
    const demo = createDemoAdapter();
    const state = await demo.status();
    expect(state.model?.local_model).toBe(false);
    expect(state.model?.name).toContain('no model');
    expect(state.logging).toBe(false);
    expect(fetcher).not.toHaveBeenCalled();
    demo.dispose?.();
  });
  it('enforces pending/revision checks and reset without fake approvals', async () => {
    vi.useFakeTimers();
    const demo = createDemoAdapter(100);
    await demo.chat('hello', 1, 'ui-demo-only');
    expect((await demo.status()).state).toBe('generating');
    await expect(demo.chat('duplicate', 1, 'ui-demo-only')).rejects.toMatchObject({ status: 409 });
    await expect(demo.reset(2, 'ui-demo-only')).rejects.toMatchObject({ status: 409 });
    await vi.advanceTimersByTimeAsync(100);
    const complete = await demo.status();
    expect(complete.messages).toHaveLength(2);
    expect(complete.messages[1].content).toContain('Demo · no model inference');
    await demo.reset(complete.revision, complete.token);
    expect((await demo.status()).messages).toEqual([]);
    demo.dispose?.();
  });
  it('stops only the demonstration without committing pending input', async () => {
    vi.useFakeTimers();
    const demo = createDemoAdapter(100);
    await demo.chat('pending', 1, 'ui-demo-only');
    await demo.stop?.();
    await vi.advanceTimersByTimeAsync(200);
    expect((await demo.status()).messages).toEqual([]);
    expect((await demo.status()).error).toContain('Demo response stopped');
    demo.dispose?.();
  });
});
