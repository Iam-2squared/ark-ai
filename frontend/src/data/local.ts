import { ApiError, parseLocalStatus, type ArkAdapter, type LocalStatus } from './contracts';

type Fetch = typeof globalThis.fetch;

/** Same-origin only. This adapter cannot target external hosts or execute tools. */
export function createLocalAdapter(fetcher: Fetch = globalThis.fetch.bind(globalThis)): ArkAdapter {
  async function request(
    path: '/api/status' | '/api/chat' | '/api/reset',
    payload?: object,
    token?: string,
    signal?: AbortSignal,
  ): Promise<unknown> {
    const controller = new AbortController();
    const abort = () => controller.abort();
    if (signal?.aborted) controller.abort();
    else signal?.addEventListener('abort', abort, { once: true });
    const timeout = setTimeout(() => controller.abort(), 15_000);
    try {
      const response = await fetcher(path, {
        method: payload ? 'POST' : 'GET',
        credentials: 'same-origin',
        cache: 'no-store',
        redirect: 'error',
        signal: controller.signal,
        ...(payload
          ? {
              headers: { 'Content-Type': 'application/json', 'X-ARK-Token': token ?? '' },
              body: JSON.stringify(payload),
            }
          : {}),
      });
      let body: unknown;
      try {
        body = await response.json();
      } catch {
        throw new ApiError('The local server did not return JSON.', response.status);
      }
      if (!response.ok) {
        const message =
          typeof body === 'object' &&
          body !== null &&
          'error' in body &&
          typeof body.error === 'string'
            ? body.error
            : `Local request failed (${response.status}).`;
        throw new ApiError(message, response.status);
      }
      return body;
    } finally {
      clearTimeout(timeout);
      signal?.removeEventListener('abort', abort);
    }
  }
  return {
    mode: 'local',
    async status(signal?: AbortSignal): Promise<LocalStatus> {
      return parseLocalStatus(await request('/api/status', undefined, undefined, signal));
    },
    async chat(message, revision, token) {
      if (!message.trim() || [...message].length > 16_000)
        throw new ApiError('Enter a message of at most 16,000 characters.');
      const body = await request('/api/chat', { message, revision }, token);
      if (
        typeof body !== 'object' ||
        body === null ||
        !('accepted' in body) ||
        body.accepted !== true
      ) {
        throw new ApiError('The server did not confirm acceptance. Refresh before retrying.');
      }
    },
    async reset(revision, token) {
      const body = await request('/api/reset', { revision }, token);
      if (typeof body !== 'object' || body === null || !('reset' in body) || body.reset !== true) {
        throw new ApiError('The server did not confirm reset. Refresh before retrying.');
      }
    },
  };
}
