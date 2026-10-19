import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import ts from 'typescript';
import { renderToStaticMarkup } from 'react-dom/server';
import { createElement } from 'react';
const read = (path) => readFileSync(new URL(path, import.meta.url), 'utf8');
const catalogue = JSON.parse(read('../lib/avatar-catalogue.json'));
const compile = (source) =>
  ts.transpileModule(source, {
    compilerOptions: {
      target: ts.ScriptTarget.ES2022,
      module: ts.ModuleKind.ES2022,
      jsx: ts.JsxEmit.ReactJSX,
    },
  }).outputText;
const url = (source) =>
  `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`;
const helperUrl = url(
  compile(read('../lib/student-avatar.ts')).replace(
    /import catalogue from ['"]\.\/avatar-catalogue.json['"];?/,
    `const catalogue=${JSON.stringify(catalogue)};`,
  ),
);
const { parseAvatar, avatarPresets, surpriseAvatar } = await import(helperUrl);
let renderer = compile(read('../components/portal/student-avatar.tsx')).replace(
  /['"]@\/lib\/student-avatar['"]/g,
  JSON.stringify(helperUrl),
);
for (const name of ['react', 'react/jsx-runtime'])
  renderer = renderer
    .replaceAll(JSON.stringify(name), JSON.stringify(import.meta.resolve(name)))
    .replaceAll(`'${name}'`, JSON.stringify(import.meta.resolve(name)));
const { StudentAvatar } = await import(url(renderer));
test('every supported feature renders with each starting character', () => {
  for (const preset of avatarPresets) {
    for (const [field, choices] of Object.entries(catalogue.options))
      for (const value of Object.keys(choices)) {
        const avatar = { ...preset, [field]: value };
        assert.ok(parseAvatar(avatar));
        const markup = renderToStaticMarkup(
          createElement(StudentAvatar, { avatar, label: 'My avatar' }),
        );
        assert.match(markup, /<svg/);
        assert.doesNotMatch(markup, /NaN|undefined|onload=/);
      }
  }
});
test('the four bases have distinct faces and valid random combinations', () => {
  assert.equal(new Set(avatarPresets.map((item) => item.face)).size, 4);
  for (let i = 0; i < 100; i++) assert.ok(parseAvatar(surpriseAvatar()));
});
test('unsupported, incomplete and injected avatar data fall back to initials', () => {
  for (const invalid of [
    null,
    {},
    { ...avatarPresets[0], version: 2 },
    { ...avatarPresets[0], skin: '<script>' },
    { ...avatarPresets[0], hair: 'toString' },
    { ...avatarPresets[0], studentId: 'someone-else' },
  ]) {
    assert.equal(parseAvatar(invalid), null);
    const markup = renderToStaticMarkup(
      createElement(StudentAvatar, { avatar: invalid, fallback: 'MP' }),
    );
    assert.doesNotMatch(markup, /<svg/);
    assert.match(markup, /MP/);
  }
});
test('avatar SVG IDs remain distinct when several avatars share a page', () => {
  const markup = renderToStaticMarkup(
    createElement(
      'div',
      null,
      ...avatarPresets.map((avatar, index) =>
        createElement(StudentAvatar, { avatar, key: index }),
      ),
    ),
  );
  const ids = [...markup.matchAll(/id="([^"]+)"/g)].map((match) => match[1]);
  assert.equal(ids.length, new Set(ids).size);
});
