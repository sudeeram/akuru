import assert from 'node:assert/strict';
import test from 'node:test';
import { flipbookSpread, nextFlipPage, previousFlipPage } from '../lib/flipbook.mjs';

test('desktop flipbook keeps a cover and stable two-page spreads', () => {
  assert.deepEqual(flipbookSpread(1, 10, true), { start: 1, left: null, right: 1 });
  assert.deepEqual(flipbookSpread(3, 10, true), { start: 2, left: 2, right: 3 });
  assert.deepEqual(flipbookSpread(10, 10, true), { start: 10, left: 10, right: null });
  assert.equal(nextFlipPage(1, 10, true), 2);
  assert.equal(nextFlipPage(3, 10, true), 4);
  assert.equal(nextFlipPage(10, 10, true), null);
  assert.equal(previousFlipPage(2, 10, true), 1);
  assert.equal(previousFlipPage(5, 10, true), 2);
});

test('phone flipbook turns one page and clamps invalid links', () => {
  assert.deepEqual(flipbookSpread(3, 10, false), { start: 3, left: 3, right: null });
  assert.deepEqual(flipbookSpread(99, 10, false), { start: 10, left: 10, right: null });
  assert.equal(nextFlipPage(3, 10, false), 4);
  assert.equal(previousFlipPage(1, 10, false), null);
});
