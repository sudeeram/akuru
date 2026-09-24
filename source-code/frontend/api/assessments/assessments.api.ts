/** Assessment, official-material and question-mapping operations. */
import { request } from '../core/client';
import { csrfToken } from '../core/csrf';
import type { AssessmentAudit, FileRef, OfficialMaterialReview, PaperMappings, TopicMapping } from './assessments.types';

export const getOfficialMaterialReview = (id: string) =>
  request<OfficialMaterialReview>(`documents/${id}/official-review`);
export const proposeOfficialMaterialReview = (id: string) =>
  request<OfficialMaterialReview>(`documents/${id}/official-review/propose`, { method: 'POST', body: {} });
export const saveOfficialMaterialReview = (id: string, review: OfficialMaterialReview) =>
  request<OfficialMaterialReview>(`documents/${id}/official-review`, {
    method: 'POST',
    body: { expectedItemCount: review.expectedItemCount, completenessConfirmed: review.completenessConfirmed,
      questions: review.questions, markSchemeEntries: review.markSchemeEntries,
      examinerComments: review.examinerComments },
  });
export const publishOfficialMaterialReview = (id: string, linked: boolean) =>
  request<OfficialMaterialReview>(`documents/${id}/official-review/publish`, {
    method: 'POST',
    body: { confirmCourse: true, confirmSubject: true, confirmSourcePaper: linked, confirmComplete: true },
  });
export const getPaperMappings = (paperId: string) =>
  request<PaperMappings>(`questions/papers/${paperId}/topic-mappings`);
export const suggestQuestionMappings = (questionId: string) =>
  request<{ questionId: string; method: string; suggestions: TopicMapping[] }>(
    `questions/${questionId}/topic-mapping/suggest`, { method: 'POST', body: {} });
export const saveQuestionMappings = (questionId: string, mappings: TopicMapping[]) =>
  request<PaperMappings['questions'][number]>(`questions/${questionId}/topic-mapping`, {
    method: 'POST', body: { mappings },
  });
export const publishQuestionMappings = (questionId: string) =>
  request<PaperMappings['questions'][number]>(`questions/${questionId}/topic-mapping/publish`, {
    method: 'POST', body: {},
  });
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

export async function getAssessmentAudit() {
  return request<{ results: AssessmentAudit[] }>('assessments/admin/audit');
}

export async function reassessAssessment(id: string, idempotencyKey: string) {
  return request<unknown>(`assessments/admin/${id}/reassess`, { method: 'POST', body: { idempotencyKey } });
}
