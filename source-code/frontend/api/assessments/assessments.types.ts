/** Contracts owned by assessment delivery, marking and official-material review. */
export type FileRef = { id: string; name: string };
export type SourceLocation = { page: number; blockId: string; boundingBox: Record<string, unknown> };
export type OfficialMaterialReview = {
  versionNumber: number; status: string; kind: 'past_paper' | 'mark_scheme' | 'examiner_report';
  courseId: string; subjectId: string; sourcePaperId?: string | null; sourcePaperVersionId?: string | null;
  expectedItemCount: number; completenessConfirmed: boolean;
  questions: { number: string; parentNumber?: string | null; prompt: string; sharedStem: string; marks: number; equations: string[]; assetIds: string[]; sourceLocations: SourceLocation[] }[];
  markSchemeEntries: { questionNumber: string; maxMarks: number; markingPoints: { code: string; text: string; kind: 'method' | 'accuracy' | 'independent' | 'communication' | 'other' }[]; alternatives: string[]; sourceLocations: SourceLocation[] }[];
  examinerComments: { questionNumber: string; commonMistakes: string[]; advice: string[]; sourceLocations: SourceLocation[] }[];
};
export type TopicMapping = { topicRef: string; weight: number; required: boolean; rationale: string; confidence?: number | null; method?: string | null };
export type PaperMappings = {
  paperId: string; paperTitle: string; subjectId: string; textbookTitle: string; textbookEdition: string;
  groupLabel: 'unit' | 'module'; groups: { groupRef: string; code: string; title: string; topics: { topicRef: string; code: string; title: string; groupRef: string; groupCode: string; groupTitle: string }[] }[];
  questions: { questionId: string; number: string; prompt: string; sharedStem: string; marks: number; status: string; sourceLocations: SourceLocation[]; mappings: TopicMapping[]; groupWeights: Record<string, number> }[];
  confirmedQuestionCount: number; totalQuestionCount: number;
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
