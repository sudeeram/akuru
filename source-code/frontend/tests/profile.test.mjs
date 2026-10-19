import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import ts from 'typescript';
const { outputText } = ts.transpileModule(
  readFileSync(new URL('../lib/profile.ts', import.meta.url), 'utf8'),
  {
    compilerOptions: {
      target: ts.ScriptTarget.ES2022,
      module: ts.ModuleKind.ES2022,
    },
  },
);
const { profileDetails } = await import(
  `data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`
);
const students = [
  {
    id: 'maya',
    parentId: 'parent-one',
    name: 'Maya',
    subjects: ['maths'],
    lastLoginAt: '2026-10-19T01:00:00Z',
  },
  { id: 'arun', parentId: 'parent-one', name: 'Arun', subjects: ['physics'] },
  {
    id: 'other-child',
    parentId: 'other-parent',
    name: 'Other child',
    subjects: ['chemistry'],
  },
];
const state = (role, id) => ({
  user: { role, id, name: 'Maya Perera', username: 'maya' },
  students,
  accounts: [{ id: 'other-user', lastLoginAt: '2026-10-18T01:00:00Z' }],
  subjects: [
    { id: 'maths', name: 'Mathematics' },
    { id: 'physics', name: 'Physics' },
  ],
});
test('Student self-profile never inherits a sibling enrolment', () => {
  const model = profileDetails(state('student', 'maya'));
  assert.equal(model.student.id, 'maya');
  assert.deepEqual(
    model.subjects.map((subject) => subject.id),
    ['maths'],
  );
  assert.deepEqual(model.children, []);
  assert.equal(model.lastLoginAt, '2026-10-19T01:00:00Z');
  const missing = profileDetails(state('student', 'unknown'));
  assert.equal(missing.student, undefined);
  assert.deepEqual(missing.subjects, []);
  assert.equal(missing.lastLoginAt, undefined);
});
test('Parent profile includes only linked children', () => {
  const model = profileDetails(state('parent', 'parent-one'));
  assert.deepEqual(
    model.children.map((child) => child.id),
    ['maya', 'arun'],
  );
  assert.equal(model.student, undefined);
  assert.deepEqual(model.subjects, []);
  assert.equal(model.lastLoginAt, undefined);
});
test('Admin profile does not project a learner or family identity', () => {
  const model = profileDetails(state('admin', 'admin'));
  assert.equal(model.roleName, 'Administrator');
  assert.equal(model.student, undefined);
  assert.deepEqual(model.children, []);
  assert.equal(model.lastLoginAt, undefined);
});
test('Profile initials have an empty-name fallback and reject unsupported roles', () => {
  assert.equal(profileDetails(state('admin', 'admin')).initials, 'MP');
  const data = state('admin', 'admin');
  data.user.name = '  ';
  assert.equal(profileDetails(data).initials, 'A');
  data.user.role = 'unknown';
  assert.throws(() => profileDetails(data), /Unsupported profile role/);
});
