import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import ts from 'typescript';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
const url = (source) =>
  `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`;
const image = url(
  `import {createElement} from ${JSON.stringify(import.meta.resolve('react'))}; export default function Image({unoptimized,...props}) { return createElement('img', {...props,'data-direct-image':String(unoptimized)}); }`,
);
let source = ts.transpileModule(
  readFileSync(
    new URL('../features/tutor-chat-elements.tsx', import.meta.url),
    'utf8',
  ),
  {
    compilerOptions: {
      target: ts.ScriptTarget.ES2022,
      module: ts.ModuleKind.ES2022,
      jsx: ts.JsxEmit.ReactJSX,
    },
  },
).outputText;
for (const name of [
  'react',
  'react/jsx-runtime',
  'lucide-react',
  'next/image',
]) {
  const target = name === 'next/image' ? image : import.meta.resolve(name);
  source = source
    .replaceAll(JSON.stringify(name), JSON.stringify(target))
    .replaceAll(`'${name}'`, JSON.stringify(target));
}
const { TutorMessageContent, TutorTextbookEvidence, TutorChatAvatar } =
  await import(url(source));
const render = (Component, props) =>
  renderToStaticMarkup(createElement(Component, props));

test('tutor explanations render paragraphs, emphasis and lists without changing scientific notation', () => {
  const html = render(TutorMessageContent, {
    content:
      'Water is **H₂O**.\n\n1. Heat 5cm³ of water.\n2. Observe the change.\n\n- Keep the temperature at −7°C.\n- Record `0.0005g`.',
  });
  assert.match(html, /<strong>H₂O<\/strong>/);
  assert.match(html, /<ol start="1">/);
  assert.equal((html.match(/<li>/g) || []).length, 4);
  assert.match(html, /<code>0\.0005g<\/code>/);
  assert.match(html, /5cm³/);
  assert.match(html, /−7°C/);
});
test('model and student text cannot inject HTML, scripts or clickable model URLs', () => {
  for (const formatted of [true, false]) {
    const html = render(TutorMessageContent, {
      formatted,
      content:
        '<script>alert(1)</script>\n[Click](javascript:alert(1))\n<img src=x onerror=alert(1)>',
    });
    assert.doesNotMatch(html, /<script|<img|<a\b/);
    assert.match(html, /&lt;script&gt;/);
  }
  assert.match(
    render(TutorMessageContent, {
      formatted: false,
      content: '**my question**',
    }),
    /\*\*my question\*\*/,
  );
});
test('textbook evidence is closed initially and absent when no evidence exists', () => {
  const children = createElement(
    'a',
    { href: '/api/v1/private-source' },
    'Source page',
  );
  const html = render(TutorTextbookEvidence, {
    sourceCount: 2,
    visualCount: 1,
    children,
  });
  assert.match(html, /<details class="tutor-textbook-evidence">/);
  assert.doesNotMatch(html, /<details[^>]*\bopen/);
  assert.match(html, /2 sources · 1 visual aid/);
  assert.match(html, /<summary>/);
  assert.match(html, /Source page/);
  assert.equal(
    render(TutorTextbookEvidence, { sourceCount: 0, visualCount: 0, children }),
    '',
  );
});
test('tutor avatars use direct static images and supply a default when no preset is available', () => {
  const html = render(TutorChatAvatar, {
    name: 'Chemistry',
    src: '/akuru-bots/akuru-bot-celebrate.png',
  });
  assert.match(html, /data-direct-image="true"/);
  assert.match(html, /src="\/akuru-bots\/akuru-bot-celebrate.png\?v=/);
  assert.doesNotMatch(html, /_next\/image/);
  assert.match(
    render(TutorChatAvatar, { name: 'Tutor' }),
    /src="\/akuru-bots\/akuru-bot-say.png\?v=/,
  );
});

const scrollSource = ts.transpileModule(
  readFileSync(new URL('../lib/tutor-chat-scroll.ts', import.meta.url), 'utf8'),
  {
    compilerOptions: {
      target: ts.ScriptTarget.ES2022,
      module: ts.ModuleKind.ES2022,
    },
  },
).outputText;
const { scrollTutorTurnIntoView } = await import(url(scrollSource));
test('nested conversation scrolling positions the answer without competing smooth animations', () => {
  const calls = [];
  const list = {
    scrollTop: 300,
    getBoundingClientRect: () => ({ top: 100 }),
    scrollTo: (options) => calls.push(['inner', options]),
    scrollIntoView: (options) => calls.push(['outer', options]),
  };
  const turn = {
    closest: () => list,
    getBoundingClientRect: () => ({ top: 500 }),
  };
  scrollTutorTurnIntoView(turn, false);
  assert.deepEqual(calls, [
    ['inner', { top: 684, behavior: 'instant' }],
    ['outer', { block: 'nearest', behavior: 'smooth' }],
  ]);
  calls.length = 0;
  scrollTutorTurnIntoView(turn, true);
  assert.equal(calls[1][1].behavior, 'instant');
});

const reactURL = import.meta.resolve('react');
const cardStubs = {
  './drawing-submissions': url(
    'export function DrawingSubmissions(){return null;}',
  ),
  './answer-visuals': url('export function ModelAnswerVisuals(){return null;}'),
  './learning-media': url(
    `import {createElement as h} from ${JSON.stringify(reactURL)}; export function Equation({value}){return h('code',null,value);} export function LearningImage({src,description}){return h('img',{src,alt:description});}`,
  ),
  './tutor-chat-elements': url(source),
};
let cardSource = ts.transpileModule(
  readFileSync(
    new URL('../features/tutor-past-paper-card.tsx', import.meta.url),
    'utf8',
  ),
  {
    compilerOptions: {
      target: ts.ScriptTarget.ES2022,
      module: ts.ModuleKind.ES2022,
      jsx: ts.JsxEmit.ReactJSX,
    },
  },
).outputText;
for (const [name, target] of Object.entries({
  ...cardStubs,
  'react/jsx-runtime': import.meta.resolve('react/jsx-runtime'),
})) {
  cardSource = cardSource
    .replaceAll(JSON.stringify(name), JSON.stringify(target))
    .replaceAll(`'${name}'`, JSON.stringify(target));
}
const { TutorPastPaperCard } = await import(url(cardSource));
const practiceCard = {
  paperTitle: 'Chemistry 1C',
  questionLabel: '3(a)',
  state: 'awaiting_answer',
  answerRevealed: false,
  markingGuidance: [{ text: 'Secret scheme guidance' }],
  alternatives: [],
  examinerAdvice: [],
  sources: [
    {
      label: 'Paper · Page 6',
      url: '/api/v1/tutoring/sessions/test/past-paper/assets/source',
    },
  ],
  practice: {
    assessmentId: 'assessment-test',
    practiceRef: 'practice-test',
    topicTitle: 'Mixtures',
    assetUrls: ['/api/v1/private-diagram'],
    question: {
      id: 'question-test',
      marks: 2,
      prompt: 'Explain the start line.',
      sharedStem: 'The chromatogram shows the inks.',
      equations: ['H₂O'],
      assetIds: ['diagram'],
      assetDescriptions: { diagram: 'Start line and solvent front' },
      drawingParts: [],
      drawingFiles: {},
    },
  },
};
test('past-paper card shows exact shared context and accessible visuals without pre-answer guidance', () => {
  const html = render(TutorPastPaperCard, {
    value: practiceCard,
    busy: false,
    refresh: () => {},
  });
  assert.match(html, /Explain the start line/);
  assert.match(html, /The chromatogram shows the inks/);
  assert.match(html, /alt="Start line and solvent front"/);
  assert.match(html, /H₂O/);
  assert.doesNotMatch(html, /Secret scheme guidance|Approved marking guidance/);
  assert.match(html, /Paper · Page 6/);
  assert.match(html, /My answer:/);
});
test('past-paper feedback is labelled, folded and safely escaped after reveal', () => {
  const value = {
    ...practiceCard,
    state: 'revealed',
    answerRevealed: true,
    markingGuidance: [
      { text: 'Pencil is insoluble. <script>alert(1)</script>' },
    ],
  };
  const html = render(TutorPastPaperCard, {
    value,
    busy: false,
    refresh: () => {},
  });
  assert.match(html, /<summary>Approved marking guidance<\/summary>/);
  assert.doesNotMatch(html, /<script>|<details[^>]*\bopen/);
  assert.match(html, /&lt;script&gt;/);
  assert.match(html, /no independent mastery credit/);
});
