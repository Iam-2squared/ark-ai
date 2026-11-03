import assert from 'node:assert/strict';
import { error, log } from 'node:console';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import process from 'node:process';
import { setTimeout as delay } from 'node:timers/promises';
import { fileURLToPath, pathToFileURL, URL } from 'node:url';
import ts from 'typescript';

/** Integration test only: never point a browser adapter at a remote origin. */
const origin = process.argv[2];
const match = /^http:\/\/127\.0\.0\.1:([1-9][0-9]{0,4})$/.exec(origin ?? '');
if (process.argv.length !== 3 || !match || Number(match[1]) > 65535) {
  error('Usage: npm run test:local-api -- http://127.0.0.1:PORT');
  process.exitCode = 1;
} else {
  let temporary;
  try {
    temporary = await mkdtemp(join(tmpdir(), 'ark-local-api-smoke-'));
    const sourceDirectory = fileURLToPath(new URL('../src/data/', import.meta.url));
    for (const name of ['contracts', 'local']) {
      const source = await readFile(join(sourceDirectory, `${name}.ts`), 'utf8');
      const compiled = ts.transpileModule(source, {
        fileName: `${name}.ts`,
        reportDiagnostics: true,
        compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
      });
      assert(
        !compiled.diagnostics?.some((item) => item.category === ts.DiagnosticCategory.Error),
        `Cannot transpile the actual ${name} adapter source.`,
      );
      const output =
        name === 'local'
          ? compiled.outputText.replace(
              /(\bfrom\s*['"])\.\/contracts(['"])/g,
              '$1./contracts.mjs$2',
            )
          : compiled.outputText;
      if (name === 'local') assert(output.includes("from './contracts.mjs'"));
      await writeFile(join(temporary, `${name}.mjs`), output);
    }
    const { createLocalAdapter } = await import(pathToFileURL(join(temporary, 'local.mjs')).href);
    const { ApiError, parseLocalStatus } = await import(
      pathToFileURL(join(temporary, 'contracts.mjs')).href
    );
    let sessionToken;

    function requireMock(snapshot) {
      assert(
        snapshot.model?.local_model === false &&
          snapshot.model.name === 'Echo — deterministic mock' &&
          snapshot.model.context_capacity === 4096 &&
          snapshot.logging === false,
        'Refusing to modify this session: start a dedicated ark.command_center --mock server.',
      );
      if (sessionToken !== undefined) {
        assert.equal(
          snapshot.token,
          sessionToken,
          'Server process changed; refusing further writes.',
        );
      }
    }

    const paths = new Set(['/api/status', '/api/chat', '/api/reset']);
    const fetcher = async (path, options = {}) => {
      assert(typeof path === 'string' && paths.has(path), 'Unexpected adapter endpoint.');
      const method = options.method ?? 'GET';
      assert(method === (path === '/api/status' ? 'GET' : 'POST'), 'Unexpected request method.');
      // Check the live identity before EVERY write. A restart between this read
      // and the write is also rejected by the original per-process request token.
      if (method === 'POST') {
        assert(sessionToken !== undefined, 'No verified mock session.');
        const check = await globalThis.fetch(`${origin}/api/status`, {
          headers: { Origin: origin },
          redirect: 'error',
          cache: 'no-store',
          signal: globalThis.AbortSignal.timeout(5_000),
        });
        assert(check.ok, 'Cannot recheck mock session identity.');
        requireMock(parseLocalStatus(await check.json()));
      }
      const headers = new globalThis.Headers(options.headers);
      headers.set('Origin', origin);
      return globalThis.fetch(`${origin}${path}`, { ...options, headers });
    };
    const adapter = createLocalAdapter(fetcher);

    async function ready() {
      const deadline = Date.now() + 10_000;
      while (Date.now() < deadline) {
        const snapshot = await adapter.status();
        if (snapshot.model !== null) requireMock(snapshot);
        assert(
          snapshot.state !== 'error' && !snapshot.error && !snapshot.warning,
          'Mock server reported an error; inspect it before retrying.',
        );
        if (snapshot.state === 'ready') return snapshot;
        await delay(30);
      }
      throw new Error('Mock server did not become ready within 10 seconds.');
    }

    const initial = await ready();
    requireMock(initial);
    sessionToken = initial.token;
    const message = 'こんにちは。ARKの接続テストです。';
    await adapter.chat(message, initial.revision, initial.token);
    const afterChat = await ready();
    assert(afterChat.revision > initial.revision);
    assert.deepEqual(afterChat.messages.slice(-2), [
      { role: 'user', content: message },
      { role: 'assistant', content: `ECHO: ${message}` },
    ]);
    await assert.rejects(
      adapter.chat('stale request must not run', initial.revision, initial.token),
      (failure) => failure instanceof ApiError && failure.status === 409,
    );
    const afterConflict = await ready();
    assert.deepEqual(afterConflict.messages, afterChat.messages, 'Stale request changed history.');
    await adapter.reset(afterConflict.revision, afterConflict.token);
    const afterReset = await ready();
    assert.deepEqual(afterReset.messages, []);
    assert.equal(afterReset.pending_message, null);
    assert(afterReset.revision > afterConflict.revision);
    log(
      'PASS: actual TypeScript local adapter → mock HTTP/V2 session; Japanese chat, stale 409, reset.',
    );
  } catch (failure) {
    error(failure instanceof Error ? failure.message : 'Local API integration test failed.');
    process.exitCode = 1;
  } finally {
    if (temporary) await rm(temporary, { recursive: true, force: true });
  }
}
