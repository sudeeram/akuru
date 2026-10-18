import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import ts from 'typescript';
const source = readFileSync(
  new URL('../lib/dashboard-summary.ts', import.meta.url),
  'utf8',
);
const { outputText } = ts.transpileModule(source, {
  compilerOptions: {
    target: ts.ScriptTarget.ES2022,
    module: ts.ModuleKind.ES2022,
  },
});
const { learnerSummary, markedScore } = await import(
  `data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`
);
const attempt = (overrides = {}) => ({
  studentId: 'maya',
  subject: 'maths',
  status: 'reviewed',
  mark: 8,
  maxMarks: 10,
  createdAt: new Date(2026, 9, 14, 12).toISOString(),
  ...overrides,
});

test('dashboard totals isolate siblings and count only the current week through now', () => {
  const now = new Date(2026, 9, 18, 12);
  const attempts = [
    attempt(),
    attempt({ studentId: 'arun' }),
    attempt({ createdAt: new Date(2026, 9, 11, 12).toISOString() }),
    attempt({ createdAt: new Date(2026, 9, 19, 12).toISOString() }),
    attempt({ status: 'needs-review', mark: null }),
  ];
  const assignments = [
    { id: '1', studentId: 'maya', completed: false, due: '2026-10-21' },
    { id: '2', studentId: 'maya', completed: true, due: '2026-10-15' },
    { id: '3', studentId: 'arun', completed: false, due: '2026-10-16' },
    { id: '4', studentId: 'maya', completed: false, due: '2026-10-19' },
  ];
  const summary = learnerSummary(attempts, assignments, 'maya', now);
  assert.equal(summary.weekly.length, 2);
  assert.equal(summary.attempts.length, 4);
  assert.equal(summary.pending.length, 1);
  assert.equal(summary.completed, 1);
  assert.equal(summary.totalAssignments, 3);
  assert.deepEqual(
    summary.assignments.map((item) => item.id),
    ['4', '1'],
  );
  assert.equal(assignments[0].id, '1');
});

test('subject score is weighted by marks and excludes unreviewed or unmarked results', () => {
  const attempts = [
    attempt(),
    attempt({ mark: 1, maxMarks: 2 }),
    attempt({ status: 'needs-review', mark: 0 }),
    attempt({ subject: 'english', mark: 0 }),
    attempt({ mark: null }),
    attempt({ maxMarks: 0 }),
  ];
  assert.equal(markedScore(attempts, 'maths'), 75);
  assert.equal(markedScore([], 'maths'), null);
  assert.equal(markedScore([attempt({ mark: null })], 'maths'), null);
  assert.equal(markedScore([attempt({ mark: 0 })], 'maths'), 0);
});
