import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import ts from 'typescript';
const compile = (file) =>
  ts.transpileModule(readFileSync(new URL(file, import.meta.url), 'utf8'), {
    compilerOptions: {
      target: ts.ScriptTarget.ES2022,
      module: ts.ModuleKind.ES2022,
    },
  }).outputText;
const url = (source) =>
  `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`;
const errorsUrl = url(compile('../api/core/errors.ts'));
const csrfUrl = url(compile('../api/core/csrf.ts'));
const { request } = await import(
  url(
    compile('../api/core/client.ts')
      .replace("'./errors'", JSON.stringify(errorsUrl))
      .replace("'./csrf'", JSON.stringify(csrfUrl)),
  )
);
const { ApiError } = await import(errorsUrl);
async function withClient(response, run) {
  const originalFetch = globalThis.fetch;
  const originalWindow = globalThis.window;
  const originalDocument = globalThis.document;
  const target = new EventTarget();
  let expired = 0;
  target.addEventListener('akuru:unauthorized', () => expired++);
  globalThis.window = target;
  globalThis.document = { cookie: '' };
  globalThis.fetch =
    typeof response === 'function' ? response : async () => response;
  try {
    await run(() => expired);
  } finally {
    globalThis.fetch = originalFetch;
    globalThis.window = originalWindow;
    globalThis.document = originalDocument;
  }
}
test('confirmed expiry dispatches before a broken response body is read', async () => {
  await withClient(
    {
      status: 401,
      text: async () => {
        throw new TypeError('Failed to fetch');
      },
    },
    async (count) => {
      await assert.rejects(
        request('auth/me'),
        (e) => e instanceof ApiError && e.status === 401,
      );
      assert.equal(count(), 1);
    },
  );
});
test('state 401 remains typed for the portal observer without treating initial login as an expiry event', async () => {
  await withClient(new Response('', { status: 401 }), async (count) => {
    await assert.rejects(
      request('state'),
      (e) => e instanceof ApiError && e.status === 401,
    );
    assert.equal(count(), 0);
  });
});
test('invalid login preserves its useful validation message without an expiry redirect', async () => {
  await withClient(
    new Response(
      JSON.stringify({ detail: 'Incorrect username or password.' }),
      { status: 401 },
    ),
    async (count) => {
      await assert.rejects(
        request('auth/login', { method: 'POST', body: {} }),
        (e) =>
          e.status === 401 && e.message === 'Incorrect username or password.',
      );
      assert.equal(count(), 0);
    },
  );
});
test('network failure is recoverable and does not log out a possibly valid session', async () => {
  await withClient(
    async () => {
      throw new TypeError('Failed to fetch');
    },
    async (count) => {
      await assert.rejects(
        request('auth/me'),
        (e) => e.status === 0 && e.message.includes('Check your connection'),
      );
      assert.equal(count(), 0);
    },
  );
});
test('an interrupted successful response is a connection error rather than proof of expiry', async () => {
  await withClient(
    {
      status: 200,
      ok: true,
      text: async () => {
        throw new TypeError('Failed to fetch');
      },
    },
    async (count) => {
      await assert.rejects(
        request('state'),
        (e) => e.status === 0 && !e.message.includes('Failed to fetch'),
      );
      assert.equal(count(), 0);
    },
  );
});
test('server failures and successful requests preserve their status and do not signal expiry', async () => {
  await withClient(
    new Response(JSON.stringify({ detail: 'Try again later.' }), {
      status: 503,
    }),
    async (count) => {
      await assert.rejects(request('state'), (e) => e.status === 503);
      assert.equal(count(), 0);
    },
  );
  await withClient(
    new Response(JSON.stringify({ id: 'account_test' })),
    async (count) => {
      assert.deepEqual(await request('auth/me'), { id: 'account_test' });
      assert.equal(count(), 0);
    },
  );
});

test('a late 401 from the previous session cannot sign out a newly authenticated user', async () => {
  let resolveOldRequest;
  const oldResponse = new Promise((resolve) => {
    resolveOldRequest = resolve;
  });
  await withClient(
    async (path) =>
      path.endsWith('/auth/login')
        ? new Response(JSON.stringify({ ok: true }))
        : oldResponse,
    async (count) => {
      const oldRequest = request('auth/me');
      const rejected = assert.rejects(oldRequest, (e) => e.status === 401);
      await request('auth/login', { method: 'POST', body: {} });
      resolveOldRequest(new Response('', { status: 401 }));
      await rejected;
      assert.equal(count(), 0);
    },
  );
});
