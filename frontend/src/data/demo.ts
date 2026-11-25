import { ApiError, type ArkAdapter, type LocalStatus } from './contracts';

/** UI-only fixture. No inference, device access, metrics, tools, audit, or network. */
export function createDemoAdapter(delayMs = 650): ArkAdapter {
  let timer: ReturnType<typeof setTimeout> | undefined;
  let state: LocalStatus = {
    state: 'ready',
    revision: 1,
    intelligence: 'V2',
    model: {
      name: 'Echo — UI demonstration (no model)',
      local_model: false,
      context_capacity: 4096,
      family: null,
      quantization: null,
    },
    messages: [],
    pending_message: null,
    error: null,
    warning: null,
    dropped_turns: 0,
    logging: false,
    token: 'ui-demo-only',
  };
  const check = (revision: number, token: string) => {
    if (state.state !== 'ready' || revision !== state.revision || token !== state.token) {
      throw new ApiError('Demo state changed. Refresh before trying again.', 409);
    }
  };
  return {
    mode: 'demo',
    async status(signal) {
      if (signal?.aborted) throw new DOMException('Aborted', 'AbortError');
      return structuredClone(state);
    },
    async chat(message, revision, token) {
      check(revision, token);
      if (!message.trim() || [...message].length > 16_000)
        throw new ApiError('Enter a message of at most 16,000 characters.', 400);
      const text = message.trim();
      state = {
        ...state,
        revision: state.revision + 1,
        state: 'generating',
        pending_message: text,
        error: null,
      };
      timer = setTimeout(() => {
        state = {
          ...state,
          revision: state.revision + 1,
          state: 'ready',
          pending_message: null,
          messages: [
            ...state.messages,
            { role: 'user', content: text },
            {
              role: 'assistant',
              content: `**Demo · no model inference**\n\n${text}\n\nThis is an in-memory echo for interface testing. Connect the local backend to use ARK Intelligence.`,
            },
          ].slice(-200) as LocalStatus['messages'],
        };
        timer = undefined;
      }, delayMs);
    },
    async reset(revision, token) {
      check(revision, token);
      state = {
        ...state,
        revision: state.revision + 1,
        messages: [],
        pending_message: null,
        dropped_turns: 0,
        error: null,
        warning: null,
      };
    },
    async stop() {
      if (state.state !== 'generating') throw new ApiError('No demonstration is running.', 409);
      clearTimeout(timer);
      timer = undefined;
      state = {
        ...state,
        revision: state.revision + 1,
        state: 'ready',
        pending_message: null,
        error: 'Demo response stopped. The message was not committed.',
      };
    },
    dispose() {
      clearTimeout(timer);
    },
  };
}
