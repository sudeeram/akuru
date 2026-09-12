import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const api = readFileSync(new URL('../lib/api.ts', import.meta.url), 'utf8');
const page = readFileSync(new URL('../app/page.tsx', import.meta.url), 'utf8');
const vite = readFileSync(new URL('../vite.config.ts', import.meta.url), 'utf8');

test('frontend uses the FastAPI v1 boundary and local proxy', () => {
  assert.match(api, /fetch\('\/api\/v1\/' \+ path/);
  assert.match(vite, /'\/api\/v1'/);
  assert.match(vite, /127\.0\.0\.1:8000/);
});

test('frontend contains no bundled mock credentials', () => {
  assert.doesNotMatch(page, /Local demo accounts/);
  assert.doesNotMatch(page, /demo-accounts/);
  assert.doesNotMatch(vite, /local-server/);
});
