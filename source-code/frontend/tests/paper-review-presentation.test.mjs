import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import ts from 'typescript';
const source = readFileSync(
  new URL('../lib/paper-review-presentation.ts', import.meta.url),
  'utf8',
);
const { outputText } = ts.transpileModule(source, {
  compilerOptions: {
    target: ts.ScriptTarget.ES2022,
    module: ts.ModuleKind.ES2022,
  },
});
const {
  reviewAttentionCount,
  reviewQuestionList,
  reviewNeighbours,
  reviewNavigationAllowed,
  reviewHasChanges,
  reviewSavedPartIndex,
} = await import(
  `data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`
);
const questions = [
  { number: '1', status: 'approved' },
  { number: '2', status: 'needs_correction' },
  { number: '3', status: 'ready_for_approval' },
  { number: '4', status: 'excluded' },
  { number: '10', status: 'unreviewed' },
];
test('review filters preserve inventory order and excluded questions do not inflate pending work', () => {
  const snapshot = structuredClone(questions);
  assert.equal(reviewAttentionCount(questions), 3);
  assert.deepEqual(
    reviewQuestionList(questions, 'attention', '').map((q) => q.number),
    ['2', '3', '10'],
  );
  assert.deepEqual(
    reviewQuestionList(questions, 'excluded', '').map((q) => q.number),
    ['4'],
  );
  assert.deepEqual(
    reviewQuestionList(questions, 'all', '  QUESTION 10 ').map((q) => q.number),
    ['10'],
  );
  assert.deepEqual(reviewQuestionList(questions, 'approved', '10'), []);
  assert.deepEqual(reviewQuestionList([], 'all', ''), []);
  assert.deepEqual(questions, snapshot);
});
test('previous/next follow the full inventory and never wrap or jump from an unsaved new question', () => {
  assert.equal(reviewNeighbours(questions, '3').previous.number, '2');
  assert.equal(reviewNeighbours(questions, '3').next.number, '4');
  assert.equal(reviewNeighbours(questions, '1').previous, undefined);
  assert.equal(reviewNeighbours(questions, '10').next, undefined);
  assert.deepEqual(reviewNeighbours(questions, ''), {
    previous: undefined,
    next: undefined,
  });
  assert.deepEqual(reviewNeighbours([], '1'), {
    previous: undefined,
    next: undefined,
  });
});
test('navigation blocks in-flight saves and honours a cancelled discard without asking for clean drafts', () => {
  let prompts = 0;
  const confirm = () => {
    prompts++;
    return false;
  };
  assert.equal(reviewNavigationAllowed(true, true, confirm), false);
  assert.equal(reviewNavigationAllowed(false, false, confirm), true);
  assert.equal(prompts, 0);
  assert.equal(reviewNavigationAllowed(false, true, confirm), false);
  assert.equal(prompts, 1);
  assert.equal(
    reviewNavigationAllowed(false, true, () => true),
    true,
  );
});
test('edits before a question number is entered are protected, and saved snapshots reset dirty state', () => {
  const empty = {
    number: '',
    status: 'unreviewed',
    data: { prompt: '', parts: [] },
  };
  assert.equal(reviewHasChanges(empty, '', empty), false);
  const draft = {
    ...empty,
    data: { ...empty.data, prompt: 'Unsaved wording' },
  };
  assert.equal(reviewHasChanges(draft, '', empty), true);
  assert.equal(reviewHasChanges(draft, JSON.stringify(draft), empty), false);
  assert.equal(
    reviewHasChanges(
      { ...draft, status: 'approved' },
      JSON.stringify(draft),
      empty,
    ),
    true,
  );
});

test("save refresh preserves the selected subpart by label and handles removed parts", () => {
  assert.equal(reviewSavedPartIndex([{ label: "a" }, { label: "c" }], "c"), 1);
  assert.equal(reviewSavedPartIndex([{ label: "c" }, { label: "a" }], "c"), 0);
  assert.equal(reviewSavedPartIndex([{ label: "a" }], "c"), 0);
});
