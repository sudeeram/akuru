import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const api = readFileSync(new URL('../lib/api.ts', import.meta.url), 'utf8');
const page = readFileSync(new URL('../app/page.tsx', import.meta.url), 'utf8');
const admin = readFileSync(
  new URL('../features/admin.tsx', import.meta.url),
  'utf8',
);
const vite = readFileSync(
  new URL('../vite.config.ts', import.meta.url),
  'utf8',
);
const uiFeatures = readFileSync(
  new URL('../app/ui-features/page.tsx', import.meta.url),
  'utf8',
);
const layout = readFileSync(
  new URL('../app/layout.tsx', import.meta.url),
  'utf8',
);
const routeLoader = readFileSync(
  new URL('../components/route-loading-overlay.tsx', import.meta.url),
  'utf8',
);
const styles = readFileSync(
  new URL('../app/globals.css', import.meta.url),
  'utf8',
);

test('frontend uses the FastAPI v1 boundary and local proxy', () => {
  assert.match(api, /fetch\('\/api\/v1\/' \+ path/);
  assert.match(vite, /'\/api\/v1'/);
  assert.match(vite, /127\.0\.0\.1:8000/);
});

test('account UUIDs remain internal identifiers', () => {
  assert.doesNotMatch(admin, /label: `\$\{a\.name\} \(\$\{a\.id\}\)`/);
  assert.doesNotMatch(admin, /\{s\.id\} · Parent: \{s\.parentId\}/);
  assert.match(admin, /@\{s\.username\}/);
  assert.match(admin, /@\{a\.username\}/);
});

test('frontend contains no bundled mock credentials', () => {
  assert.doesNotMatch(page, /Local demo accounts/);
  assert.doesNotMatch(page, /demo-accounts/);
  assert.doesNotMatch(vite, /local-server/);
});

test('admin UI reference is routed and API-authorized', () => {
  assert.match(page, /href="\/ui-features"/);
  assert.match(uiFeatures, /api\('admin\/ui-features'\)/);
  assert.match(uiFeatures, /Admin access required/);
  assert.match(uiFeatures, /AKURU-owned components/);
  assert.match(uiFeatures, /UI feature categories/);
  assert.match(uiFeatures, /Workflow board/);
  assert.match(uiFeatures, /Charts and trends/);
  assert.match(uiFeatures, /Access and communication/);
});

test('page transitions rotate through AKURU BOT loading scenes', () => {
  assert.match(layout, /RouteLoadingOverlay/);
  assert.equal(
    (routeLoader.match(/\/akuru-loading\/akuru-loading-/g) ?? []).length,
    5,
  );
  assert.match(routeLoader, /route-loader/);
  assert.match(routeLoader, /hashchange/);
  assert.match(styles, /prefers-reduced-motion/);
});

test('all portal roles receive horizontally scrollable navigation', () => {
  assert.match(page, /portal-horizontal-nav/);
  assert.match(page, /aria-current=\{view === id \? 'page'/);
  assert.match(page, /nav\.map\(\(\[id, label, Icon\]\)/);
  assert.match(styles, /overflow-x: auto/);
  assert.match(styles, /-webkit-overflow-scrolling: touch/);
  assert.doesNotMatch(page, /SidebarProvider|PortalNavigation|app-sidebar/);
});
