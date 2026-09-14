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
};
export type UnitMastery = {
  unitId: string; unitCode: string; unitTitle: string; subjectId: string;
  score: number; preciseScore: number; confidence: 'low' | 'medium' | 'high'; provisional: boolean;
  evidenceCount: number; evidenceWeight: number; varietyCount: number; trend: number; lastEvidenceAt: string;
  dimensions: { dimension: string; score: number; evidenceWeight: number }[];
  recentEvents: { id: string; previousScore?: number | null; newScore: number; previousConfidence?: string | null; newConfidence: string; explanation: string; createdAt: string }[];
};
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
      updatedAt: string;
      items: {
        subject: string;
        topic: string;
        minutes: number;
        reason: string;
      }[];
    }
  >;
  mastery: Record<string, UnitMastery[]>;
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
