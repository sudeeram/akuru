import assert from 'node:assert/strict';
import test from 'node:test';
import { readableTextbookBlocks } from '../lib/textbook-display.mjs';

test('joins OCR line wraps while preserving headings, lists and paragraphs', () => {
  assert.deepEqual(readableTextbookBlocks(
    '2 ELEMENTS, COMPOUNDS AND MIXTURES\nThe air\nthat we breathe is a mixture.\n\n'
    + 'LEARNING OBJECTIVES\n• Understand elements\n• Understand a mixture that may\n'
    + 'melt over a range.\n\nREMINDER\nRead Chapter 3.\nNext sentence.'
  ), [
    { kind: 'heading', text: '2 ELEMENTS, COMPOUNDS AND MIXTURES' },
    { kind: 'paragraph', text: 'The air that we breathe is a mixture.' },
    { kind: 'heading', text: 'LEARNING OBJECTIVES' },
    { kind: 'list', items: ['Understand elements', 'Understand a mixture that may melt over a range.'] },
    { kind: 'heading', text: 'REMINDER' },
    { kind: 'paragraph', text: 'Read Chapter 3. Next sentence.' },
  ]);
});

test('keeps captions and scientific notation intact', () => {
  assert.deepEqual(readableTextbookBlocks('Figure 2.1 Gold is an element, but the\nring is a mixture.\n\nH₂O has a mass of 0.01g.'), [
    { kind: 'paragraph', text: 'Figure 2.1 Gold is an element, but the ring is a mixture.' },
    { kind: 'paragraph', text: 'H₂O has a mass of 0.01g.' },
  ]);
});
