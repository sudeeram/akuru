import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import ts from 'typescript';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
const read = (path) => readFileSync(new URL(path, import.meta.url), 'utf8');
const compile = (source) =>
  ts.transpileModule(source, {
    compilerOptions: {
      target: ts.ScriptTarget.ES2022,
      module: ts.ModuleKind.ES2022,
      jsx: ts.JsxEmit.ReactJSX,
    },
  }).outputText;
const url = (source) =>
  `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`;
const helper = url(compile(read('../lib/badges.ts')));
const { badgeStatus, badgeCount } = await import(helper);
let source = compile(read('../components/portal/badges.tsx'))
  .replaceAll("'@/lib/badges'", JSON.stringify(helper))
  .replaceAll('"@/lib/badges"', JSON.stringify(helper));
for (const name of ['react/jsx-runtime', 'lucide-react'])
  source = source
    .replaceAll(JSON.stringify(name), JSON.stringify(import.meta.resolve(name)))
    .replaceAll(`'${name}'`, JSON.stringify(import.meta.resolve(name)));
const { StatusBadge, MetadataBadge, CountBadge, ReviewBadge } = await import(
  url(source)
);
test('explicit statuses never confuse incomplete, unreviewed or unpublished with success', () => {
  for (const status of [
    'incomplete',
    'unpublished',
    'not ready',
    'not checked',
    'unreviewed',
    'review_required',
    'pending_review',
    'awaiting review',
    'new backend state',
  ])
    assert.notEqual(badgeStatus(status).tone, 'success', status);
  for (const status of [
    'approved',
    'published',
    'reviewed',
    'completed',
    'ready',
    'enrolled',
  ])
    assert.equal(badgeStatus(status).tone, 'success', status);
  for (const status of ['failed', 'blocked', 'overdue', 'high'])
    assert.equal(badgeStatus(status).tone, 'danger', status);
  assert.equal(badgeStatus('review_required').tone, 'warning');
  assert.equal(badgeStatus('following each other').tone, 'accent');
  assert.equal(badgeStatus('draft').tone, 'neutral');
  assert.equal(badgeStatus('Visible').icon, 'eye');
  assert.equal(badgeStatus('Hidden').icon, 'hidden');
});
test('status badges keep readable text, decorative icons and safe escaping', () => {
  const html = renderToStaticMarkup(
    createElement(StatusBadge, { status: 'failed' }),
  );
  assert.match(html, /aria-label="Status: Needs attention"/);
  assert.match(html, /data-tone="danger"/);
  assert.match(html, /aria-hidden="true"/);
  const untrusted = renderToStaticMarkup(
    createElement(MetadataBadge, null, '<script>alert(1)</script>'),
  );
  assert.doesNotMatch(untrusted, /<script>/);
  assert.match(untrusted, /&lt;script&gt;/);
  const review = renderToStaticMarkup(
    createElement(ReviewBadge, { state: 'partial' }, 'Partially reviewed'),
  );
  assert.match(review, /data-tone="warning"/);
  assert.match(review, /Partially reviewed/);
});
test('notification counts cap visually while retaining the actual accessible count', () => {
  for (const [count, expected] of [
    [0, '0'],
    [3, '3'],
    [100, '99+'],
    [-4, '0'],
    [2.9, '2'],
    [NaN, '0'],
    [Infinity, '0'],
  ])
    assert.equal(badgeCount(count), expected);
  const html = renderToStaticMarkup(
    createElement(CountBadge, { count: 150, label: 'unread notifications' }),
  );
  assert.match(html, /150 unread notifications/);
  assert.match(html, /99\+/);
});
test('all semantic badge palettes have readable text contrast and allow long labels to wrap', () => {
  const css = read('../app/badges.css');
  const luminance = (hex) => {
    const rgb = [1, 3, 5]
      .map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
      .map((v) => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
    return rgb[0] * 0.2126 + rgb[1] * 0.7152 + rgb[2] * 0.0722;
  };
  const palettes = [
    ...css.matchAll(
      /--badge-bg:\s*(#[0-9a-f]{6});\s*--badge-fg:\s*(#[0-9a-f]{6})/gi,
    ),
  ];
  assert.equal(palettes.length, 6);
  for (const [, bg, fg] of palettes) {
    const a = luminance(bg),
      b = luminance(fg);
    assert.ok(
      (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05) >= 4.5,
      `${fg} on ${bg}`,
    );
  }
  assert.match(css, /white-space:\s*normal/);
  assert.match(css, /overflow-wrap:\s*anywhere/);
});
