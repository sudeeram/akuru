/** @param {number} page @param {number} count @param {boolean} spread */
export function flipbookSpread(page, count, spread) {
  if (count < 1) return { start: 0, left: null, right: null };
  const current = Math.min(Math.max(Math.trunc(page) || 1, 1), count);
  if (!spread) return { start: current, left: current, right: null };
  if (current === 1) return { start: 1, left: null, right: 1 };
  const start = 2 + 2 * Math.floor((current - 2) / 2);
  return { start, left: start, right: start + 1 <= count ? start + 1 : null };
}

/** @param {number} page @param {number} count @param {boolean} spread */
export function nextFlipPage(page, count, spread) {
  const current = flipbookSpread(page, count, spread);
  const next = spread ? (current.start === 1 ? 2 : current.start + 2) : current.start + 1;
  return next <= count ? next : null;
}

/** @param {number} page @param {number} count @param {boolean} spread */
export function previousFlipPage(page, count, spread) {
  const current = flipbookSpread(page, count, spread);
  const previous = spread ? (current.start === 2 ? 1 : current.start - 2) : current.start - 1;
  return previous >= 1 ? previous : null;
}
