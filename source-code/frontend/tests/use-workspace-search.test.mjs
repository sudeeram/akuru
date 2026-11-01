import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import ts from 'typescript';
const url = (source) =>
  `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`;
const compile = (source) =>
  ts.transpileModule(source, {
    compilerOptions: {
      target: ts.ScriptTarget.ES2022,
      module: ts.ModuleKind.ES2022,
    },
  }).outputText;
const routeUrl = url(
  compile(readFileSync(new URL('../lib/routes.ts', import.meta.url), 'utf8')),
);
const mockUrl = url(`
const search={record:'2',section:'c',page:'3',password:'discard'};
const router={state:{location:{pathname:'/admin/exam-documents/review/paper'}},navigate(value){calls.push(value);}};
export const calls=[];
export const useRouter=()=>router;
export const useRouterState=({select})=>select({location:{search,searchStr:'?record=%222%22&section=c&page=%223%22'}});
`);
const source = compile(
  readFileSync(
    new URL('../lib/use-workspace-search.ts', import.meta.url),
    'utf8',
  ),
)
  .replace(/(['"])@tanstack\/react-router\1/g, JSON.stringify(mockUrl))
  .replace(/(['"])\.\/routes\1/g, JSON.stringify(routeUrl));
const { useWorkspaceSearch } = await import(url(source));
const mock = await import(mockUrl);
test('workspace search consumes decoded numeric question/page references and preserves validated context on update', () => {
  const [values, update] = useWorkspaceSearch({
    record: '',
    section: '',
    page: '',
  });
  assert.deepEqual(values, { record: '2', section: 'c', page: '3' });
  update({ section: 'e' });
  const request = mock.calls.at(-1);
  assert.equal(request.replace, true);
  assert.deepEqual(
    request.search({
      record: '2',
      section: 'c',
      page: '3',
      password: 'secret',
    }),
    { record: '2', section: 'e', page: '3' },
  );
});
