/** Tutor profile, session, practice, history, quota and realtime operations. */
import { request } from '../core/client';
import type {
  NextTopicResult,
  RealtimeCredential,
  RealtimeLanguageMode,
  TutorAdminPresets,
  TutorAgentReply,
  TutorCitationContext,
  TutorHistorySummary,
  TutorOptions,
  TutorPractice,
  TutorProfile,
  TutorProfileDraft,
  TutorQuota,
  TutorQuotaAudit,
  TutorSafetyEvent,
  TutorSession,
  TutorSessionOptions,
  TutorSignal,
  TutorSourceSearch,
} from './tutor.types';

export const getTutorOptions = () => request<TutorOptions>('tutoring/options');
export const getTutorProfiles = (studentId?: string) => request<{ profiles: TutorProfile[] }>(
  studentId ? `tutoring/students/${studentId}/profiles` : 'tutoring/profiles',
);
export const saveTutorProfile = (draft: TutorProfileDraft, profileRef?: string) => request<TutorProfile>(
  profileRef ? `tutoring/profiles/${profileRef}` : 'tutoring/profiles',
  { method: 'POST', body: draft },
);
export const deleteTutorProfile = (profileRef: string) => request<void>(
  `tutoring/profiles/${profileRef}`, { method: 'DELETE' },
);
export const getTutorAdminPresets = () => request<TutorAdminPresets>('tutoring/admin/presets');
export const updateTutorPreset = (kind: 'avatars' | 'voices', code: string, enabled: boolean, sortOrder: number) => request<TutorAdminPresets>(
  `tutoring/admin/${kind}/${code}`, { method: 'POST', body: { enabled, sortOrder } },
);
export const getTutorQuota = () => request<TutorQuota>('tutoring/quota');
export const getTutorAdminQuotas = () => request<{ quotas: TutorQuota[] }>('tutoring/admin/quotas');
export const updateTutorAdminQuota = (studentRef: string, body: { periodDays: number; requestAllowance: number; textTokenAllowance: number; voiceMinuteAllowance: number; enabled: boolean; reason: string }) => request<TutorQuota>(
  `tutoring/admin/quotas/${studentRef}`, { method: 'POST', body },
);
export const getTutorQuotaAudit = (studentRef: string) => request<TutorQuotaAudit>(`tutoring/admin/quotas/${studentRef}/audit`);
export const getTutorHistorySummaries = () => request<{ summaries: TutorHistorySummary[] }>('tutoring/history/summaries');
export const getTutorSafetyEvents = () => request<{ events: TutorSafetyEvent[] }>('tutoring/history/safety-events');
export const reviewTutorSafetyEvent = (eventRef: string, status: 'reviewed' | 'resolved', note: string) => request<unknown>(`tutoring/admin/safety-events/${eventRef}/review`, { method: 'POST', body: { status, note } });
export const getTutorSupportTranscript = (sessionRef: string, reason: string) => request<{ sessionRef: string; studentName: string; turns: { turnRef: string; role: string; modality: string; content: string; purged: boolean; createdAt: string }[] }>(`tutoring/admin/transcripts/${sessionRef}/support-access`, { method: 'POST', body: { reason } });
export const previewTutorTranscriptPurge = (days: number) => request<{ olderThanDays: number; cutoff: string; turnCount: number; sessionCount: number }>(`tutoring/admin/transcripts/purge-preview?olderThanDays=${days}`);
export const purgeTutorTranscripts = (olderThanDays: number, reason: string) => request<{ purgedTurnCount: number }>('tutoring/admin/transcripts/purge', { method: 'POST', body: { olderThanDays, reason, confirmation: 'PURGE TRANSCRIPTS' } });
export const createRealtimeCredential = (sessionRef: string, requestKey: string, languageMode: RealtimeLanguageMode, failedConnectionRef?: string) => request<RealtimeCredential>(
  `tutoring/sessions/${sessionRef}/realtime-credential`,
  { method: 'POST', body: { requestKey, languageMode, failedConnectionRef } },
);
export const updateRealtimeState = (connectionRef: string, state: 'connected' | 'ended' | 'failed' | 'cancelled', failureCode?: string) => request<unknown>(
  `tutoring/realtime/${connectionRef}/state`, { method: 'POST', body: { state, failureCode } },
);
export const saveRealtimeTranscriptTurn = (connectionRef: string, role: 'student' | 'assistant', content: string, requestKey: string) => request<unknown>(
  `tutoring/realtime/${connectionRef}/turns`, { method: 'POST', body: { role, content, requestKey } },
);
export const getTutorSessionOptions = () => request<TutorSessionOptions>('tutoring/session-options');
export const getTutorSessions = () => request<{ sessions: TutorSession[] }>('tutoring/sessions');
export const startTutorSession = (subjectId: string, topicRef: string, profileRef: string, requestKey: string) => request<TutorSession>('tutoring/sessions', { method: 'POST', body: { subjectId, topicRef, profileRef, requestKey } });
export const addTutorTurn = (sessionRef: string, content: string, modality: 'text' | 'voice', requestKey: string) => request<TutorSession>(`tutoring/sessions/${sessionRef}/turns`, { method: 'POST', body: { content, modality, requestKey } });
export const switchTutorProfile = (sessionRef: string, profileRef: string, requestKey: string) => request<TutorSession>(`tutoring/sessions/${sessionRef}/switch-profile`, { method: 'POST', body: { profileRef, requestKey } });
export const switchTutorTopic = (sessionRef: string, topicRef: string, requestKey: string) => request<TutorSession>(`tutoring/sessions/${sessionRef}/switch-topic`, { method: 'POST', body: { topicRef, requestKey } });
export const endTutorSession = (sessionRef: string, requestKey: string) => request<TutorSession>(`tutoring/sessions/${sessionRef}/end`, { method: 'POST', body: { requestKey } });
export const getNextTutorTopic = (sessionRef: string, subjectId: string, requestKey: string) => request<NextTopicResult>(`tutoring/sessions/${sessionRef}/next-topic`, { method: 'POST', body: { subjectId, requestKey } });
export const searchTutorSources = (sessionRef: string, query: string, textbookEdition?: string) => request<TutorSourceSearch>(`tutoring/sessions/${sessionRef}/sources/search`, { method: 'POST', body: { query, textbookEdition, limit: 5 } });
export const getTutorCitationContext = (sessionRef: string, citationRef: string) => request<TutorCitationContext>(`tutoring/sessions/${sessionRef}/sources/${citationRef}/context`);
export const addTutorAgentTurn = (sessionRef: string, message: string, teachingMode: TutorAgentReply['teachingMode'], requestKey: string) => request<TutorAgentReply>(`tutoring/sessions/${sessionRef}/agent-turns`, { method: 'POST', body: { message, teachingMode, requestKey } });
export const getTutorPractice = (sessionRef: string) => request<TutorPractice | null>(`tutoring/sessions/${sessionRef}/practice`);
export const startTutorPractice = (sessionRef: string, requestKey: string) => request<TutorPractice>(`tutoring/sessions/${sessionRef}/practice`, { method: 'POST', body: { requestKey } });
export const getTutorPracticeHint = (sessionRef: string, requestKey: string) => request<TutorPractice>(`tutoring/sessions/${sessionRef}/practice/hint`, { method: 'POST', body: { requestKey } });
export const saveTutorPracticeAnswer = (sessionRef: string, answer: string, requestKey: string) => request<TutorPractice>(`tutoring/sessions/${sessionRef}/practice/answer`, { method: 'POST', body: { answer, requestKey } });
export const submitTutorPractice = (sessionRef: string, requestKey: string) => request<TutorPractice>(`tutoring/sessions/${sessionRef}/practice/submit`, { method: 'POST', body: { requestKey } });
export const getTutorSignals = (studentId?: string) => request<{ signals: TutorSignal[] }>(`tutoring/signals${studentId ? `?studentId=${encodeURIComponent(studentId)}` : ''}`);
