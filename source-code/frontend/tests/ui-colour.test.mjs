import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import ts from 'typescript';
const css = readFileSync(
  new URL('../app/ui-adoption.css', import.meta.url),
  'utf8',
);
const source = readFileSync(
  new URL('../lib/subject-accent.ts', import.meta.url),
  'utf8',
);
const { outputText } = ts.transpileModule(source, {
  compilerOptions: {
    target: ts.ScriptTarget.ES2022,
    module: ts.ModuleKind.ES2022,
  },
});
const { subjectAccent } = await import(
  `data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`
);
const luminance = (hex) => {
  const rgb = hex
    .match(/[a-f0-9]{2}/g)
    .map((c) => parseInt(c, 16) / 255)
    .map((c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return rgb[0] * 0.2126 + rgb[1] * 0.7152 + rgb[2] * 0.0722;
};
test('decorative accent text meets AA on its soft surface and white', () => {
  for (const tone of ['blue', 'teal', 'violet', 'amber', 'coral', 'neutral']) {
    const foreground = css.match(
      new RegExp(`--ak-accent-${tone}: (#\\w{6})`),
    )[1];
    const background = css.match(new RegExp(`--ak-soft-${tone}: (#\\w{6})`))[1];
    for (const surface of [background, '#ffffff']) {
      const ratio =
        (luminance(surface) + 0.05) / (luminance(foreground) + 0.05);
      assert.ok(
        ratio >= 4.5,
        `${tone} contrast ${ratio.toFixed(2)} on ${surface}`,
      );
    }
  }
});
test('subject accents remain stable by identifier with safe neutral fallback', () => {
  assert.equal(subjectAccent('chemistry'), 'violet');
  assert.equal(subjectAccent('maths'), 'blue');
  for (const id of [
    undefined,
    '',
    'unknown-course',
    '__proto__',
    'constructor',
  ])
    assert.equal(subjectAccent(id), 'neutral');
});
