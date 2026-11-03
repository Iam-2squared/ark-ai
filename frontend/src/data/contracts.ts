/** The frozen Local UI v1 wire contract; not a new backend capability claim. */
export type AdapterMode = 'demo' | 'local';
export type RuntimeState = 'loading' | 'ready' | 'generating' | 'error';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface LocalModel {
  name: string;
  local_model: boolean;
  family?: string | null;
  parameter_size?: string | null;
  quantization?: string | null;
  context_capacity: number;
}

export interface LocalStatus {
  state: RuntimeState;
  revision: number;
  intelligence: 'V2';
  model: LocalModel | null;
  messages: ChatMessage[];
  pending_message: string | null;
  error: string | null;
  warning: string | null;
  dropped_turns: number;
  logging: boolean;
  token: string;
}

export interface ArkAdapter {
  readonly mode: AdapterMode;
  status(signal?: AbortSignal): Promise<LocalStatus>;
  chat(message: string, revision: number, token: string): Promise<void>;
  reset(revision: number, token: string): Promise<void>;
  /** Only demonstration adapters may cancel: the frozen API has no stop endpoint. */
  stop?(): Promise<void>;
  dispose?(): void;
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number | null = null,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function nonnegativeInteger(value: unknown): value is number {
  return typeof value === 'number' && Number.isSafeInteger(value) && value >= 0;
}
function nullableString(value: unknown): value is string | null {
  return value === null || typeof value === 'string';
}

/** Fail closed. Malformed/unavailable data never becomes a synthetic ready state. */
export function parseLocalStatus(value: unknown): LocalStatus {
  const invalid = () => new ApiError('The local server returned an incompatible status contract.');
  if (
    !isRecord(value) ||
    !['loading', 'ready', 'generating', 'error'].includes(String(value.state)) ||
    !nonnegativeInteger(value.revision) ||
    value.intelligence !== 'V2' ||
    typeof value.token !== 'string' ||
    !/^[\x21-\x7e]{1,256}$/.test(value.token) ||
    typeof value.logging !== 'boolean' ||
    !nonnegativeInteger(value.dropped_turns) ||
    !nullableString(value.pending_message) ||
    !nullableString(value.error) ||
    !nullableString(value.warning) ||
    !Array.isArray(value.messages) ||
    value.messages.length > 200
  )
    throw invalid();
  const messages: ChatMessage[] = value.messages.map((message: unknown) => {
    if (
      !isRecord(message) ||
      (message.role !== 'user' && message.role !== 'assistant') ||
      typeof message.content !== 'string'
    )
      throw invalid();
    return { role: message.role, content: message.content };
  });
  let model: LocalModel | null = null;
  if (value.model !== null) {
    if (
      !isRecord(value.model) ||
      typeof value.model.name !== 'string' ||
      typeof value.model.local_model !== 'boolean' ||
      !nonnegativeInteger(value.model.context_capacity) ||
      value.model.context_capacity === 0
    )
      throw invalid();
    for (const field of ['family', 'parameter_size', 'quantization']) {
      if (field in value.model && !nullableString(value.model[field])) throw invalid();
    }
    model = {
      name: value.model.name,
      local_model: value.model.local_model,
      context_capacity: value.model.context_capacity,
      ...(value.model.family !== undefined ? { family: value.model.family as string | null } : {}),
      ...(value.model.parameter_size !== undefined
        ? { parameter_size: value.model.parameter_size as string | null }
        : {}),
      ...(value.model.quantization !== undefined
        ? { quantization: value.model.quantization as string | null }
        : {}),
    };
  }
  if ((value.state === 'ready' || value.state === 'generating') && !model) throw invalid();
  return {
    state: value.state as RuntimeState,
    revision: value.revision,
    intelligence: 'V2',
    model,
    messages,
    pending_message: value.pending_message,
    error: value.error,
    warning: value.warning,
    dropped_turns: value.dropped_turns,
    logging: value.logging,
    token: value.token,
  };
}
