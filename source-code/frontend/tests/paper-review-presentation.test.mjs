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
  reviewAccuracy,
  reviewProvenance,
  reviewNeighbours,
  reviewNavigationAllowed,
  reviewHasChanges,
  reviewSavedPartIndex,
  reviewPageLinkState,
  reviewPartSaveState,
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
test('lowest-confidence sort keeps unscored questions last without changing the inventory', () => {
  const rows = [
    {number:'1',status:'unreviewed',data:{extractionConfidence:{percent:70}}},
    {number:'2',status:'unreviewed',data:{extractionConfidence:{percent:35}}},
    {number:'3',status:'unreviewed',data:{}},
  ];
  assert.deepEqual(reviewQuestionList(rows,'all','',true).map(q=>q.number),['2','1','3']);
  assert.deepEqual(rows.map(q=>q.number),['1','2','3']);
});
test('accuracy comparisons take precedence over import estimates and stale comparisons are unscored', () => {
  const model = {role:'paper',method:'codex_assisted',provider:'Test',modelId:'test-model-v2'};
  const assessed = {number:'1',status:'approved',data:{extractionConfidence:{percent:45}},
    accuracyAnalysis:{isCurrent:true,question:{percent:92},provenance:[model]}};
  assert.equal(reviewAccuracy(assessed),92);
  assert.equal(reviewAccuracy({...assessed,accuracyAnalysis:{...assessed.accuracyAnalysis,isCurrent:false}}),undefined);
  assert.equal(reviewQuestionList([assessed],'all','',false,'test-model-v2').length,1);
  assert.equal(reviewQuestionList([assessed],'all','',false,'other-model').length,0);
});
test('subpart provenance overrides only the matching source role', () => {
  const analysis = {provenance:[{role:'paper',modelId:'paper-model'},{role:'scheme',modelId:'scheme-model'}],
    parts:[{label:'a',provenance:[{role:'scheme',modelId:'part-scheme-model'}]}]};
  assert.deepEqual(reviewProvenance(analysis,'a').map(source=>source.modelId),['paper-model','part-scheme-model']);
  assert.deepEqual(reviewProvenance(analysis,'b').map(source=>source.modelId),['paper-model','scheme-model']);
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

test('page-link status distinguishes page links from exact block evidence', () => {
  const sources = [{ page: 1, blockId: 'a' }, { page: 1, blockId: 'b' }, { page: 2 }];
  assert.deepEqual(reviewPageLinkState(sources, 1), { pageLinked: false, linkedBlockCount: 2 });
  const linked = [...sources, { page: 1, blockId: null }];
  assert.deepEqual(reviewPageLinkState(linked, 1), { pageLinked: true, linkedBlockCount: 2 });
  // Removing only page-level evidence preserves the independently linked blocks.
  assert.deepEqual(reviewPageLinkState(linked.filter((s) => !(s.page === 1 && !s.blockId)), 1), { pageLinked: false, linkedBlockCount: 2 });
  assert.deepEqual(reviewPageLinkState(sources, 3), { pageLinked: false, linkedBlockCount: 0 });
});

test('approval is green only after the exact part has been saved', () => {
  const saved = { label: 'a', status: 'unreviewed', prompt: 'Original' };
  const approved = { ...saved, status: 'approved' };
  assert.deepEqual(reviewPartSaveState(approved, [saved]), { unsaved: true, displayStatus: 'unsaved' });
  assert.deepEqual(reviewPartSaveState(approved, [approved]), { unsaved: false, displayStatus: 'approved' });
  assert.equal(reviewPartSaveState({ ...approved, prompt: 'Edited' }, [approved]).displayStatus, 'unsaved');
});
