export type {
  ApiOperation,
  ApiOperations,
  Schemas as BackendSchemas,
} from './generated/api-contract';

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}
export function errorMessage(error: unknown) {
  return error instanceof Error
    ? error.message
    : 'Something went wrong. Please try again.';
}
const fieldLabels: Record<string, string> = {
  username: 'Username',
  name: 'Full name',
  password: 'Password',
  parentId: 'Parent account',
  progression: 'Grade and Term progression',
  subjects: 'Subjects',
  newPassword: 'New password',
};
function apiErrorMessage(data: unknown) {
  if (!data || typeof data !== 'object')
    return 'The server could not process the request.';
  if ('error' in data && typeof data.error === 'object' && data.error) {
    const error = data.error as {
      message?: unknown;
      details?: unknown;
    };
    if (Array.isArray(error.details) && error.details.length) {
      const messages = error.details
        .map((item) => {
          if (!item || typeof item !== 'object') return '';
          const location =
            'location' in item && Array.isArray(item.location)
              ? item.location
              : [];
          const key = String(location.at(-1) ?? 'request');
          const label = fieldLabels[key] ?? key;
          const message =
            'message' in item && typeof item.message === 'string'
              ? item.message.replace(/^Value error,\s*/i, '')
              : 'is invalid';
          return `${label}: ${message}`;
        })
        .filter(Boolean);
      if (messages.length) return messages.join(' ');
    }
    if (typeof error.message === 'string') return error.message;
  }
  if ('error' in data && typeof data.error === 'string') return data.error;
  if ('detail' in data && typeof data.detail === 'string') return data.detail;
  if ('detail' in data && Array.isArray(data.detail)) {
    return data.detail
      .map((item) => {
        if (!item || typeof item !== 'object') return '';
        const location =
          'loc' in item && Array.isArray(item.loc) ? item.loc : [];
        const key = String(location.at(-1) ?? 'request');
        const label = fieldLabels[key] ?? key;
        const message =
          'msg' in item && typeof item.msg === 'string'
            ? item.msg.replace(/^Value error,\s*/i, '')
            : 'is invalid';
        return `${label}: ${message}`;
      })
      .filter(Boolean)
      .join(' ');
  }
  return 'The server could not process the request.';
}
function csrfToken() {
  return typeof document === 'undefined'
    ? ''
    : decodeURIComponent(
        document.cookie
          .split('; ')
          .find((value) => value.startsWith('akuru_csrf='))
          ?.slice('akuru_csrf='.length) ?? '',
      );
}
export type Lesson = { explanation: string; points: string[]; hints: string[] };
export type FileRef = { id: string; name: string };
export type TextbookReviewUnit = {
  code: string; chapter: string; title: string; summary: string; startPage: number; endPage: number;
  sections: string[]; definitions: string[]; concepts: string[]; equations: string[];
  examples: string[]; diagrams: string[];
};
export type TextbookReview = {
  versionNumber: number; status: string; courseId: string; subjectId: string;
  edition: string; units: TextbookReviewUnit[];
};
export type CurriculumPlanUnit = { id: string; code: string; title: string };
export type CurriculumPlanPeriod = { grade: number; term: number; unitIds: string[] };
export type CurriculumPlan = {
  versionNumber: number; status: string; subjectId: string; textbookTitle: string;
  textbookEdition: string; availableUnits: CurriculumPlanUnit[]; periods: CurriculumPlanPeriod[];
};
export type SourceLocation = { page: number; blockId: string; boundingBox: Record<string, unknown> };
export type OfficialMaterialReview = {
  versionNumber: number; status: string; kind: 'past_paper' | 'mark_scheme' | 'examiner_report';
  courseId: string; subjectId: string; sourcePaperId?: string | null; sourcePaperVersionId?: string | null;
  expectedItemCount: number; completenessConfirmed: boolean;
  questions: { number: string; parentNumber?: string | null; prompt: string; sharedStem: string; marks: number; equations: string[]; assetIds: string[]; sourceLocations: SourceLocation[] }[];
  markSchemeEntries: { questionNumber: string; maxMarks: number; markingPoints: { code: string; text: string; kind: 'method' | 'accuracy' | 'independent' | 'communication' | 'other' }[]; alternatives: string[]; sourceLocations: SourceLocation[] }[];
  examinerComments: { questionNumber: string; commonMistakes: string[]; advice: string[]; sourceLocations: SourceLocation[] }[];
};
export type UnitMapping = { unitId: string; weight: number; rationale: string; confidence?: number | null; method?: string | null };
export type PaperMappings = {
  paperId: string; paperTitle: string; subjectId: string; textbookTitle: string; textbookEdition: string;
  units: { id: string; code: string; title: string }[];
  questions: { questionId: string; number: string; prompt: string; marks: number; status: string; mappings: UnitMapping[] }[];
};
export type UiFeaturesAccess = {
  allowed: true;
  user: { name: string; role: 'admin' };
};
export type TutorAvatar = {
  code: string; name: string; description: string; imagePath: string;
  presentation: 'masculine' | 'feminine' | 'neutral'; enabled?: boolean; sortOrder?: number;
};
export type TutorVoice = {
  code: string; name: string; description: string;
  presentation: 'masculine' | 'feminine' | 'neutral'; enabled?: boolean; sortOrder?: number;
};
export type TutorOptions = {
  presentations: string[]; tones: string[]; levels: string[]; communicationCharacters: string[];
  explanationDepths: string[]; teachingStyles: string[]; avatars: TutorAvatar[]; voices: TutorVoice[];
};
export type TutorProfileDraft = {
  name: string; presentation: 'masculine' | 'feminine' | 'neutral'; avatarCode: string; voiceCode: string;
  tone: 'calm' | 'encouraging' | 'direct' | 'playful'; friendliness: 'low' | 'medium' | 'high';
  enthusiasm: 'low' | 'medium' | 'high'; speed: 'low' | 'medium' | 'high';
  communicationCharacter: 'childlike' | 'balanced' | 'authoritative';
  explanationDepth: 'concise' | 'standard' | 'detailed';
  teachingStyle: 'guided' | 'socratic' | 'example_led' | 'exam_focused';
};
export type TutorProfile = TutorProfileDraft & { profileRef: string; version: number; active: boolean };
export type TutorAdminPresets = { avatars: TutorAvatar[]; voices: TutorVoice[] };
export type TutorQuotaAmount = { allowance: number; used: number; remaining: number };
export type TutorQuota = {
  studentRef: string; studentName: string; enabled: boolean;
  state: 'available' | 'warning' | 'exhausted' | 'disabled' | 'renewed'; periodDays: number;
  periodStartsAt: string; renewsAt: string; requests: TutorQuotaAmount;
  textTokens: TutorQuotaAmount; voiceMinutes: TutorQuotaAmount; fallbackMessage: string;
};
export type TutorQuotaAudit = { studentRef: string; events: { action: string; reason: string; changes: Record<string, unknown>; createdAt: string }[] };
export type TutorHistorySummary = { summaryRef: string; sessionRef: string; studentName: string; subjectId: string; unitsCovered: { code: string; title: string }[]; activities: string[]; strengths: string[]; difficulties: string[]; suggestedNextSteps: string[]; usage: { aiRequests?: number; textTokens?: number; voiceTurns?: number }; createdAt: string };
export type TutorSafetyEvent = { eventRef: string; studentName: string; category: string; severity: string; action: string; notificationStatus: string; reviewStatus: string; createdAt: string };
export type TutorSessionUnit = { id: string; code: string; title: string };
export type TutorTurn = { turnRef: string; role: 'student' | 'assistant'; modality: 'text' | 'voice'; content: string; sequence: number; profileRef: string; profileVersion: number; sources: string[]; structured: Partial<TutorAgentReply>; createdAt: string };
export type TutorSession = {
  sessionRef: string; subjectId: string; activeUnit: TutorSessionUnit; currentTutor: TutorProfile;
  mode: 'practice'; status: 'active' | 'ended'; startedAt: string; endedAt?: string | null;
  turns: TutorTurn[];
  profileEvents: { fromProfileRef: string; fromProfileVersion: number; toProfileRef: string; toProfileVersion: number; handoverSummary: Record<string, unknown>; createdAt: string }[];
  unitEvents: { fromUnit: TutorSessionUnit; toUnit: TutorSessionUnit; createdAt: string }[];
};
export type TutorSessionOptions = { subjects: { id: string; name: string; units: TutorSessionUnit[] }[]; profiles: TutorProfile[] };
export type NextUnitResult = {
  status: 'ready' | 'no_evidence' | 'no_eligible_units'; message: string; algorithmVersion: string;
  recommendation?: { unit: TutorSessionUnit; reason: string; evidenceRefs: string[];
    activity: { type: string; title: string; instruction: string; successCondition: string };
    requiresStudentAction: boolean; moveAction: Record<string, unknown> } | null;
  ranking: { unit: TutorSessionUnit; score: number }[];
};
export type TutorCitation = {
  citationRef: string; documentVersion: number; textbookTitle: string; textbookEdition: string;
  unitId: string; unitCode: string; unitTitle: string; contentKind: string; passage: string;
  pdfPageIndex: number; pdfPageNumber: number; printedPageLabel?: string | null; pageReference: string;
  boundingBox: Record<string, unknown>; confidence: number; assetRef: string; sourceUrl: string; assetUrl: string;
};
export type TutorSourceSearch = { status: 'exact' | 'evidence_insufficient'; message: string; query: string; citations: TutorCitation[] };
export type TutorCitationContext = { citation: TutorCitation; nearbyPassages: TutorCitation[]; groundingInstruction: string };
export type TutorAgentReply = {
  operationRef: string; turnRef: string; content: string;
  teachingMode: 'explanation' | 'questions' | 'guided_practice' | 'socratic_practice' | 'revision' | 'exam_technique' | 'french_conversation';
  citations: TutorCitation[]; followUpChoices: string[];
  toolResults: { name: string; status: 'ready' | 'evidence_insufficient' | 'unavailable'; summary: string; evidenceRefs: string[] }[];
  visuals: { title: string; altText: string; visualType: 'official_source' | 'explanatory'; kind: string;
    contentUrl?: string | null; readableFallback: string; equation?: string | null; sourceLabel: string;
    provenance: Record<string, unknown>; sourceRefs: string[] }[];
  proposedSignals: { category: string; observation: string; evidenceRefs: string[]; confidence: number }[];
  provider: string; model: string; promptName: string; promptVersion: string;
};
export type TutorPractice = {
  practiceRef: string; status: 'active' | 'submitted'; unitCode: string; unitTitle: string;
  question: { id: string; number: string; prompt: string; sharedStem: string; marks: number;
    equations: string[]; assetIds: string[]; answer: string; result?: AssessmentResult | null };
  assetUrls: string[]; hintCount: number; latestHint?: string | null; feedbackVisible: boolean;
  createdAt: string; submittedAt?: string | null;
};
export type TutorSignal = { signalRef: string; studentName: string; subjectId: string; unitCode: string;
  unitTitle: string; category: string; observation: string; confidence: number; evidenceCount: number;
  promptName: string; promptVersion: string; createdAt: string };
type ApiResult<P extends string> = P extends 'state'
  ? State
  : P extends 'admin/ui-features'
    ? UiFeaturesAccess
    : P extends `lesson${string}`
      ? Lesson
      : P extends 'hint'
        ? { hint: string; total: number }
        : P extends 'attempt'
          ? Attempt
        : P extends `exams/${string}`
              ? Exam
              : unknown;
export async function api<P extends string>(
  path: P,
  body?: unknown,
): Promise<ApiResult<P>> {
  return request(path, { method: body === undefined ? 'GET' : 'POST', body }) as Promise<ApiResult<P>>;
}
async function request(
  path: string,
  options: { method?: 'GET' | 'POST' | 'DELETE'; body?: unknown } = {},
): Promise<unknown> {
  const csrf = csrfToken();
  const headers: Record<string, string> = {};
  const method = options.method ?? 'GET';
  if (options.body !== undefined) headers['Content-Type'] = 'application/json';
  if (method !== 'GET' && csrf) headers['X-CSRF-Token'] = csrf;
  const response = await fetch('/api/v1/' + path, {
    method,
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });
  const raw = response.status === 204 ? '' : await response.text();
  let data: unknown = {};
  if (raw) {
    try {
      data = JSON.parse(raw);
    } catch {
      data = { detail: 'The server returned an unreadable response.' };
    }
  }
  if (!response.ok) {
    throw new ApiError(apiErrorMessage(data), response.status);
  }
  return data;
}
export const getTutorOptions = () => request('tutoring/options') as Promise<TutorOptions>;
export const getTutorProfiles = (studentId?: string) => request(
  studentId ? `tutoring/students/${studentId}/profiles` : 'tutoring/profiles',
) as Promise<{ profiles: TutorProfile[] }>;
export const saveTutorProfile = (draft: TutorProfileDraft, profileRef?: string) => request(
  profileRef ? `tutoring/profiles/${profileRef}` : 'tutoring/profiles',
  { method: 'POST', body: draft },
) as Promise<TutorProfile>;
export const deleteTutorProfile = (profileRef: string) => request(
  `tutoring/profiles/${profileRef}`, { method: 'DELETE' },
);
export const getTutorAdminPresets = () => request('tutoring/admin/presets') as Promise<TutorAdminPresets>;
export const updateTutorPreset = (kind: 'avatars' | 'voices', code: string, enabled: boolean, sortOrder: number) => request(
  `tutoring/admin/${kind}/${code}`, { method: 'POST', body: { enabled, sortOrder } },
) as Promise<TutorAdminPresets>;
export const getTutorQuota = () => request('tutoring/quota') as Promise<TutorQuota>;
export const getTutorAdminQuotas = () => request('tutoring/admin/quotas') as Promise<{ quotas: TutorQuota[] }>;
export const updateTutorAdminQuota = (studentRef: string, body: { periodDays: number; requestAllowance: number; textTokenAllowance: number; voiceMinuteAllowance: number; enabled: boolean; reason: string }) => request(
  `tutoring/admin/quotas/${studentRef}`, { method: 'POST', body },
) as Promise<TutorQuota>;
export const getTutorQuotaAudit = (studentRef: string) => request(`tutoring/admin/quotas/${studentRef}/audit`) as Promise<TutorQuotaAudit>;
export const getTutorHistorySummaries = () => request('tutoring/history/summaries') as Promise<{ summaries: TutorHistorySummary[] }>;
export const getTutorSafetyEvents = () => request('tutoring/history/safety-events') as Promise<{ events: TutorSafetyEvent[] }>;
export const reviewTutorSafetyEvent = (eventRef: string, status: 'reviewed' | 'resolved', note: string) => request(`tutoring/admin/safety-events/${eventRef}/review`, { method: 'POST', body: { status, note } });
export const getTutorSupportTranscript = (sessionRef: string, reason: string) => request(`tutoring/admin/transcripts/${sessionRef}/support-access`, { method: 'POST', body: { reason } }) as Promise<{ sessionRef: string; studentName: string; turns: { turnRef: string; role: string; modality: string; content: string; purged: boolean; createdAt: string }[] }>;
export const previewTutorTranscriptPurge = (days: number) => request(`tutoring/admin/transcripts/purge-preview?olderThanDays=${days}`) as Promise<{ olderThanDays: number; cutoff: string; turnCount: number; sessionCount: number }>;
export const purgeTutorTranscripts = (olderThanDays: number, reason: string) => request('tutoring/admin/transcripts/purge', { method: 'POST', body: { olderThanDays, reason, confirmation: 'PURGE TRANSCRIPTS' } }) as Promise<{ purgedTurnCount: number }>;
export type RealtimeCredential = { connectionRef: string; clientSecret: string; expiresAt: string; model: string; voiceReady: boolean; reconnect: boolean };
export type RealtimeLanguageMode = 'auto' | 'french_conversation' | 'french_vocabulary' | 'french_pronunciation';
export const createRealtimeCredential = (sessionRef: string, requestKey: string, languageMode: RealtimeLanguageMode, failedConnectionRef?: string) => request(
  `tutoring/sessions/${sessionRef}/realtime-credential`,
  { method: 'POST', body: { requestKey, languageMode, failedConnectionRef } },
) as Promise<RealtimeCredential>;
export const updateRealtimeState = (connectionRef: string, state: 'connected' | 'ended' | 'failed' | 'cancelled', failureCode?: string) => request(
  `tutoring/realtime/${connectionRef}/state`, { method: 'POST', body: { state, failureCode } },
);
export const saveRealtimeTranscriptTurn = (connectionRef: string, role: 'student' | 'assistant', content: string, requestKey: string) => request(
  `tutoring/realtime/${connectionRef}/turns`, { method: 'POST', body: { role, content, requestKey } },
);
export const getTutorSessionOptions = () => request('tutoring/session-options') as Promise<TutorSessionOptions>;
export const getTutorSessions = () => request('tutoring/sessions') as Promise<{ sessions: TutorSession[] }>;
export const startTutorSession = (subjectId: string, unitId: string, profileRef: string, requestKey: string) => request('tutoring/sessions', { method: 'POST', body: { subjectId, unitId, profileRef, requestKey } }) as Promise<TutorSession>;
export const addTutorTurn = (sessionRef: string, content: string, modality: 'text' | 'voice', requestKey: string) => request(`tutoring/sessions/${sessionRef}/turns`, { method: 'POST', body: { content, modality, requestKey } }) as Promise<TutorSession>;
export const switchTutorProfile = (sessionRef: string, profileRef: string, requestKey: string) => request(`tutoring/sessions/${sessionRef}/switch-profile`, { method: 'POST', body: { profileRef, requestKey } }) as Promise<TutorSession>;
export const switchTutorUnit = (sessionRef: string, unitId: string, requestKey: string) => request(`tutoring/sessions/${sessionRef}/switch-unit`, { method: 'POST', body: { unitId, requestKey } }) as Promise<TutorSession>;
export const endTutorSession = (sessionRef: string, requestKey: string) => request(`tutoring/sessions/${sessionRef}/end`, { method: 'POST', body: { requestKey } }) as Promise<TutorSession>;
export const getNextTutorUnit = (sessionRef: string, subjectId: string, requestKey: string) => request(`tutoring/sessions/${sessionRef}/next-unit`, { method: 'POST', body: { subjectId, requestKey } }) as Promise<NextUnitResult>;
export const searchTutorSources = (sessionRef: string, query: string, textbookEdition?: string) => request(`tutoring/sessions/${sessionRef}/sources/search`, { method: 'POST', body: { query, textbookEdition, limit: 5 } }) as Promise<TutorSourceSearch>;
export const getTutorCitationContext = (sessionRef: string, citationRef: string) => request(`tutoring/sessions/${sessionRef}/sources/${citationRef}/context`) as Promise<TutorCitationContext>;
export const addTutorAgentTurn = (sessionRef: string, message: string, teachingMode: TutorAgentReply['teachingMode'], requestKey: string) => request(`tutoring/sessions/${sessionRef}/agent-turns`, { method: 'POST', body: { message, teachingMode, requestKey } }) as Promise<TutorAgentReply>;
export const getTutorPractice = (sessionRef: string) => request(`tutoring/sessions/${sessionRef}/practice`) as Promise<TutorPractice | null>;
export const startTutorPractice = (sessionRef: string, requestKey: string) => request(`tutoring/sessions/${sessionRef}/practice`, { method: 'POST', body: { requestKey } }) as Promise<TutorPractice>;
export const getTutorPracticeHint = (sessionRef: string, requestKey: string) => request(`tutoring/sessions/${sessionRef}/practice/hint`, { method: 'POST', body: { requestKey } }) as Promise<TutorPractice>;
export const saveTutorPracticeAnswer = (sessionRef: string, answer: string, requestKey: string) => request(`tutoring/sessions/${sessionRef}/practice/answer`, { method: 'POST', body: { answer, requestKey } }) as Promise<TutorPractice>;
export const submitTutorPractice = (sessionRef: string, requestKey: string) => request(`tutoring/sessions/${sessionRef}/practice/submit`, { method: 'POST', body: { requestKey } }) as Promise<TutorPractice>;
export const getTutorSignals = (studentId?: string) => request(`tutoring/signals${studentId ? `?studentId=${encodeURIComponent(studentId)}` : ''}`) as Promise<{ signals: TutorSignal[] }>;
export async function uploadLearningDocument(
  file: File,
  metadata: {
    kind:
      | 'textbook'
      | 'reference'
      | 'past_paper'
      | 'mark_scheme'
      | 'examiner_report';
    courseId: string;
    subjectId: string;
    title: string;
    sourceDocumentId?: string;
    edition?: string;
    year?: string;
    session?: string;
    component?: string;
    variant?: string;
    publisher?: string;
    isbn?: string;
    sourceUrl?: string;
  },
) {
  if (file.size > 50 * 1024 * 1024)
    throw new Error('Choose a file no larger than 50 MB.');
  const query = new URLSearchParams(
    Object.entries(metadata).filter(
      (entry): entry is [string, string] => typeof entry[1] === 'string',
    ),
  );
  const response = await fetch(`/api/v1/documents?${query}`, {
    method: 'POST',
    headers: {
      'Content-Type': file.type || 'application/octet-stream',
      'X-Filename': file.name,
      'X-CSRF-Token': csrfToken(),
    },
    body: file,
  });
  const data: unknown = await response.json().catch(() => ({}));
  if (!response.ok) throw new ApiError(apiErrorMessage(data), response.status);
  return data;
}
export const getTextbookReview = (id: string) =>
  api(`documents/${id}/textbook-review`) as Promise<TextbookReview>;
export const proposeTextbookReview = (id: string) =>
  api(`documents/${id}/textbook-review/propose`, {}) as Promise<TextbookReview>;
export const saveTextbookReview = (id: string, review: TextbookReview) =>
  api(`documents/${id}/textbook-review`, {
    courseId: review.courseId, subjectId: review.subjectId,
    edition: review.edition, units: review.units,
  }) as Promise<TextbookReview>;
export const publishTextbookReview = (id: string) =>
  api(`documents/${id}/textbook-review/publish`, {
    confirmCourse: true, confirmSubject: true, confirmEdition: true,
  }) as Promise<TextbookReview>;
export const getCurriculumPlan = (subjectId: string) =>
  api(`admin/curriculum-plans/${subjectId}`) as Promise<CurriculumPlan>;
export const saveCurriculumPlan = (subjectId: string, periods: CurriculumPlanPeriod[]) =>
  api(`admin/curriculum-plans/${subjectId}`, { periods }) as Promise<CurriculumPlan>;
export const publishCurriculumPlan = (subjectId: string) =>
  api(`admin/curriculum-plans/${subjectId}/publish`, {
    confirmSubject: true, confirmTextbook: true,
  }) as Promise<CurriculumPlan>;
export const getOfficialMaterialReview = (id: string) =>
  api(`documents/${id}/official-review`) as Promise<OfficialMaterialReview>;
export const proposeOfficialMaterialReview = (id: string) =>
  api(`documents/${id}/official-review/propose`, {}) as Promise<OfficialMaterialReview>;
export const saveOfficialMaterialReview = (id: string, review: OfficialMaterialReview) =>
  api(`documents/${id}/official-review`, {
    expectedItemCount: review.expectedItemCount, completenessConfirmed: review.completenessConfirmed,
    questions: review.questions, markSchemeEntries: review.markSchemeEntries,
    examinerComments: review.examinerComments,
  }) as Promise<OfficialMaterialReview>;
export const publishOfficialMaterialReview = (id: string, linked: boolean) =>
  api(`documents/${id}/official-review/publish`, {
    confirmCourse: true, confirmSubject: true, confirmSourcePaper: linked, confirmComplete: true,
  }) as Promise<OfficialMaterialReview>;
export const getPaperMappings = (paperId: string) =>
  api(`questions/papers/${paperId}/unit-mappings`) as Promise<PaperMappings>;
export const suggestQuestionMappings = (questionId: string) =>
  api(`questions/${questionId}/unit-mapping/suggest`, {}) as Promise<{ questionId: string; method: string; suggestions: UnitMapping[] }>;
export const saveQuestionMappings = (questionId: string, mappings: UnitMapping[]) =>
  api(`questions/${questionId}/unit-mapping`, { mappings }) as Promise<PaperMappings['questions'][number]>;
export const publishQuestionMappings = (questionId: string) =>
  api(`questions/${questionId}/unit-mapping/publish`, {}) as Promise<PaperMappings['questions'][number]>;
export async function uploadWorking(file: File, assessmentId: string, questionId: string): Promise<FileRef & { ocrConfidence: number; needsReview: boolean }> {
  if (file.size > 5 * 1024 * 1024) throw new Error('Choose a file smaller than 5 MB.');
  const token = csrfToken();
  const response = await fetch(`/api/v1/assessments/${assessmentId}/questions/${questionId}/working`, {
    method: 'POST', headers: { 'Content-Type': file.type, 'X-Filename': file.name, ...(token ? { 'X-CSRF-Token': token } : {}) }, body: file,
  });
  const raw = await response.text();
  const data = raw ? JSON.parse(raw) : {};
  if (!response.ok) throw new Error(data?.error?.message || 'Working could not be uploaded.');
  return data;
}
export type Subject = {
  id: string;
  name: string;
  symbol: string;
  color: string;
  topic: string;
  topics: string[];
  course: string;
};
export type Student = {
  parentId: string;
  username: string;
  term: string;
  progression: { grade: string; term: string }[];
  needsConfiguration?: boolean;
  id: string;
  name: string;
  initial: string;
  grade: string;
  level: string;
  subjects: string[];
  courses: Record<string, { level: string; syllabus: string }>;
};
export type Question = {
  unitIds?: string[];
  course?: string;
  id: string;
  subject: string;
  topic: string;
  title: string;
  prompt: string;
  marks: number;
  type: string;
  unit?: string;
  diagram: string;
  source: string;
  assetIds?: string[];
  equations?: string[];
  assessmentId?: string;
};
export type Attempt = {
  id: string;
  studentId: string;
  subject: string;
  questionId: string;
  title: string;
  answer: string;
  fileId: string;
  hints: number;
  mark: number | null;
  maxMarks: number;
  status: string;
  feedback: string;
  explanation: string;
  points: string[];
  improvedAnswer?: string;
  recommendations?: string[];
  createdAt: string;
  examId?: string;
  assessmentId?: string;
  workingUrl?: string;
  confidence?: number;
  resultVersion?: number;
  reviewReasons?: string[];
  strengths?: string[];
  smallMistakes?: string[];
  conceptualMistakes?: string[];
  markingDecisions?: { pointId: string; criterion: string; awarded: boolean; marksAwarded: number; maxMarks: number; studentEvidence: string; rationale: string; confidence: number }[];
};
export type AssessmentAudit = {
  answer: string; workingUrl?: string | null;
  resultId: string; assessmentId: string; questionId: string; studentId: string; studentName: string;
  subjectId: string; assessmentTitle: string; questionNumber: string; questionPrompt: string; version: number;
  status: string; awardedMarks: number; maxMarks: number; confidence: number; provider: string; model: string;
  promptName: string; promptVersion: string; subjectEngine: string; subjectEngineVersion: string;
  reviewReasons: string[]; markingDecisions: NonNullable<Attempt['markingDecisions']>; strengths: string[];
  smallMistakes: string[]; conceptualMistakes: string[]; improvedAnswer: string; teachingExplanation: string;
  deterministicChecks: Record<string, unknown>; sourceManifest: Record<string, unknown>[]; createdAt: string;
};

export async function getAssessmentAudit() {
  return request('assessments/admin/audit') as Promise<{ results: AssessmentAudit[] }>;
}

export async function reassessAssessment(id: string, idempotencyKey: string) {
  return request(`assessments/admin/${id}/reassess`, { method: 'POST', body: { idempotencyKey } });
}
export type UnitMastery = {
  unitId: string; unitCode: string; unitTitle: string; subjectId: string;
  score: number; preciseScore: number; confidence: 'low' | 'medium' | 'high'; provisional: boolean;
  evidenceCount: number; evidenceWeight: number; varietyCount: number; trend: number; lastEvidenceAt: string;
  dimensions: { dimension: string; score: number; evidenceWeight: number }[];
  recentEvents: { id: string; previousScore?: number | null; newScore: number; previousConfidence?: string | null; newConfidence: string; explanation: string; createdAt: string }[];
};
export type ImprovementRecommendation = {
  id: string; diagnosisId: string; studentId: string; subjectId: string; unitId: string;
  unitCode: string; unitTitle: string; category: string; description: string; observedEvidence: string[];
  occurrenceCount: number; activityType: 'review' | 'targeted_practice' | 'spaced_retry' | 'unit_check';
  title: string; reason: string; action: string; successCondition: string; sourceTitle: string;
  sourcePage: number; sourceUrl: string; questionId?: string | null;
  reviewStatus: 'approved' | 'pending_review' | 'rejected'; reviewReason: string; createdAt: string;
};
export type EducationalMedia = {
  id: string; subjectId: string; unitId: string; sourceChunkId: string; kind: string; title: string;
  altText: string; prompt: string; promptVersion: string; parameters: Record<string, unknown>;
  sourceManifest: { documentTitle?: string; unitCode?: string; page?: number }[]; provider: string;
  model: string; responseId?: string | null; contentType: string; status: string; reviewNotes: string;
  createdAt: string; reviewedAt?: string | null; contentUrl: string;
};
export type MediaSource = { id: string; subjectId: string; unitCode: string; unitTitle: string; documentTitle: string; page: number; excerpt: string };
export type Assignment = {
  id: string;
  studentId: string;
  subject: string;
  title: string;
  due: string;
  questionId: string;
  completed: boolean;
};
export type Doc = {
  course: string;
  textbookId?: string;
  paperId?: string;
  legacy?: boolean;
  id: string;
  name: string;
  subject: string;
  kind: string;
  status: string;
  notes: string;
  processingProgress?: number;
  processingError?: string | null;
  edition?: string | null;
};
export type ExtractionBlock = {
  sequenceNumber: number;
  kind: string;
  text: string;
  latex?: string | null;
  boundingBox: Record<string, number>;
  method: string;
  confidence: number;
  needsReview: boolean;
  sourceAssetId?: string | null;
  metadata: Record<string, unknown>;
};
export type ExtractionPage = {
  pageNumber: number;
  widthPoints: number;
  heightPoints: number;
  renderAssetId: string;
  method: string;
  confidence: number;
  needsReview: boolean;
  metadata: Record<string, unknown>;
  blocks: ExtractionBlock[];
};
export type DocumentExtraction = {
  status: string;
  pages: ExtractionPage[];
};
export async function getDocumentExtraction(id: string): Promise<DocumentExtraction> {
  return request(`documents/${id}/extraction`) as Promise<DocumentExtraction>;
}
export type DocumentJob = {
  stage: string;
  status: string;
  progress: number;
  attemptCount: number;
  extractionVersion: string;
  errorCode?: string | null;
  errorMessage?: string | null;
  result: Record<string, unknown>;
  queuedAt: string;
  startedAt?: string | null;
  completedAt?: string | null;
};
export async function getLatestDocumentJob(id: string): Promise<DocumentJob> {
  return request(`documents/${id}/jobs/latest`) as Promise<DocumentJob>;
}
export async function retryDocument(id: string): Promise<DocumentJob> {
  return request(`documents/${id}/retry`, { method: 'POST' }) as Promise<DocumentJob>;
}
export async function removeDocument(id: string): Promise<void> {
  await request(`documents/${id}`, { method: 'DELETE' });
}
export type Exam = {
  id: string;
  studentId: string;
  subject: string;
  status: string;
  startedAt: string;
  endsAt: string;
  questionIds: string[];
  answers: Record<string, string>;
  files: Record<string, string>;
  mode: 'practice' | 'official_paper' | 'mock';
  feedbackVisible: boolean;
};
export type AssessmentApiResponse = {
  id: string; studentId: string; subjectId: string; status: string;
  submittedAt?: string | null;
  questions: { id: string; rubric?: { markingPoints?: { text?: string }[] } | null; result?: AssessmentResult | null }[];
};
export type AssessmentResult = {
  id: string; version: number; status: 'published' | 'needs_review'; awardedMarks: number; maxMarks: number;
  confidence: number; strengths: string[]; smallMistakes: string[]; conceptualMistakes: string[];
  improvedAnswer: string; teachingExplanation: string; recommendations: string[]; reviewReasons: string[];
  markingDecisions: { pointId: string; criterion: string; awarded: boolean; marksAwarded: number; maxMarks: number; studentEvidence: string; rationale: string; confidence: number }[];
  subjectEngine: string; subjectEngineVersion: string; deterministicChecks: Record<string, unknown>;
};
export type State = {
  catalog: {
    courses: string[];
    activeCourses: string[];
    grades: string[];
    terms: string[];
    kinds: string[];
    progressionPairs: { grade: string; term: string }[];
  };
  accounts: { id: string; username: string; name: string; role: string }[];
  units: Unit[];
  coverage: Coverage[];
  questionBank: BankQuestion[];
  drafts: Record<string, string>;
  user: {
    id: string;
    username: string;
    name: string;
    role: string;
    mustChangePassword: boolean;
  };
  subjects: Subject[];
  questions: Question[];
  students: Student[];
  attempts: Attempt[];
  assignments: Assignment[];
  documents: Doc[];
  exams: Exam[];
  assessmentBlueprints: { id: string; name: string; subjectId: string; grade: number; term: number; targetMarks: number; durationMinutes: number; questionCount: number; skills: string[]; difficultyProfile: Record<string, number>; status: string }[];
  officialPapers: { id: string; subjectId: string; title: string; questionCount: number; marks: number }[];
  reviews: {
    id: string;
    studentId: string;
    feedback: string;
    createdAt: string;
  }[];
  plans: Record<
    string,
    {
      id: string;
      studentId: string;
      version: number;
      updatedAt: string;
      generationReason: 'evidence' | 'request';
      items: {
        id: string;
        subject: string;
        unitId: string;
        unitCode: string;
        topic: string;
        activityType: string;
        minutes: number;
        reason: string;
        source: string;
        sourceUrl: string;
        successCondition: string;
        scheduledFor: string;
        status: string;
      }[];
    }
  >;
  mastery: Record<string, UnitMastery[]>;
  recommendations: Record<string, ImprovementRecommendation[]>;
};
export type Unit = {
  id: string;
  textbookId: string;
  subject: string;
  course: string;
  code: string;
  title: string;
};
export type Coverage = {
  course: string;
  subject: string;
  grade: string;
  term: string;
  unitIds: string[];
};
export type BankQuestion = Question & {
  paperId: string;
  number: string;
  status: string;
  unitIds: string[];
  explanation: string;
  points: string[];
  hints: string[];
  answer: number | null;
};
