import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import ts from 'typescript';
import { createMemoryHistory } from '@tanstack/react-router';
const compile = (source) =>
  ts.transpileModule(source, {
    compilerOptions: {
      target: ts.ScriptTarget.ES2022,
      module: ts.ModuleKind.ES2022,
      jsx: ts.JsxEmit.ReactJSX,
    },
  }).outputText;
const dataUrl = (source) =>
  `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`;
const routeUrl = dataUrl(
  compile(readFileSync(new URL('../lib/routes.ts', import.meta.url), 'utf8')),
);
const routes = await import(routeUrl);
const examples = {
  bookRef: 'book_math',
  topicRef: 'topic_algebra',
  documentRef: 'doc_source',
  paperId: 'b4fd7a17-e3dd-4403-9799-875e1abb464c',
  deckRef: 'deck_math',
  sessionRef: 'session_abc',
  position: '2',
};
const concrete = (path) => path.replace(/\$(\w+)/g, (_, key) => examples[key]);

test('every static and dynamic destination matches exactly and isolates roles', () => {
  const paths = [
    ...routes.staticApplicationRoutes,
    ...routes.dynamicApplicationRoutes,
  ];
  assert.equal(new Set(paths.map((item) => item.path)).size, paths.length);
  for (const item of paths) {
    const path = concrete(item.path);
    assert.equal(routes.describeRoute(path)?.view, item.view, path);
    assert.equal(routes.isApplicationPath(path), true, path);
    for (const role of ['admin', 'parent', 'student'])
      assert.equal(
        routes.roleAllowsPath(role, path),
        item.role === 'public' || item.role === role,
        `${role}: ${path}`,
      );
    assert.ok(routes.routeBreadcrumbs(path).length, path);
  }
});
test('unknown categories, malformed references and extra path segments are rejected', () => {
  for (const path of [
    '/admin/exam-documents/unknown',
    '/admin/textbooks-not-a-route',
    '/admin/textbooks/book_math/extra',
    '/admin/textbooks/%ZZ',
    '/admin/textbooks/book_%2Fsecret',
    '/admin/exam-documents/review/not-a-uuid',
    '/flashcards/sessions/session_abc/cards/0',
    '/flashcards/sessions/session_abc/cards/Infinity',
    '/student/textbooks/book_math/topics/other',
  ])
    assert.equal(routes.isApplicationPath(path), false, path);
});
test('query validation drops secrets, control characters and invalid learning parameters', () => {
  assert.deepEqual(
    routes.workspaceSearch({
      q: 'algebra',
      password: 'secret',
      answer: 'private',
      transcript: 'private',
      page: 'Infinity',
      source: '-1',
      count: '999',
      mode: 'unknown',
      difficulty: 'unknown',
      learner: '../other',
      status: 'draft\nunsafe',
    }),
    { q: 'algebra' },
  );
  assert.deepEqual(
    routes.workspaceSearch({
      page: 2,
      source: '1',
      count: '20',
      mode: 'review',
      subject: 'maths',
      learner: 'acct_maya',
    }),
    {
      page: '2',
      source: '1',
      count: '20',
      mode: 'review',
      subject: 'maths',
      learner: 'acct_maya',
    },
  );
});
test('topic breadcrumbs retain the parent textbook destination', () => {
  assert.ok(
    routes
      .routeBreadcrumbs('/admin/textbooks/book_math/topics/topic_algebra')
      .some((item) => item.path === '/admin/textbooks/book_math'),
  );
});
// Exercise the real router with an in-memory history, without browser or private data.
const resolve = (name) => import.meta.resolve(name);
let routerSource = compile(
  readFileSync(new URL('../lib/app-router.tsx', import.meta.url), 'utf8'),
);
routerSource = routerSource
  .replaceAll('"./routes"', JSON.stringify(routeUrl))
  .replaceAll("'./routes'", JSON.stringify(routeUrl));
for (const name of ['react/jsx-runtime', '@tanstack/react-router'])
  routerSource = routerSource
    .replaceAll(JSON.stringify(name), JSON.stringify(resolve(name)))
    .replaceAll(`'${name}'`, JSON.stringify(resolve(name)));
const { createAkuruRouter } = await import(dataUrl(routerSource));
test('memory history and real router resolve direct entry, filters and Back/Forward', () => {
  const router = createAkuruRouter(() => null);
  const first = '/admin/textbooks/book_math/topics/topic_algebra';
  const history = createMemoryHistory({
    initialEntries: [`${first}?page=2&password=secret`],
  });
  router.update({ history });
  const match = () =>
    router.matchRoutes(
      history.location.pathname,
      history.location.search
        ? Object.fromEntries(new URLSearchParams(history.location.search))
        : {},
    );
  assert.equal(
    match().at(-1).routeId,
    '/admin/textbooks/$bookRef/topics/$topicRef',
  );
  assert.deepEqual(match().at(-1)._strictSearch, { page: '2' });
  history.push('/admin/accounts?q=Maya');
  assert.equal(match().at(-1).routeId, '/admin/accounts');
  history.back();
  assert.equal(history.location.pathname, first);
  assert.deepEqual(match().at(-1)._strictSearch, { page: '2' });
  history.forward();
  assert.deepEqual(match().at(-1)._strictSearch, { q: 'Maya' });
});
