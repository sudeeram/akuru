import { request } from '../core/client';

export type ReviewEvidence = { page: number; blockId?: string | null; assetId?: string | null };
export type ReviewStatus = 'unreviewed' | 'needs_correction' | 'ready_for_approval' | 'approved' | 'excluded';
export type CoverageStatus = 'unreviewed' | 'supported' | 'partial_or_uncertain' | 'outside_current_coverage';
export type ReviewPart = {
  label: string; marks: number; prompt: string;
  markingPoints: { code: string; text: string; kind: 'method'|'accuracy'|'independent'|'communication'|'other'; dependsOn?: string | null; followThrough?: boolean }[];
  alternatives: string[]; examinerAdvice: string;
  paperSources: ReviewEvidence[]; schemeSources: ReviewEvidence[]; reportSources: ReviewEvidence[];
  coverage: CoverageStatus; topicRefs: string[]; coverageReason: string; status: ReviewStatus;
};
export type ReviewQuestionData = {
  marks: number; sharedStem: string; prompt: string;
  paperSources: ReviewEvidence[]; visualAssetIds: string[]; visualAltText: string;
  parts: ReviewPart[]; exclusionReason: string;
};
export type PaperReview = {
  paperDocumentId: string; paperVersionId: string; schemeDocumentId: string|null; reportDocumentId: string|null;
  expectedQuestionCount: number; questionCount: number; approvedCount: number;
  wholePaperReady: boolean; blockers: string[];
  questions: { number: string; revision: number; status: ReviewStatus; data: ReviewQuestionData; reviewedBy: string|null; reviewedAt: string|null }[];
};
const base = (paperId: string) => `admin/official-paper-reviews/${paperId}`;
export const getPaperReview = (paperId: string) => request<PaperReview>(base(paperId));
export const startPaperReview = (paperId: string, body: {schemeDocumentId?: string|null; reportDocumentId?: string|null; expectedQuestionCount?: number}) =>
  request<PaperReview>(`${base(paperId)}/start`, { method: 'POST', body });
export const savePaperReviewQuestion = (paperId: string, body: {number: string; expectedRevision: number; status: ReviewStatus; data: ReviewQuestionData}) =>
  request<PaperReview>(`${base(paperId)}/questions`, { method: 'POST', body });
export const seedPaperReview = (paperId: string, draftBank: object, coverageTriage?: object) =>
  request<PaperReview>(`${base(paperId)}/seed`, { method: 'POST', body: { draftBank, coverageTriage } });
export const getReviewTopics = (paperId: string) =>
  request<{topicRef: string; code: string; title: string}[]>(`${base(paperId)}/topics`);
export const getReviewTopicEvidence = (paperId: string, topicRef: string) =>
  request<{topicRef: string; code: string; title: string; chunks: {pageNumber: number; text: string}[]}>(`${base(paperId)}/topics/${encodeURIComponent(topicRef)}/evidence`);
export const prepareOfficialReviewDrafts = (paperId: string) =>
  request<{paperDocumentId:string;paperDraftVersion:number;schemeDocumentId:string;schemeDraftVersion:number;published:false}>(`${base(paperId)}/prepare-official-drafts`, {method:'POST',body:{}});
