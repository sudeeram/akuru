import { request } from '../core/client';
import { csrfToken } from '../core/csrf';
import { ApiError, apiErrorMessage } from '../core/errors';

export type PreparedIssue = { id: string; title: string; reason: string; action: string; page: number };
export type PreparedSummary = { sha256: string; title: string; pageCount: number; blockCount: number; figureCount: number; exerciseCount: number; issues: PreparedIssue[]; documentId?: string; alreadyImported?: boolean };
export type PreparedReview = { documentId: string; contentHash: string; issues: PreparedIssue[]; decisions: Record<string, string>; confirmed: boolean; immutable: boolean; reviewUrl: string };
const base = (book: string, topic: string) => `admin/textbooks/${book}/topics/${topic}/prepared-packages`;

export async function uploadPreparedTextbook(book: string, topic: string, file: File, action: 'preview' | 'import'): Promise<PreparedSummary> {
  if (file.size > 50 * 1024 * 1024) throw new Error('Choose a package no larger than 50 MB.');
  const token = csrfToken();
  const response = await fetch(`/api/v1/${base(book, topic)}/${action}`, {
    method: 'POST', headers: { 'Content-Type': 'application/octet-stream', ...(token ? { 'X-CSRF-Token': token } : {}) }, body: file,
  });
  if (response.status === 401) {
    window.dispatchEvent(new Event('akuru:unauthorized'));
    throw new ApiError('Please sign in again to continue.', 401);
  }
  let data: unknown;
  try { data = await response.json(); } catch { throw new Error('The server returned an unreadable response.'); }
  if (!response.ok) throw new ApiError(apiErrorMessage(data), response.status);
  return data as PreparedSummary;
}
export const getPreparedReview = (book: string, topic: string, document: string) => request<PreparedReview>(`${base(book, topic)}/${document}/review`);
export const confirmPreparedReview = (book: string, topic: string, document: string, body: { contentHash: string; confirmWholeDocument: boolean; decisions: Record<string, string> }) => request<PreparedReview>(`${base(book, topic)}/${document}/review`, { method: 'POST', body });
