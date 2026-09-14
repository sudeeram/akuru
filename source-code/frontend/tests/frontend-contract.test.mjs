import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const api = readFileSync(new URL('../lib/api.ts', import.meta.url), 'utf8');
const page = readFileSync(new URL('../app/page.tsx', import.meta.url), 'utf8');
const admin = readFileSync(
  new URL('../features/admin.tsx', import.meta.url),
  'utf8',
);
const student = readFileSync(new URL('../features/student.tsx', import.meta.url), 'utf8');
const vite = readFileSync(
  new URL('../vite.config.ts', import.meta.url),
  'utf8',
);
const uiFeatures = readFileSync(
  new URL('../app/ui-features/page.tsx', import.meta.url),
  'utf8',
);
const layout = readFileSync(
  new URL('../app/layout.tsx', import.meta.url),
  'utf8',
);
const routeLoader = readFileSync(
  new URL('../components/route-loading-overlay.tsx', import.meta.url),
  'utf8',
);
const styles = readFileSync(
  new URL('../app/globals.css', import.meta.url),
  'utf8',
);

test('frontend uses the FastAPI v1 boundary and local proxy', () => {
  assert.match(api, /fetch\('\/api\/v1\/' \+ path/);
  assert.match(vite, /'\/api\/v1'/);
  assert.match(vite, /127\.0\.0\.1:8000/);
});

test('account UUIDs remain internal identifiers', () => {
  assert.doesNotMatch(admin, /label: `\$\{a\.name\} \(\$\{a\.id\}\)`/);
  assert.doesNotMatch(admin, /\{s\.id\} · Parent: \{s\.parentId\}/);
  assert.match(admin, /@\{s\.username\}/);
  assert.match(admin, /@\{a\.username\}/);
});

test('frontend contains no bundled mock credentials', () => {
  assert.doesNotMatch(page, /Local demo accounts/);
  assert.doesNotMatch(page, /demo-accounts/);
  assert.doesNotMatch(vite, /local-server/);
});

test('login submits from the keyboard', () => {
  assert.match(page, /submitLoginOnEnter/);
  assert.match(page, /e\.key !== 'Enter'/);
  assert.match(page, /e\.currentTarget\.form\?\.requestSubmit\(\)/);
  assert.equal((page.match(/onKeyDown=\{submitLoginOnEnter\}/g) ?? []).length, 2);
});

test('admin UI reference is routed and API-authorized', () => {
  assert.match(page, /href="\/ui-features"/);
  assert.match(uiFeatures, /api\('admin\/ui-features'\)/);
  assert.match(uiFeatures, /Admin access required/);
  assert.match(uiFeatures, /AKURU-owned components/);
  assert.match(uiFeatures, /UI feature categories/);
  assert.match(uiFeatures, /Workflow board/);
  assert.match(uiFeatures, /Charts and trends/);
  assert.match(uiFeatures, /Access and communication/);
});

test('page transitions rotate through AKURU BOT loading scenes', () => {
  assert.match(layout, /RouteLoadingOverlay/);
  assert.equal(
    (routeLoader.match(/\/akuru-loading\/akuru-loading-/g) ?? []).length,
    5,
  );
  assert.match(routeLoader, /route-loader/);
  assert.match(routeLoader, /hashchange/);
  assert.match(styles, /prefers-reduced-motion/);
});

test('all portal roles receive horizontally scrollable navigation', () => {
  assert.match(page, /portal-horizontal-nav/);
  assert.match(page, /aria-current=\{view === id \? 'page'/);
  assert.match(page, /nav\.map\(\(\[id, label, Icon\]\)/);
  assert.match(styles, /overflow-x: auto/);
  assert.match(styles, /-webkit-overflow-scrolling: touch/);
  assert.doesNotMatch(page, /SidebarProvider|PortalNavigation|app-sidebar/);
});

test('admin review displays deterministic extraction evidence', () => {
  assert.match(api, /getDocumentExtraction/);
  assert.match(api, /documents\/\$\{id\}\/extraction/);
  assert.match(admin, /Extracted page \{page\.pageNumber\}/);
  assert.match(admin, /review required/);
  assert.match(admin, /renderAssetId/);
  assert.match(admin, /block\.latex/);
  assert.match(admin, /block\.sourceAssetId/);
  assert.match(admin, /Retry processing/);
  assert.match(admin, /removeDocument/);
  assert.doesNotMatch(admin, /api\('documents\/review'/);
  assert.match(admin, /Its write API is not implemented yet/);
});

test('admin manages OpenAI aliases and priorities without receiving keys', () => {
  assert.match(page, /OpenAI accounts/);
  assert.match(admin, /admin\/ai-accounts/);
  assert.match(admin, /Priorities must be unique/);
  assert.match(admin, /Credential configured/);
  assert.doesNotMatch(admin, /openai_account_keys|API_KEY|sk-/);
});

test('admin reviews and publishes versioned textbook units from source evidence', () => {
  assert.match(api, /getTextbookReview/);
  assert.match(api, /proposeTextbookReview/);
  assert.match(api, /publishTextbookReview/);
  assert.match(admin, /Reviewed textbook units/);
  assert.match(admin, /Propose units/);
  assert.match(admin, /'sections', 'definitions', 'concepts', 'equations', 'examples', 'diagrams'/);
  assert.match(admin, /Publish reviewed units/);
});

test('admin edits and publishes cumulative curriculum coverage', () => {
  assert.match(api, /getCurriculumPlan/);
  assert.match(api, /saveCurriculumPlan/);
  assert.match(api, /publishCurriculumPlan/);
  assert.match(admin, /Cumulative coverage/);
  assert.match(admin, /Grade 10 Term1 and Term2/);
});

test('admin reviews and publishes complete official assessment material', () => {
  assert.match(api, /proposeOfficialMaterialReview/);
  assert.match(api, /saveOfficialMaterialReview/);
  assert.match(api, /publishOfficialMaterialReview/);
  assert.match(admin, /Official material review/);
  assert.match(admin, /Expected complete item count/);
  assert.match(admin, /Marking points · one per line/);
  assert.match(admin, /Common mistakes · one per line/);
  assert.match(admin, /Publish official material/);
});

test('admin confirms weighted question mappings from constrained suggestions', () => {
  assert.match(api, /getPaperMappings/);
  assert.match(api, /suggestQuestionMappings/);
  assert.match(api, /saveQuestionMappings/);
  assert.match(api, /publishQuestionMappings/);
  assert.match(admin, /Total weight:/);
  assert.match(admin, /Suggest mappings/);
  assert.match(admin, /Confirm mapping/);
  assert.doesNotMatch(admin, /api\('admin\/questions'/);
});

test('student assessment UI uses immutable FastAPI assessment sessions', () => {
  assert.match(student, /assessments\/start/);
  assert.match(student, /assessments\/\$\{exam\.id\}\/answers/);
  assert.match(student, /assessments\/\$\{exam\.id\}\/submit/);
  assert.match(student, /mode: 'official_paper'/);
  assert.match(admin, /assessments\/admin\/blueprints/);
  assert.match(page, /Mock blueprints/);
  assert.doesNotMatch(student, /api\('exams\/start'/);
});

test('student submissions request traceable AKURU assessment feedback', () => {
  assert.match(student, /assessments\/\$\{practice\.id\}\/evaluate/);
  assert.match(student, /assessments\/\$\{exam\.id\}\/evaluate/);
  assert.match(student, /feedback\?\.markingDecisions/);
  assert.match(student, /feedback\?\.teachingExplanation/);
  assert.match(student, /feedback\?\.status === 'published'/);
  assert.match(api, /type AssessmentResult/);
  assert.match(api, /studentEvidence: string/);
});

test('progress uses backend-calculated explainable unit mastery', () => {
  assert.match(api, /type UnitMastery/);
  assert.match(api, /preciseScore: number/);
  assert.match(api, /confidence: 'low' \| 'medium' \| 'high'/);
  assert.match(api, /mastery: Record<string, UnitMastery\[\]>/);
  assert.match(student, /unit\.score\.toFixed\(1\)\}\/10/);
  assert.match(student, /unit\.provisional \? 'Provisional' : unit\.confidence/);
  assert.match(student, /evidenceCount/);
  assert.match(student, /unit\.trend/);
  assert.match(student, /questions\/\$\{q\.id\}\/hint/);
});

test('frontend presents source-linked improvement recommendations for review', () => {
  assert.match(api, /type ImprovementRecommendation/);
  assert.match(api, /recommendations: Record<string, ImprovementRecommendation\[\]>/);
  assert.match(student, /AKURU next steps/);
  assert.match(student, /successCondition/);
  assert.match(student, /sourceUrl/);
  assert.match(student, /reviewStatus === 'approved'/);
  assert.match(readFileSync(new URL('../features/parent.tsx', import.meta.url), 'utf8'), /recommendations\/\$\{id\}\/review/);
});

test('handwritten working uses the private authenticated assessment endpoint', () => {
  assert.match(api, /export async function uploadWorking/);
  assert.match(api, /questions\/\$\{questionId\}\/working/);
  assert.match(api, /'X-Filename': file\.name/);
  assert.match(api, /'X-CSRF-Token'/);
  assert.match(student, /uploadWorking\(f, practice\.id, q\.id\)/);
  assert.match(student, /uploadWorking\(f, exam\.id, q\.id\)/);
  assert.doesNotMatch(api, /readAsDataURL/);
  assert.doesNotMatch(student, /'\/api\/files\/' \+ chosen\.fileId/);
});
