import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import test from 'node:test';

const apiFiles = [
  '../api/core/client.ts',
  '../api/core/errors.ts',
  '../api/core/csrf.ts',
  '../api/state/state.api.ts',
  '../api/state/state.types.ts',
  '../api/tutoring/tutor.api.ts',
  '../api/tutoring/tutor.types.ts',
  '../api/documents/documents.api.ts',
  '../api/documents/documents.types.ts',
  '../api/textbooks/textbooks.api.ts',
  '../api/textbooks/textbooks.types.ts',
  '../api/curriculum/curriculum.api.ts',
  '../api/curriculum/curriculum.types.ts',
  '../api/assessments/assessments.api.ts',
  '../api/assessments/assessments.types.ts',
  '../api/flashcards/flashcards.api.ts',
  '../api/flashcards/flashcards.types.ts',
  '../api/mastery/mastery.types.ts',
];
const api = apiFiles
  .map((path) => readFileSync(new URL(path, import.meta.url), 'utf8'))
  .join('\n');
const apiClient = readFileSync(new URL('../api/core/client.ts', import.meta.url), 'utf8');
const documentApi = readFileSync(new URL('../api/documents/documents.api.ts', import.meta.url), 'utf8');
const textbookApiClient = readFileSync(new URL('../api/textbooks/textbooks.api.ts', import.meta.url), 'utf8');
const page = readFileSync(new URL('../app/page.tsx', import.meta.url), 'utf8');
const tutorSessions = readFileSync(new URL('../features/tutor-sessions.tsx', import.meta.url), 'utf8');
const learningMedia = readFileSync(new URL('../features/learning-media.tsx', import.meta.url), 'utf8');
const admin = readFileSync(
  new URL('../features/admin.tsx', import.meta.url),
  'utf8',
);
const textbookStructure = readFileSync(new URL('../features/textbook-structure.tsx', import.meta.url), 'utf8');
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
const tutorProfiles = readFileSync(
  new URL('../features/tutor-profiles.tsx', import.meta.url),
  'utf8',
);
const tutorSignals = readFileSync(new URL('../features/tutor-signals.tsx', import.meta.url), 'utf8');
const tutorHistory = readFileSync(new URL('../features/tutor-history.tsx', import.meta.url), 'utf8');
const tutorVoice = readFileSync(new URL('../features/tutor-voice.tsx', import.meta.url), 'utf8');
const flashcards = readFileSync(new URL('../features/flashcards.tsx', import.meta.url), 'utf8');

test('frontend uses the FastAPI v1 boundary and local proxy', () => {
  assert.match(api, /fetch\(`\/api\/v1\/\$\{path\}`/);
  assert.match(vite, /'\/api\/v1'/);
  assert.match(vite, /127\.0\.0\.1:8000/);
});

test('frontend API is split by domain behind one typed public barrel', () => {
  assert.equal(existsSync(new URL('../lib/api.ts', import.meta.url)), false);
  assert.match(apiClient, /function request<T>/);
  assert.doesNotMatch(api, /type ApiResult/);
  assert.match(page, /from '@\/api'/);
  assert.match(documentApi, /body: file/);
  assert.doesNotMatch(documentApi, /contentBase64/);
  assert.match(textbookApiClient, /contentBase64/);
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
  assert.match(uiFeatures, /getUiFeaturesAccess\(\)/);
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
  assert.match(admin, /Review required/);
  assert.match(admin, /Extraction review progress/);
  assert.match(admin, /Pages to review/);
  assert.match(admin, /Blocks to review/);
  assert.match(admin, /extraction-page-\$\{page\.pageNumber\}/);
  assert.match(admin, /review-status-required/);
  assert.match(admin, /review-status-complete/);
  assert.match(admin, /Partially reviewed/);
  assert.match(admin, /Yet to be reviewed/);
  assert.match(admin, /Fully reviewed/);
  assert.match(admin, /Hide reviewed blocks/);
  assert.match(admin, /Show reviewed blocks/);
  assert.match(admin, /<details className="panel extraction-page-review"/);
  assert.match(admin, /extraction-page-review-counts/);
  assert.match(styles, /\.review-status-required/);
  assert.match(styles, /\.review-status-partial/);
  assert.match(styles, /\.review-status-complete/);
  assert.match(styles, /\.extraction-review-summary\s*\{[^}]*position:\s*static/s);
  assert.match(admin, /renderAssetId/);
  assert.match(admin, /block\.latex/);
  assert.match(admin, /block\.sourceAssetId/);
  assert.match(admin, /Retry processing/);
  assert.match(admin, /removeDocument/);
  assert.doesNotMatch(admin, /api\('documents\/review'/);
  assert.match(admin, /TextbookStructureAdmin/);
});

test('admin manages versioned Unit or Module textbook structures with public references', () => {
  assert.match(api, /admin\/textbooks/);
  assert.match(api, /textbookRef/);
  assert.match(api, /groupRef/);
  assert.match(api, /topicRef/);
  assert.match(textbookStructure, /Structure label/);
  assert.match(textbookStructure, /Publish structure/);
  assert.match(textbookStructure, /reorderTextbookGroups/);
  assert.match(textbookStructure, /reorderTextbookTopics/);
  assert.match(textbookStructure, /Published or referenced topics are protected/);
  assert.doesNotMatch(textbookStructure, /book\.id|group\.id|topic\.id|UUID/);
});

test('admin attaches scanned textbook parts to a topic and reviews extraction evidence', () => {
  assert.match(api, /uploadTopicPart/);
  assert.match(api, /uploadTopicPartsBatch/);
  assert.match(api, /suggestTopicParts/);
  assert.match(textbookStructure, /Upload scanned textbook part PDFs or images/);
  assert.match(textbookStructure, /filename check suggests a different topic/);
  assert.match(admin, /Original page/);
  assert.match(admin, /Normalized review page/);
  assert.match(admin, /Printed page label/);
  assert.match(admin, /Save reviewed block/);
  assert.match(api, /updateExtractionBlock/);
  assert.match(api, /updateExtractionPage/);
});

test('admin publishes reviewed topics independently with readiness and version history', () => {
  assert.match(api, /publishTextbookTopic/);
  assert.match(textbookStructure, /Publication readiness/);
  assert.match(textbookStructure, /Publish topic content/);
  assert.match(textbookStructure, /topics published/);
  assert.match(textbookStructure, /superseded version/);
  assert.match(textbookStructure, /Existing citations keep their current version/);
});

test('admin builds incremental versioned topic coverage without exposing internal ids', () => {
  assert.match(api, /createCurriculumPlanDraft/);
  assert.match(api, /confirmPublishedChanges/);
  assert.match(admin, /Add topics covered now/);
  assert.match(admin, /Cumulative coverage preview/);
  assert.match(admin, /requiresPublishedChangeConfirmation/);
  assert.match(admin, /Existing assessments retain their original snapshot/);
});

test('admin manages OpenAI aliases and priorities without receiving keys', () => {
  assert.match(page, /OpenAI accounts/);
  assert.match(admin, /admin\/ai-accounts/);
  assert.match(admin, /Priorities must be unique/);
  assert.match(admin, /Credential configured/);
  assert.doesNotMatch(admin, /openai_account_keys|API_KEY|sk-/);
});

test('admin uses the topic-based textbook workflow', () => {
  assert.match(admin, /Topic-based textbook workflow/);
  assert.match(admin, /Attach each scanned PDF or image directly to its topic/);
  assert.doesNotMatch(api, /textbook-review/);
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
  assert.match(api, /topic-mapping/);
  assert.match(admin, /mark the topics that every student must have covered/);
  assert.match(admin, /Extracted evidence/);
  assert.match(admin, /Group summary/);
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

test('progress uses backend-calculated explainable topic mastery', () => {
  assert.match(api, /type TopicMastery/);
  assert.match(api, /preciseScore: number/);
  assert.match(api, /confidence: 'low' \| 'medium' \| 'high'/);
  assert.match(api, /mastery: Record<string, TopicMastery\[\]>/);
  assert.match(student, /topic\.score\.toFixed\(1\)\}\/10/);
  assert.match(student, /topic\.provisional \? 'Provisional' : topic\.confidence/);
  assert.match(student, /evidenceCount/);
  assert.match(student, /topic\.trend/);
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

test('study planner uses persisted adaptive plans and completion APIs', () => {
  assert.match(student, /api\('plans', \{ studentId: p\.child\.id \}\)/);
  assert.match(student, /plans\/items\/\$\{item\.id\}\/complete/);
  assert.match(student, /item\.sourceUrl/);
  assert.match(student, /item\.successCondition/);
  assert.match(student, /item\.scheduledFor/);
  assert.match(api, /generationReason/);
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

test('role-specific experiences expose evidence, trends, review tasks and audit controls', () => {
  const parent = readFileSync(new URL('../features/parent.tsx', import.meta.url), 'utf8');
  const admin = readFileSync(new URL('../features/admin.tsx', import.meta.url), 'utf8');
  const diagram = readFileSync(new URL('../features/diagram.tsx', import.meta.url), 'utf8');
  assert.match(student, /How each mark was decided/);
  assert.match(student, /studentEvidence/);
  assert.match(student, /mastery-dimensions/);
  assert.match(student, /Mistake pattern/);
  assert.match(parent, /Child-by-child learning summary/);
  assert.match(parent, /Latest 10 score changes/);
  assert.match(api, /assessments\/admin\/audit/);
  assert.match(admin, /Reassess and create new version/);
  assert.match(admin, /extraction-review-grid/);
  assert.match(diagram, /Enlarge diagram/);
  assert.match(student, /<Equation key={equation}/);
});

test('visual media is source-grounded, private until reviewed, and learner scoped', () => {
  const admin = readFileSync(new URL('../features/media-admin.tsx', import.meta.url), 'utf8');
  const gallery = readFileSync(new URL('../features/media-gallery.tsx', import.meta.url), 'utf8');
  assert.match(admin, /media\/admin\/deterministic/);
  assert.match(admin, /media\/admin\/illustrations/);
  assert.match(admin, /Publish illustration/);
  assert.match(admin, /sourceManifest/);
  assert.match(gallery, /studentId=/);
  assert.match(gallery, /Supporting visual\. Official source evidence/);
  assert.doesNotMatch(gallery, /item\.prompt/);
});

test('admin evaluation gates require reviewed corpora and passing releases', () => {
  const evaluation = readFileSync(new URL('../features/evaluation-admin.tsx', import.meta.url), 'utf8');
  assert.match(page, /Evaluation gates/);
  assert.match(admin, /EvaluationAdmin/);
  assert.match(evaluation, /missingApprovedSubjects/);
  assert.match(evaluation, /evaluations\/admin\/corpora/);
  assert.match(evaluation, /evaluations\/admin\/runs/);
  assert.match(evaluation, /Activate automatic feedback/);
  assert.match(evaluation, /Tutor subjects awaiting approval/);
  assert.match(evaluation, /Production-like staging/);
  assert.match(evaluation, /Admin testing/);
  assert.match(evaluation, /Parent pilot/);
  assert.match(evaluation, /Eligible students/);
  assert.match(evaluation, /Tutor feature kill switch applied/);
  assert.match(evaluation, /prompt-injection-rejected/);
  assert.match(evaluation, /no-cross-student-context/);
  assert.match(evaluation, /french-voice/);
});

test('admin operations exposes alerts, usage and audit without secrets', () => {
  const operations = readFileSync(new URL('../features/operations-admin.tsx', import.meta.url), 'utf8');
  assert.match(page, /Security & operations|Operations/);
  assert.match(admin, /OperationsAdmin/);
  assert.match(operations, /operations\/admin\/status/);
  assert.match(operations, /Provider tokens/);
  assert.match(operations, /Recent security and content audit/);
  assert.doesNotMatch(operations, /OPENAI_API_KEY|DATABASE_PASSWORD/);
});

test('role-scoped tutor profiles use curated AKURU heroes and immutable API versions', () => {
  assert.match(page, /My tutors/);
  assert.match(page, /Tutor presets/);
  assert.match(api, /getTutorProfiles/);
  assert.match(api, /saveTutorProfile/);
  assert.match(api, /deleteTutorProfile/);
  assert.match(tutorProfiles, /switching|multiple tutor|more than one tutor/i);
  assert.match(tutorProfiles, /Save new version/);
  assert.match(tutorProfiles, /Child-safe AKURU hero|CURATED AKURU BOT/i);
  assert.match(tutorProfiles, /getTutorAdminPresets/);
  assert.doesNotMatch(tutorProfiles, /providerVoice|provider_voice|generated avatar/i);
  assert.doesNotMatch(tutorProfiles, />\{item\.id\}</);
});

test('student tutor room retains transcripts and supports explicit tutor and topic switches', () => {
  assert.match(page, /Tutor room/);
  assert.match(tutorSessions, /getTutorSessionOptions/);
  assert.match(tutorSessions, /switchTutorProfile/);
  assert.match(tutorSessions, /switchTutorTopic/);
  assert.match(tutorSessions, /CONTINUOUS HANDOVER/);
  assert.match(tutorSessions, /profileVersion/);
  assert.match(api, /requestKey/);
  assert.doesNotMatch(tutorSessions, /MediaRecorder|audioBlob|raw audio/i);
});

test('next-topic advice is evidence based and requires an explicit student move', () => {
  assert.match(api, /getNextTutorTopic/);
  assert.match(tutorSessions, /What should I improve next/);
  assert.match(tutorSessions, /Find next topic/);
  assert.match(tutorSessions, /Move to this topic/);
  assert.match(tutorSessions, /switchTutorTopic/);
});

test('tutor textbook sources expose exact authorized citations and nearby context', () => {
  assert.match(api, /searchTutorSources/);
  assert.match(api, /getTutorCitationContext/);
  assert.match(api, /pdfPageIndex/);
  assert.match(api, /printedPageLabel/);
  assert.match(tutorSessions, /APPROVED TEXTBOOK/);
  assert.match(tutorSessions, /pageReference/);
  assert.match(tutorSessions, /Open cited page or crop/);
  assert.match(tutorSessions, /Show nearby context/);
  assert.match(tutorSessions, /only when it finds an authorized passage/);
});

test('structured text tutor supports teaching modes, evidence and recoverable keyboard input', () => {
  assert.match(api, /addTutorAgentTurn/);
  assert.match(api, /agent-turns/);
  assert.match(api, /TutorAgentReply/);
  assert.match(tutorSessions, /Teaching approach/);
  assert.match(tutorSessions, /Socratic practice/);
  assert.match(tutorSessions, /French conversation/);
  assert.match(tutorSessions, /Evidence used by tutor/);
  assert.match(tutorSessions, /followUpChoices/);
  assert.match(tutorSessions, /setMessage\(''\)/);
  assert.match(tutorSessions, /<form className="tutor-composer" onSubmit=/);
  assert.match(tutorSessions, /Proposed tutor observations do not change mastery/);
});

test('guided tutor practice uses authoritative assessment feedback and bounded observations', () => {
  const parent = readFileSync(new URL('../features/parent.tsx', import.meta.url), 'utf8');
  assert.match(api, /startTutorPractice/);
  assert.match(api, /getTutorPracticeHint/);
  assert.match(api, /saveTutorPracticeAnswer/);
  assert.match(api, /submitTutorPractice/);
  assert.match(tutorSessions, /Practise one eligible question/);
  assert.match(tutorSessions, /Submit for assessment/);
  assert.match(tutorSessions, /How each mark was decided/);
  assert.match(tutorSessions, /Improved answer/);
  assert.match(tutorSessions, /Submit it before moving to another topic/);
  assert.match(tutorSignals, /NON-AUTHORITATIVE/);
  assert.match(tutorSignals, /does not change mastery or study plans/);
  assert.match(parent, /TutorSignals studentId=\{child\.id\}/);
});

test('per-child tutor allowances are visible and Admin controlled without UUIDs or provider secrets', () => {
  const quotas = readFileSync(new URL('../features/tutor-quotas.tsx', import.meta.url), 'utf8');
  assert.match(api, /getTutorQuota/);
  assert.match(api, /updateTutorAdminQuota/);
  assert.match(tutorSessions, /tutor requests remaining/);
  assert.match(quotas, /Per-child tutor allowance/);
  assert.match(quotas, /Audit reason/);
  assert.match(quotas, /Voice minutes/);
  assert.doesNotMatch(quotas, /credentialAlias|provider secret|OpenAI key/i);
  assert.doesNotMatch(quotas, /\.id\b/);
});

test('tutor history gives parents summaries and Admins audited retention controls', () => {
  assert.match(page, /Tutor history/);
  assert.match(page, /<TutorHistory notify=\{notify\}/);
  assert.match(admin, /<TutorHistory admin notify=\{p\.notify\}/);
  assert.match(api, /tutoring\/history\/summaries/);
  assert.match(api, /tutoring\/history\/safety-events/);
  assert.match(api, /support-access/);
  assert.match(api, /purge-preview/);
  assert.match(tutorHistory, /Educational summaries protect the child/);
  assert.match(tutorHistory, /without repeating the child’s message/);
  assert.match(tutorHistory, /Audited support transcript/);
  assert.match(tutorHistory, /Confirm PURGE TRANSCRIPTS/);
  assert.doesNotMatch(tutorHistory, /studentId|parentId|sourceTurnId/);
});

test('realtime voice uses ephemeral WebRTC credentials, captions, recovery and accessible controls', () => {
  assert.match(api, /createRealtimeCredential/);
  assert.match(api, /saveRealtimeTranscriptTurn/);
  assert.match(tutorSessions, /<TutorVoice/);
  assert.match(tutorVoice, /new RTCPeerConnection/);
  assert.match(tutorVoice, /navigator\.mediaDevices\.getUserMedia/);
  assert.match(tutorVoice, /api\.openai\.com\/v1\/realtime\/calls/);
  assert.match(tutorVoice, /input_audio_transcription\.completed/);
  assert.match(tutorVoice, /output_audio_transcript\.delta/);
  assert.match(tutorVoice, /response\.cancel/);
  assert.match(tutorVoice, />Pause</);
  assert.match(tutorVoice, /'Unmute' : 'Mute'/);
  assert.match(tutorVoice, />Repeat</);
  assert.match(tutorVoice, />Slower</);
  assert.match(tutorVoice, /Use text instead/);
  assert.match(tutorVoice, /french_conversation/);
  assert.match(tutorVoice, /french_vocabulary/);
  assert.match(tutorVoice, /french_pronunciation/);
  assert.match(tutorVoice, /start\(credential\.connectionRef\)/);
  assert.doesNotMatch(tutorVoice, /MediaRecorder|Blob|indexedDB|localStorage/);
});

test('tutor visuals distinguish evidence from explanations and remain accessible', () => {
  assert.match(tutorSessions, /OFFICIAL SOURCE/);
  assert.match(tutorSessions, /EXPLANATORY AID/);
  assert.match(tutorSessions, /Text alternative:/);
  assert.match(tutorSessions, /does not replace the official source/);
  assert.match(tutorSessions, /<Equation value=\{visual\.equation\}/);
  assert.match(tutorSessions, /<LearningImage/);
  assert.match(tutorSessions, /Asset provenance/);
  assert.match(learningMedia, /Enlarge diagram/);
  assert.match(learningMedia, /Dialog open=\{open\}/);
  assert.match(learningMedia, /Open original size in a new tab/);
});

test('topic hierarchy workflow supports keyboard filters and accessible status cues', () => {
  assert.match(textbookStructure, /Find textbook content/);
  assert.match(textbookStructure, /Search textbook/);
  assert.match(textbookStructure, /Content status/);
  assert.match(textbookStructure, /aria-live="polite"/);
  assert.match(textbookStructure, /Move \$\{group\.code\} earlier/);
  assert.match(textbookStructure, /Move topic \$\{topic\.code\} earlier/);
  assert.match(textbookStructure, /Term coverage is managed/);
  assert.match(admin, /Term to review/);
  assert.match(page, /Skip to page content/);
  assert.match(page, /<main id="main-content"/);
  assert.match(styles, /\.skip-link/);
  assert.match(styles, /input:focus-visible/);
  assert.match(styles, /catalogue-filters/);
  assert.match(readFileSync(new URL('../features/shared.tsx', import.meta.url), 'utf8'), /aria-label=\{`Status: \$\{label\}`\}/);
});

test('topic PDFs have an Admin-only quality report and publication quality gate', () => {
  const backendQuality = readFileSync(new URL('../../backend/app/services/topic_quality.py', import.meta.url), 'utf8');
  const textbookApi = readFileSync(new URL('../../backend/app/api/v1/textbook_structures.py', import.meta.url), 'utf8');
  const textbookService = readFileSync(new URL('../../backend/app/services/textbook_structures.py', import.meta.url), 'utf8');
  assert.match(api, /getTopicQualityReport/);
  assert.match(textbookStructure, /View topic PDF quality report/);
  assert.match(textbookApi, /topics\/\{topic_ref\}\/quality/);
  assert.match(backendQuality, /pageCoverage/);
  assert.match(backendQuality, /ocrConfidence/);
  assert.match(backendQuality, /formulaReview/);
  assert.match(backendQuality, /diagramRetention/);
  assert.match(backendQuality, /printedPageAccuracy/);
  assert.match(backendQuality, /topicRetrievalPrecision/);
  assert.match(textbookService, /quality_gate/);
});

test('admin can designate canonical text and non-retrievable visual references', () => {
  const textbookService = readFileSync(new URL('../../backend/app/services/textbook_structures.py', import.meta.url), 'utf8');
  const documentsService = readFileSync(new URL('../../backend/app/services/documents.py', import.meta.url), 'utf8');
  assert.match(api, /getTopicSources/);
  assert.match(api, /updateTopicSourceRole/);
  assert.match(textbookStructure, /Manage topic sources/);
  assert.match(textbookStructure, /Visual reference/);
  assert.match(textbookStructure, /OCR text excluded from retrieval/);
  assert.match(textbookService, /TextbookTopicDocument\.role != "visual_reference"/);
  assert.match(documentsService, /version\.status = "completed" if complete else "needs_review"/);
  assert.match(documentsService, /document\.review_state = "reviewed" if complete else "pending"/);
});

test('admin sees group-level Topic 1 launch readiness without coupling later topics', () => {
  const textbookSchema = readFileSync(new URL('../../backend/app/schemas/textbook_structures.py', import.meta.url), 'utf8');
  const textbookService = readFileSync(new URL('../../backend/app/services/textbook_structures.py', import.meta.url), 'utf8');
  assert.match(textbookSchema, /totalTopicCount/);
  assert.match(textbookSchema, /reviewedTopicCount/);
  assert.match(textbookSchema, /publishedTopicCount/);
  assert.match(textbookSchema, /studentEligibleTopicCount/);
  assert.match(textbookService, /CurriculumPlan\.status == "published"/);
  assert.match(textbookStructure, /Total topics/);
  assert.match(textbookStructure, /Student eligible/);
  assert.match(textbookStructure, /does not change existing topic identities or published versions/);
  assert.match(textbookStructure, /Owned by iGCSE/);
  assert.match(api, /getTopicLaunchReadiness/);
  assert.match(textbookStructure, /View launch readiness/);
  assert.match(textbookStructure, /Detach from topic/);
  assert.match(textbookStructure, /Possible duplicate primary text/);
  assert.match(textbookStructure, /Apply recommended v2\.1 source roles/);
  assert.match(textbookStructure, /Authoritative review checklist/);
  assert.match(textbookStructure, /Select and review visual assets/);
  assert.match(textbookStructure, /Accessible text alternative/);
  assert.match(textbookStructure, /Approve visual/);
  assert.match(api, /applyRecommendedTopicSourceRoles/);
  assert.match(api, /getTopicVisualAssets/);
  assert.match(api, /reviewTopicVisualAsset/);
});

test('flashcards are Admin reviewed, source grounded and accessible to eligible Students', () => {
  assert.match(page, /\['flashcards', 'Flashcards'/);
  assert.match(page, /\['flashcards', 'Flashcard release'/);
  assert.match(api, /flashcards\/admin\/decks\/generate/);
  assert.match(api, /flashcards\/student\/sessions/);
  assert.match(flashcards, /Exact textbook evidence/);
  assert.match(flashcards, /Release approved deck/);
  assert.match(flashcards, /Show approved answer/);
  assert.match(flashcards, /How well did you remember it?/);
  assert.match(flashcards, /aria-live="polite"/);
  assert.match(flashcards, /<fieldset className="flashcard-face"/);
  assert.match(flashcards, /View source details/);
});
