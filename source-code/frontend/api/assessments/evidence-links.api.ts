import { request } from '../core/client';
import type {
  PaperReview,
  AnalysisProvenance,
} from './official-paper-review.api';
export type EvidenceProposal = {
  id: string;
  part: string;
  role: 'paper' | 'scheme';
  page?: number;
  text?: string;
  reason: string;
  confidence: number;
  autoEligible: boolean;
  status: string;
  normalizedBounds?: Record<'x0' | 'y0' | 'x1' | 'y1', number>;
  blockId?: string | null;
};
export type EvidenceRun = {
  id: string;
  number: string;
  revision: number;
  contentHash: string;
  createdAt: string;
  proposals: EvidenceProposal[];
  provenance: AnalysisProvenance[];
};
export type EvidenceJob = {
  id: string;
  number: string;
  status: string;
  errorCode?: string;
  result: { runId?: string; model?: string };
};
const root = (paperId: string) => `admin/official-paper-reviews/${paperId}`;
export const getEvidenceRuns = (paperId: string) =>
  request<EvidenceRun[]>(`${root(paperId)}/evidence-links`);
export const getEvidenceJobs = (paperId: string) =>
  request<EvidenceJob[]>(`${root(paperId)}/evidence-link-jobs`);
export const proposeEvidence = (paperId: string, body: unknown) =>
  request<EvidenceRun>(`${root(paperId)}/evidence-links`, {
    method: 'POST',
    body,
  });
export const queueEvidence = (paperId: string, body: unknown) =>
  request<EvidenceJob>(`${root(paperId)}/evidence-link-jobs`, {
    method: 'POST',
    body,
  });
export const reviewEvidence = (paperId: string, runId: string, body: unknown) =>
  request<{ run: EvidenceRun; review: PaperReview }>(
    `${root(paperId)}/evidence-links/${runId}/review`,
    { method: 'POST', body },
  );
export const queueEvidenceBatch = (paperId: string, questions: unknown[]) =>
  request<EvidenceJob[]>(`${root(paperId)}/evidence-link-job-batch`, {
    method: 'POST',
    body: { questions },
  });
