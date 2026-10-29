import { request } from '../core/client';

export type ReviewEvidence = {
  page: number;
  blockId?: string | null;
  assetId?: string | null;
};
export type ReviewStatus =
  | 'unreviewed'
  | 'needs_correction'
  | 'ready_for_approval'
  | 'approved'
  | 'excluded';
export type CoverageStatus =
  | 'unreviewed'
  | 'supported'
  | 'partial_or_uncertain'
  | 'outside_current_coverage';
export type MarkingRules = {
  version: 1;
  groups: {
    id: string;
    pointIds: string[];
    maxMarks: number;
    requiredForFullCredit: string[];
  }[];
  combinedResponses: { phrase: string; pointIds: string[] }[];
};
export type TextbookPageEvidence = {
  topicRef: string; documentVersionId: string; page: number; printedPageLabel: string;
};
export type TextbookPageOption = TextbookPageEvidence & { documentId: string; assetId: string };
export const getReviewTopicEvidence = (paperId: string, topicRef: string) =>
  request<{ visualPages: TextbookPageOption[] }>(`admin/official-paper-reviews/${paperId}/topics/${topicRef}/evidence`);
export type AnswerVisual = { assetId: string; partLabel: string; pointCodes: string[]; caption: string; altText: string; status: "proposed" | "approved" | "rejected" };
export type ReviewPart = {
  answerVisuals?: AnswerVisual[];
  answerVisualRequired?: boolean;
  responseType?: "text" | "drawing";
  label: string;
  marks: number;
  prompt: string;
  visualAssetIds: string[];
  markingPoints: {
    code: string;
    text: string;
    kind: 'method' | 'accuracy' | 'independent' | 'communication' | 'other';
    dependsOn?: string | null;
    followThrough?: boolean;
    acceptedAnswers?: string[];
  }[];
  alternatives: string[];
  examinerAdvice: string;
  scoringRules?: MarkingRules;
  assessmentReadiness?: 'unreviewed' | 'automatic' | 'manual_only';
  assessmentReadinessReason?: string;
  paperSources: ReviewEvidence[];
  schemeSources: ReviewEvidence[];
  reportSources: ReviewEvidence[];
  coverage: CoverageStatus;
  topicRefs: string[];
  coverageReason: string;
  textbookEvidence?: TextbookPageEvidence[];
  status: ReviewStatus;
};
export type ReviewQuestionData = {
  marks: number;
  sharedStem: string;
  prompt: string;
  paperSources: ReviewEvidence[];
  visualAssetIds: string[];
  candidateVisualAssetIds: string[];
  visualAltText: string;
  parts: ReviewPart[];
  exclusionReason: string;
};
export type PaperReview = {
  paperDocumentId: string;
  paperVersionId: string;
  schemeDocumentId: string | null;
  reportDocumentId: string | null;
  expectedQuestionCount: number;
  questionCount: number;
  approvedCount: number;
  assessmentReleaseReady?: boolean;
  automaticAssessmentReady?: boolean;
  assessmentBlockers?: string[];
  wholePaperReady: boolean;
  blockers: string[];
  questions: {
    number: string;
    revision: number;
    status: ReviewStatus;
    data: ReviewQuestionData;
    reviewedBy: string | null;
    reviewedAt: string | null;
  }[];
};
const base = (paperId: string) => `admin/official-paper-reviews/${paperId}`;
export const getPaperReview = (paperId: string) =>
  request<PaperReview>(base(paperId));
export const startPaperReview = (
  paperId: string,
  body: {
    schemeDocumentId?: string | null;
    reportDocumentId?: string | null;
    expectedQuestionCount?: number;
  },
) => request<PaperReview>(`${base(paperId)}/start`, { method: 'POST', body });
export const savePaperReviewQuestion = (
  paperId: string,
  body: {
    number: string;
    expectedRevision: number;
    status: ReviewStatus;
    data: ReviewQuestionData;
  },
) =>
  request<PaperReview>(`${base(paperId)}/questions`, { method: 'POST', body });
export const seedPaperReview = (
  paperId: string,
  draftBank: object,
  coverageTriage?: object,
) =>
  request<PaperReview>(`${base(paperId)}/seed`, {
    method: 'POST',
    body: { draftBank, coverageTriage },
  });
export const getReviewTopics = (paperId: string) =>
  request<{ topicRef: string; code: string; title: string }[]>(
    `${base(paperId)}/topics`,
  );
export const prepareOfficialReviewDrafts = (paperId: string) =>
  request<{
    paperDocumentId: string;
    paperDraftVersion: number;
    schemeDocumentId: string;
    schemeDraftVersion: number;
    published: false;
  }>(`${base(paperId)}/prepare-official-drafts`, { method: 'POST', body: {} });
export const createPaperReviewCrop = (
  paperId: string,
  body: {
    source?: "paper" | "scheme";
    page: number;
    kind: 'diagram' | 'table';
    x0: number;
    y0: number;
    x1: number;
    y1: number;
    altText: string;
  },
) =>
  request<{
    assetId: string;
    page: number;
    kind: 'diagram' | 'table';
    altText: string;
    approved: boolean;
    bounds: { x0: number; y0: number; x1: number; y1: number };
  }>(`${base(paperId)}/visual-crops`, { method: 'POST', body });
export const getPaperReviewCrops = (paperId: string) =>
  request<
    {
      assetId: string;
      page: number;
      kind: 'diagram' | 'table';
      altText: string;
      approved: boolean;
      bounds: { x0: number; y0: number; x1: number; y1: number };
    }[]
  >(`${base(paperId)}/visual-crops`);
export const generatePaperReviewVisuals = (paperId: string) =>
  request<{ created: number; attached: number; questionCount: number }>(
    `${base(paperId)}/visual-candidates/generate`,
    { method: 'POST', body: {} },
  );
