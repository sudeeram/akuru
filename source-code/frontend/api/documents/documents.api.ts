/** Binary upload, extraction review and processing-job operations. */
import { request } from '../core/client';
import { ApiError, apiErrorMessage } from '../core/errors';
import { csrfToken } from '../core/csrf';
import type { DocumentExtraction, DocumentJob, LearningDocumentMetadata } from './documents.types';

export async function uploadLearningDocument(
  file: File,
  metadata: LearningDocumentMetadata,
): Promise<unknown> {
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

export async function getDocumentExtraction(id: string): Promise<DocumentExtraction> {
  return request<DocumentExtraction>(`documents/${id}/extraction`);
}
export const updateExtractionPage = (documentId: string, pageId: string, printedPageLabel: string) => request<DocumentExtraction>(`documents/${documentId}/extraction/pages/${pageId}`, { method: 'POST', body: { printedPageLabel } });
export const updateExtractionBlock = (documentId: string, blockId: string, body: { kind: string; text: string; latex?: string | null; caption?: string | null; sequenceNumber: number }) => request<DocumentExtraction>(`documents/${documentId}/extraction/blocks/${blockId}`, { method: 'POST', body });
export async function getLatestDocumentJob(id: string): Promise<DocumentJob> {
  return request<DocumentJob>(`documents/${id}/jobs/latest`);
}
export async function retryDocument(id: string): Promise<DocumentJob> {
  return request<DocumentJob>(`documents/${id}/retry`, { method: 'POST' });
}
export async function removeDocument(id: string): Promise<void> {
  await request<void>(`documents/${id}`, { method: 'DELETE' });
}
