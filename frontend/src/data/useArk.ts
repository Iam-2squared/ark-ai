import { useCallback, useEffect, useRef, useState } from 'react';
import { ApiError, type AdapterMode, type ArkAdapter, type LocalStatus } from './contracts';
import { createDemoAdapter } from './demo';
import { createLocalAdapter } from './local';

interface SubmittedTurn {
  text: string;
  revision: number;
  token: string;
}
export interface ArkConnection {
  status: LocalStatus | null;
  connected: boolean;
  loading: boolean;
  error: string | null;
  pending: boolean;
  uncertain: boolean;
  recoveredDraft: string | null;
  clearRecoveredDraft(): void;
  refresh(): Promise<void>;
  send(message: string): Promise<boolean>;
  reset(): Promise<boolean>;
  stop(): Promise<boolean>;
  canStop: boolean;
}

function messageOf(error: unknown): string {
  return error instanceof Error ? error.message : 'The local request failed.';
}

/** Poll complete snapshots today; a future streaming transport can share this contract. */
export function useArk(mode: AdapterMode): ArkConnection {
  const [status, setStatus] = useState<LocalStatus | null>(null);
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uncertain, setUncertain] = useState(false);
  const [recoveredDraft, setRecoveredDraft] = useState<string | null>(null);
  const adapterRef = useRef<ArkAdapter | null>(null);
  const stateRef = useRef<LocalStatus | null>(null);
  const connectedRef = useRef(false);
  const activeRef = useRef(false);
  const epoch = useRef(0);
  const locked = useRef(false);
  const reading = useRef<Promise<void> | null>(null);
  const readAbort = useRef<AbortController | null>(null);
  const submitted = useRef<SubmittedTurn | null>(null);

  const refresh = useCallback(async (): Promise<void> => {
    if (!activeRef.current || !adapterRef.current) return;
    if (reading.current) return reading.current;
    const adapter = adapterRef.current;
    const currentEpoch = epoch.current;
    const controller = new AbortController();
    readAbort.current = controller;
    const read = (async () => {
      try {
        const incoming = await adapter.status(controller.signal);
        if (!activeRef.current || currentEpoch !== epoch.current) return;
        const previous = stateRef.current;
        if (
          previous &&
          previous.token === incoming.token &&
          incoming.revision < previous.revision
        ) {
          throw new ApiError('A stale status was rejected. Refresh before sending again.');
        }
        stateRef.current = incoming;
        connectedRef.current = true;
        setStatus(incoming);
        setConnected(true);
        const turn = submitted.current;
        if (turn && incoming.token !== turn.token) {
          setRecoveredDraft(turn.text);
          setUncertain(true);
          setError('The backend restarted during the request. Check history before sending again.');
          submitted.current = null;
        } else if (turn && incoming.revision > turn.revision && incoming.state !== 'generating') {
          // The frozen backend sets error on a failed generation. A logging-only
          // warning keeps a committed answer; transcript length can remain 200.
          if (incoming.error) setRecoveredDraft(turn.text);
          submitted.current = null;
        }
        // Mutation errors remain visible until an explicit new action or a manual refresh.
      } catch (cause) {
        if (!activeRef.current || currentEpoch !== epoch.current || controller.signal.aborted)
          return;
        connectedRef.current = false;
        setConnected(false);
        setError(`${messageOf(cause)} No request is retried automatically.`);
      } finally {
        if (activeRef.current && currentEpoch === epoch.current) setLoading(false);
      }
    })();
    reading.current = read;
    try {
      await read;
    } finally {
      if (reading.current === read) reading.current = null;
      if (readAbort.current === controller) readAbort.current = null;
    }
  }, []);

  useEffect(() => {
    const adapter = mode === 'local' ? createLocalAdapter() : createDemoAdapter();
    adapterRef.current = adapter;
    activeRef.current = true;
    epoch.current += 1;
    stateRef.current = null;
    connectedRef.current = false;
    locked.current = false;
    reading.current = null;
    submitted.current = null;
    setStatus(null);
    setConnected(false);
    setLoading(true);
    setPending(false);
    setError(null);
    setUncertain(false);
    setRecoveredDraft(null);
    let timer: ReturnType<typeof setTimeout>;
    let disposed = false;
    const poll = async () => {
      await refresh();
      if (!disposed)
        timer = setTimeout(
          () => {
            void poll();
          },
          stateRef.current?.state === 'generating' ? 350 : 1500,
        );
    };
    void poll();
    return () => {
      disposed = true;
      activeRef.current = false;
      epoch.current += 1;
      clearTimeout(timer);
      readAbort.current?.abort();
      adapter.dispose?.();
      adapterRef.current = null;
    };
  }, [mode, refresh]);

  const act = useCallback(
    async (action: 'chat' | 'reset' | 'stop', text = ''): Promise<boolean> => {
      const adapter = adapterRef.current;
      if (!activeRef.current || !adapter || locked.current || !connectedRef.current) return false;
      const before = stateRef.current;
      if (
        !before ||
        (action === 'stop'
          ? !adapter.stop || before.state !== 'generating'
          : before.state !== 'ready')
      )
        return false;
      if (action === 'chat' && (!text.trim() || [...text].length > 16_000)) return false;
      const currentEpoch = epoch.current;
      locked.current = true; // Synchronous guard also covers rapid double clicks before React renders.
      setPending(true);
      setError(null);
      setUncertain(false);
      let accepted = false;
      try {
        // Drain an older poll; then request a fresh revision before a mutation.
        if (reading.current) await reading.current;
        await refresh();
        if (!activeRef.current || currentEpoch !== epoch.current) return false;
        const current = stateRef.current;
        if (
          !connectedRef.current ||
          !current ||
          (action === 'stop' ? current.state !== 'generating' : current.state !== 'ready')
        )
          return false;
        if (current.token !== before.token || current.revision !== before.revision) {
          setError('The conversation changed. Review the refreshed history before trying again.');
          return false;
        }
        if (action === 'chat') {
          await adapter.chat(text, current.revision, current.token);
          if (!activeRef.current || currentEpoch !== epoch.current) return false;
          submitted.current = { text, revision: current.revision, token: current.token };
          setRecoveredDraft(null);
        } else if (action === 'reset') {
          await adapter.reset(current.revision, current.token);
          if (!activeRef.current || currentEpoch !== epoch.current) return false;
          submitted.current = null;
          setRecoveredDraft(null);
        } else {
          await adapter.stop?.();
          if (!activeRef.current || currentEpoch !== epoch.current) return false;
        }
        accepted = true;
      } catch (cause) {
        if (activeRef.current && currentEpoch === epoch.current) {
          const ambiguous = !(cause instanceof ApiError && cause.status !== null);
          setUncertain(ambiguous);
          setError(
            `${messageOf(cause)} ${
              ambiguous
                ? 'Acceptance is unknown. Check the refreshed conversation before retrying.'
                : 'The action was not accepted. Check the refreshed state before retrying.'
            }`,
          );
        }
      } finally {
        if (activeRef.current && currentEpoch === epoch.current) {
          if (reading.current) await reading.current;
          await refresh();
          locked.current = false;
          setPending(false);
        }
      }
      return accepted;
    },
    [refresh],
  );

  const manualRefresh = useCallback(async () => {
    setError(null);
    await refresh();
  }, [refresh]);
  const send = useCallback((message: string) => act('chat', message), [act]);
  const reset = useCallback(() => act('reset'), [act]);
  const stop = useCallback(() => act('stop'), [act]);
  const clearRecoveredDraft = useCallback(() => setRecoveredDraft(null), []);
  return {
    status,
    connected,
    loading,
    error,
    pending,
    uncertain,
    recoveredDraft,
    clearRecoveredDraft,
    refresh: manualRefresh,
    send,
    reset,
    stop,
    canStop: mode === 'demo' && connected && !pending && status?.state === 'generating',
  };
}
