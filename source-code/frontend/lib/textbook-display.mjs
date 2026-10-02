const BULLET = /^(?:[•●▪◦]|[-–—]\s|\(?\d+[.)]\s|\(?[a-z][.)]\s|o\s)/i;

/** @typedef {{kind: 'heading' | 'paragraph', text: string} | {kind: 'list', items: string[]}} TextbookDisplayBlock */

function isHeading(line) {
  return line.length <= 90 && /[A-Z]{3}/.test(line) && line === line.toUpperCase()
    && !/[.!?;:]$/.test(line);
}

/** Turn OCR's line wraps into readable blocks without changing saved textbook evidence.
 * @param {string} text
 * @returns {TextbookDisplayBlock[]}
 */
export function readableTextbookBlocks(text) {
  /** @type {TextbookDisplayBlock[]} */
  const blocks = [];
  let prose = '';
  /** @type {string[]} */
  let items = [];
  const flushProse = () => {
    if (prose) blocks.push({ kind: 'paragraph', text: prose });
    prose = '';
  };
  const flushItems = () => {
    if (items.length) blocks.push({ kind: 'list', items });
    items = [];
  };
  for (const raw of text.replace(/\r\n?/g, '\n').split('\n')) {
    const line = raw.trim();
    if (!line) { flushProse(); flushItems(); continue; }
    if (isHeading(line)) {
      flushProse(); flushItems(); blocks.push({ kind: 'heading', text: line });
    } else if (BULLET.test(line)) {
      flushProse();
      items.push(line.replace(BULLET, '').trim());
    } else if (items.length) {
      items[items.length - 1] += ` ${line}`;
    } else {
      prose += `${prose ? ' ' : ''}${line}`;
    }
  }
  flushProse(); flushItems();
  return blocks;
}
