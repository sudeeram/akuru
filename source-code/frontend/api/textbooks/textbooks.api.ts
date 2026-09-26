/** Textbook hierarchy, topic source, publication and visual-review operations. */
import { request } from '../core/client';
import { ApiError, apiErrorMessage } from '../core/errors';
import { csrfToken } from '../core/csrf';
import type { DocumentJob } from '../documents/documents.types';
import type { TextbookStructure, TopicDocumentSource, TopicLaunchReadiness, TopicQualityReport, TopicRetrievalPreflight, TopicReviewChecklist, TopicSourceRole, TopicVisualAsset } from './textbooks.types';

export const getTextbookStructures = () => request<{ textbooks: TextbookStructure[] }>('admin/textbooks');

export const createTextbookStructure = (body: { courseId: 'igcse'; subjectId: string; title: string; edition: string; publisher: string; groupLabel: 'unit' | 'module' }) => request<TextbookStructure>('admin/textbooks', { method: 'POST', body });
export const updateTextbookStructure = (ref: string, body: { title: string; edition: string; publisher: string; groupLabel: 'unit' | 'module' }) => request<TextbookStructure>(`admin/textbooks/${ref}`, { method: 'POST', body });
export const archiveTextbookStructure = (ref: string) => request<TextbookStructure>(`admin/textbooks/${ref}`, { method: 'DELETE' });
export const saveTextbookGroup = (bookRef: string, body: { code: string; title: string; summary: string; sequence: number }, groupRef?: string) => request<TextbookStructure>(`admin/textbooks/${bookRef}/groups${groupRef ? `/${groupRef}` : ''}`, { method: 'POST', body });
export const removeTextbookGroup = (bookRef: string, groupRef: string) => request<TextbookStructure>(`admin/textbooks/${bookRef}/groups/${groupRef}`, { method: 'DELETE' });
export const reorderTextbookGroups = (bookRef: string, refs: string[]) => request<TextbookStructure>(`admin/textbooks/${bookRef}/groups/reorder`, { method: 'POST', body: { refs } });
export const saveTextbookTopic = (bookRef: string, groupRef: string, body: { code: string; title: string; sequence: number; syllabusRef: string; description: string }, topicRef?: string) => request<TextbookStructure>(`admin/textbooks/${bookRef}/groups/${groupRef}/topics${topicRef ? `/${topicRef}` : ''}`, { method: 'POST', body });
export const removeTextbookTopic = (bookRef: string, topicRef: string) => request<TextbookStructure>(`admin/textbooks/${bookRef}/topics/${topicRef}`, { method: 'DELETE' });
export const reorderTextbookTopics = (bookRef: string, groupRef: string, refs: string[]) => request<TextbookStructure>(`admin/textbooks/${bookRef}/groups/${groupRef}/topics/reorder`, { method: 'POST', body: { refs } });
export const publishTextbookStructure = (bookRef: string) => request<TextbookStructure>(`admin/textbooks/${bookRef}/publish`, { method: 'POST', body: { confirmCourse: true, confirmSubject: true, confirmEdition: true, confirmStructure: true } });
export const publishTextbookTopic = (bookRef: string, topicRef: string) => request<TextbookStructure>(`admin/textbooks/${bookRef}/topics/${topicRef}/publish`, { method: 'POST', body: { confirmSources: true, confirmExtraction: true, confirmTopic: true } });
export const getTopicQualityReport = (bookRef: string, topicRef: string) => request<TopicQualityReport>(`admin/textbooks/${bookRef}/topics/${topicRef}/quality`);
export const getTopicSources = (bookRef: string, topicRef: string) => request<TopicDocumentSource[]>(`admin/textbooks/${bookRef}/topics/${topicRef}/sources`);
export const applyRecommendedTopicSourceRoles = (bookRef: string, topicRef: string) => request<TopicDocumentSource[]>(`admin/textbooks/${bookRef}/topics/${topicRef}/sources/apply-recommended-roles`, { method: 'POST', body: {} });
export const updateTopicSourceRole = (bookRef: string, topicRef: string, documentId: string, role: TopicSourceRole) => request<TopicDocumentSource[]>(`admin/textbooks/${bookRef}/topics/${topicRef}/sources/${documentId}`, { method: 'PATCH', body: { role } });
export const detachTopicSource = (bookRef: string, topicRef: string, documentId: string) => request<TopicDocumentSource[]>(`admin/textbooks/${bookRef}/topics/${topicRef}/sources/${documentId}`, { method: 'DELETE' });
export const moveTopicSource = (bookRef: string, topicRef: string, documentId: string, targetTopicRef: string) => request<TopicDocumentSource[]>(`admin/textbooks/${bookRef}/topics/${topicRef}/sources/${documentId}/move`, { method: 'POST', body: { targetTopicRef } });
export const getTopicReviewChecklist = (bookRef: string, topicRef: string) => request<TopicReviewChecklist>(`admin/textbooks/${bookRef}/topics/${topicRef}/review-checklist`);
export const getTopicVisualAssets = (bookRef: string, topicRef: string, documentId: string) => request<TopicVisualAsset[]>(`admin/textbooks/${bookRef}/topics/${topicRef}/sources/${documentId}/visual-assets`);
export const reviewTopicVisualAsset = (bookRef: string, topicRef: string, documentId: string, assetRef: string, status: 'selected'|'approved'|'rejected', caption: string, altText: string) => request<TopicVisualAsset[]>(`admin/textbooks/${bookRef}/topics/${topicRef}/sources/${documentId}/visual-assets/${assetRef}`, { method: 'PATCH', body: { status, caption, altText } });
export const getTopicLaunchReadiness = (bookRef: string, topicRef: string, studentId?: string) => request<TopicLaunchReadiness>(`admin/textbooks/${bookRef}/topics/${topicRef}/launch-readiness${studentId ? `?studentId=${encodeURIComponent(studentId)}` : ''}`);
export const runTopicRetrievalPreflight = (bookRef: string, topicRef: string) => request<TopicRetrievalPreflight>(`admin/textbooks/${bookRef}/topics/${topicRef}/retrieval-preflight`, { method: 'POST', body: {} });
export async function uploadTopicPart(bookRef: string, topicRef: string, file: File,
  role: TopicSourceRole = 'primary', onProgress?: (percent: number) => void) {
  if (file.size > 50 * 1024 * 1024) throw new Error('Choose a file no larger than 50 MB.');
  return new Promise<{ document: { id: string }; job: DocumentJob }>((resolve, reject) => {
    const upload = new XMLHttpRequest();
    upload.open('POST', `/api/v1/admin/textbooks/${bookRef}/topics/${topicRef}/documents?role=${role}`);
    upload.setRequestHeader('Content-Type', file.type);
    upload.setRequestHeader('X-Filename', file.name);
    upload.setRequestHeader('Idempotency-Key', crypto.randomUUID());
    const csrf = csrfToken();
    if (csrf) upload.setRequestHeader('X-CSRF-Token', csrf);
    upload.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable) onProgress?.(Math.round((event.loaded / event.total) * 100));
    });
    upload.addEventListener('load', () => {
      let data: unknown = {};
      try { data = upload.responseText ? JSON.parse(upload.responseText) : {}; }
      catch { data = { detail: 'The server returned an unreadable response.' }; }
      if (upload.status >= 200 && upload.status < 300) {
        onProgress?.(100);
        resolve(data as { document: { id: string }; job: DocumentJob });
      } else {
        if (upload.status === 401 && typeof window !== 'undefined')
          window.dispatchEvent(new Event('akuru:unauthorized'));
        reject(new ApiError(apiErrorMessage(data), upload.status));
      }
    });
    upload.addEventListener('error', () => reject(new Error('The upload was interrupted. Check your connection and try again.')));
    upload.addEventListener('abort', () => reject(new Error('The upload was cancelled.')));
    upload.send(file);
  });
}
async function fileBase64(file: File) {
  const bytes = new Uint8Array(await file.arrayBuffer()); let binary = '';
  for (let offset = 0; offset < bytes.length; offset += 0x8000)
    binary += String.fromCharCode(...bytes.subarray(offset, offset + 0x8000));
  return btoa(binary);
}
export async function uploadTopicPartsBatch(bookRef: string, topicRef: string, files: File[], role: TopicSourceRole = 'primary') {
  const items = await Promise.all(files.map(async (file) => ({ filename: file.name,
    contentType: file.type, contentBase64: await fileBase64(file), role,
    idempotencyKey: crypto.randomUUID() })));
  return request<{ document: { id: string }; job: DocumentJob }[]>(
    `admin/textbooks/${bookRef}/topics/${topicRef}/documents/batch`,
    { method: 'POST', body: { items } },
  );
}
export const suggestTopicParts = (bookRef: string, filenames: string[]) =>
  request<{ filename: string; suggestedTopicRef?: string | null; suggestedTopicCode?: string | null; confidence: number }[]>(
    `admin/textbooks/${bookRef}/topics/suggest`,
    { method: 'POST', body: { filenames } },
  );
