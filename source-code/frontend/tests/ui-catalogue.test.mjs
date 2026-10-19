import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import ts from 'typescript';
const load = async (path) =>
  import(
    `data:text/javascript;base64,${Buffer.from(ts.transpileModule(readFileSync(new URL(path, import.meta.url), 'utf8'), { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ES2022 } }).outputText).toString('base64')}`
  );
const { catalogueEntries, findEntries, catalogueFromHash } = await load(
  '../features/ui-reference/catalogue/registry.ts',
);
const { workspaceRows, pageWindow, attendanceSummary, sampleRecords } =
  await load('../features/ui-reference/catalogue/models.ts');
test('all 27 families have unique deep links and searchable use cases', () => {
  assert.equal(catalogueEntries.length, 27);
  assert.equal(new Set(catalogueEntries.map((e) => e.id)).size, 27);
  for (const entry of catalogueEntries)
    assert.equal(catalogueFromHash(`#ui-catalog-${entry.id}`), entry.id);
  assert.equal(catalogueFromHash('#ui-catalog-invented'), null);
  assert.equal(catalogueFromHash('#ui-components'), null);
  assert.equal(findEntries('  ').length, 27);
  assert.ok(findEntries('loading').length > 0);
  assert.ok(findEntries('card').some((e) => e.id === 'cards'));
  assert.equal(findEntries('impossible-no-match').length, 0);
  assert.ok(findEntries('  GRID  ').some((e) => e.id === 'grid'));
});
test('workspace filtering, sorting and pagination remain consistent at boundaries', () => {
  const filtered = workspaceRows('atomic', 'Ready', false);
  assert.ok(filtered.length > 0);
  assert.ok(
    filtered.every((r) => r.title.includes('Atomic') && r.status === 'Ready'),
  );
  assert.deepEqual(
    workspaceRows('atomic', 'Ready', true),
    [...filtered].reverse(),
  );
  const last = pageWindow(sampleRecords, 999, 5);
  assert.equal(last.current, 5);
  assert.equal(last.rows.length, 3);
  assert.equal(last.start, 21);
  assert.equal(last.end, 23);
  const empty = pageWindow([], 4, 5);
  assert.deepEqual(empty, { current: 1, pages: 1, rows: [], start: 0, end: 0 });
  assert.equal(pageWindow(filtered, 4, 25).current, 1);
  assert.equal(pageWindow(sampleRecords, -1, 5).current, 1);
});
test('attendance distinguishes no data, unmarked and absent; late counts as attended', () => {
  assert.deepEqual(attendanceSummary([null, null]), {
    present: 0,
    late: 0,
    absent: 0,
    marked: 0,
    total: 2,
    rate: null,
  });
  assert.equal(attendanceSummary(['Absent']).rate, 0);
  assert.equal(attendanceSummary(['Late']).rate, 100);
  const initial = ['Present', 'Late', null, 'Absent'];
  assert.equal(attendanceSummary(initial).rate, 67);
  const changed = [...initial];
  changed[2] = 'Present';
  assert.equal(attendanceSummary(changed).rate, 75);
  assert.equal(attendanceSummary(changed).marked, 4);
  assert.equal(attendanceSummary(initial).marked, 3);
  assert.equal(attendanceSummary([]).rate, null);
});
