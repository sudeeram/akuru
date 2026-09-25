import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import test from 'node:test';

const read = path => readFileSync(new URL(path, import.meta.url), 'utf8');
const page = read('../app/page.tsx');
const routes = read('../lib/routes.ts');
const router = read('../lib/app-router.tsx');
const queryClient = read('../lib/query-client.ts');
const queryKeys = read('../lib/query-keys.ts');
const flashcards = read('../features/flashcards.tsx');
const apiClient = read('../api/core/client.ts');
const nginx = read('../../../deploy/ubuntu/nginx-akuru.conf');

test('TanStack providers and centralized routes form the application boundary', () => {
  assert.match(page, /QueryClientProvider/);
  assert.match(page, /RouterProvider/);
  assert.match(router, /createRootRoute/);
  assert.match(router, /validateSearch/);
  assert.match(routes, /const roleViews/);
  assert.match(routes, /roleAllowsPath/);
  assert.match(routes, /isApplicationPath/);
  assert.ok(existsSync(new URL('../app/[...path]/page.tsx', import.meta.url)));
});

test('Admin, Parent and Student paths are separate and legacy hashes are migrated', () => {
  assert.match(routes, /accounts: '\/admin\/accounts'/);
  assert.match(routes, /students: '\/parent\/students'/);
  assert.match(routes, /subjects: '\/student\/subjects'/);
  assert.match(page, /window\.location\.hash\.slice\(1\)/);
  assert.match(page, /window\.history\.replaceState/);
  assert.match(page, /roleAllowsPath/);
});

test('private Query data is actor scoped and erased on identity changes', () => {
  assert.match(queryKeys, /actorRef/);
  assert.match(queryClient, /cancelQueries/);
  assert.match(queryClient, /queryClient\.clear\(\)/);
  assert.doesNotMatch(queryClient, /persistQueryClient|localStorage|sessionStorage/);
  assert.ok((page.match(/clearPrivateQueryState\(\)/g) ?? []).length >= 2);
  assert.match(apiClient, /akuru:unauthorized/);
  assert.match(page, /addEventListener\('akuru:unauthorized'/);
});

test('Flashcard deep links cover decks, modes, sessions and current cards', () => {
  assert.ok(routes.includes('`/flashcards/decks/${encodeURIComponent(deckRef)}`'));
  assert.ok(routes.includes('`/flashcards/sessions/${encodeURIComponent(sessionRef)}/cards/${Math.max(1, position)}`'));
  for (const mode of ['review', 'difficult'])
    assert.match(routes, new RegExp(`['"]${mode}['"]`));
  for (const removedMode of ['quick', 'normal', 'full_topic', 'due_today', 'unit_mixed'])
    assert.doesNotMatch(routes, new RegExp(`['"]${removedMode}['"]`));
  assert.match(flashcards, /getFlashcardSession/);
  assert.match(flashcards, /flashcardPaths\.card/);
  assert.match(flashcards, /Flashcard deck unavailable/);
});

test('navigation updates title and focus for keyboard and assistive technology users', () => {
  assert.match(page, /document\.title/);
  assert.match(page, /getElementById\('main-content'\)\?\.focus/);
  assert.match(page, /tabIndex=\{-1\}/);
});

test('card-to-card navigation does not show the feature transition loader', () => {
  assert.match(page, /withinFlashcardSession/);
  assert.match(page, /if \(!withinFlashcardSession\) window\.dispatchEvent/);
});

test('production routing keeps APIs, health and build assets outside application fallback', () => {
  assert.match(nginx, /location \/api\//);
  assert.match(nginx, /location = \/health/);
  assert.match(nginx, /location \^~ \/_next\//);
  assert.match(nginx, /try_files \$uri =404/);
  assert.match(nginx, /location \/ \{/);
  assert.ok(nginx.indexOf('location /api/') < nginx.indexOf('location / {'));
});
