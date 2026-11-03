import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import ts from 'typescript';
const source = readFileSync(new URL('../lib/tutor-session-context.ts', import.meta.url), 'utf8');
const compiled = ts.transpileModule(source, {compilerOptions: {module: ts.ModuleKind.ESNext}}).outputText;
const { tutorLearningContextChanged: changed } = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString('base64')}`);
const original = {sessionRef:'chemistry-session', status:'active', activeTopic:{topicRef:'chemistry-topic'}, currentTutor:{profileRef:'old'}};
test('new subject sessions cannot retain an old paper, practice or message draft', () => {
  assert.equal(changed(original, {...original,sessionRef:'biology-session',activeTopic:{topicRef:'biology-topic'}}),true);
  assert.equal(changed(null,original),true);
});
test('ending or switching topics invalidates question-specific UI state', () => {
  assert.equal(changed(original,{...original,status:'ended'}),true);
  assert.equal(changed(original,{...original,activeTopic:{topicRef:'different-topic'}}),true);
});
test('switching tutors or refreshing the same context preserves the current question', () => {
  assert.equal(changed(original,{...original,currentTutor:{profileRef:'new'}}),false);
  assert.equal(changed(original,structuredClone(original)),false);
});
