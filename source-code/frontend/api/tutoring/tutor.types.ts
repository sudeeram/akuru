/** Data contracts owned by the Tutor experience. */
import type { AssessmentResult } from '../assessments/assessments.types';

export type TutorAvatar = {
  code: string; name: string; description: string; imagePath: string;
  presentation: 'masculine' | 'feminine' | 'neutral'; enabled?: boolean; sortOrder?: number;
};
export type TutorVoice = {
  code: string; name: string; description: string;
  presentation: 'masculine' | 'feminine' | 'neutral'; enabled?: boolean; sortOrder?: number;
};
export type TutorOptions = {
  presentations: string[]; tones: string[]; levels: string[]; communicationCharacters: string[];
  explanationDepths: string[]; teachingStyles: string[]; avatars: TutorAvatar[]; voices: TutorVoice[];
};
export type TutorProfileDraft = {
  name: string; presentation: 'masculine' | 'feminine' | 'neutral'; avatarCode: string; voiceCode: string;
  tone: 'calm' | 'encouraging' | 'direct' | 'playful'; friendliness: 'low' | 'medium' | 'high';
  enthusiasm: 'low' | 'medium' | 'high'; speed: 'low' | 'medium' | 'high';
  communicationCharacter: 'childlike' | 'balanced' | 'authoritative';
  explanationDepth: 'concise' | 'standard' | 'detailed';
  teachingStyle: 'guided' | 'socratic' | 'example_led' | 'exam_focused';
};
export type TutorProfile = TutorProfileDraft & { profileRef: string; version: number; active: boolean };
export type TutorAdminPresets = { avatars: TutorAvatar[]; voices: TutorVoice[] };
export type TutorQuotaAmount = { allowance: number; used: number; remaining: number };
export type TutorQuota = {
  studentRef: string; studentName: string; enabled: boolean;
  state: 'available' | 'warning' | 'exhausted' | 'disabled' | 'renewed'; periodDays: number;
  periodStartsAt: string; renewsAt: string; requests: TutorQuotaAmount;
  textTokens: TutorQuotaAmount; voiceMinutes: TutorQuotaAmount; fallbackMessage: string;
};
export type TutorQuotaAudit = { studentRef: string; events: { action: string; reason: string; changes: Record<string, unknown>; createdAt: string }[] };
export type TutorHistorySummary = { summaryRef: string; sessionRef: string; studentName: string; subjectId: string; topicsCovered: { code: string; title: string }[]; activities: string[]; strengths: string[]; difficulties: string[]; suggestedNextSteps: string[]; usage: { aiRequests?: number; textTokens?: number; voiceTurns?: number }; createdAt: string };
export type TutorSafetyEvent = { eventRef: string; studentName: string; category: string; severity: string; action: string; notificationStatus: string; reviewStatus: string; createdAt: string };
export type TutorSessionTopic = { topicRef: string; code: string; title: string; groupRef: string; groupCode: string; groupTitle: string };
export type TutorTurn = { turnRef: string; role: 'student' | 'assistant'; modality: 'text' | 'voice'; content: string; sequence: number; profileRef: string; profileVersion: number; sources: string[]; structured: Partial<TutorAgentReply>; createdAt: string };
export type TutorSession = {
  sessionRef: string; subjectId: string; activeTopic: TutorSessionTopic; currentTutor: TutorProfile;
  mode: 'practice'; status: 'active' | 'ended'; startedAt: string; endedAt?: string | null;
  turns: TutorTurn[];
  profileEvents: { fromProfileRef: string; fromProfileVersion: number; toProfileRef: string; toProfileVersion: number; handoverSummary: Record<string, unknown>; createdAt: string }[];
  topicEvents: { fromTopic: TutorSessionTopic; toTopic: TutorSessionTopic; createdAt: string }[];
};
export type TutorSessionOptions = { subjects: { id: string; name: string; topics: TutorSessionTopic[] }[]; profiles: TutorProfile[] };
export type NextTopicResult = {
  status: 'ready' | 'no_evidence' | 'no_eligible_topics'; message: string; algorithmVersion: string;
  recommendation?: { topic: TutorSessionTopic; reason: string; evidenceRefs: string[];
    activity: { type: string; title: string; instruction: string; successCondition: string };
    requiresStudentAction: boolean; moveAction: Record<string, unknown> } | null;
  ranking: { topic: TutorSessionTopic; score: number }[];
};
export type TutorCitation = {
  citationRef: string; documentVersion: number; textbookTitle: string; textbookEdition: string;
  topicRef: string; topicCode: string; topicTitle: string; groupLabel: string; groupCode: string; groupTitle: string; contentKind: string; passage: string;
  pdfPageIndex: number; pdfPageNumber: number; printedPageLabel?: string | null; pageReference: string;
  boundingBox: Record<string, unknown>; confidence: number; assetRef: string; sourceUrl: string; assetUrl: string;
};
export type TutorSourceSearch = { status: 'exact' | 'evidence_insufficient'; message: string; query: string; citations: TutorCitation[] };
export type TutorCitationContext = { citation: TutorCitation; nearbyPassages: TutorCitation[]; groundingInstruction: string };
export type TutorAgentReply = {
  operationRef: string; turnRef: string; content: string;
  teachingMode: 'explanation' | 'questions' | 'guided_practice' | 'socratic_practice' | 'revision' | 'exam_technique' | 'french_conversation';
  citations: TutorCitation[]; followUpChoices: string[];
  toolResults: { name: string; status: 'ready' | 'evidence_insufficient' | 'unavailable'; summary: string; evidenceRefs: string[] }[];
  visuals: { title: string; altText: string; visualType: 'official_source' | 'explanatory'; kind: string;
    contentUrl?: string | null; readableFallback: string; equation?: string | null; sourceLabel: string;
    provenance: Record<string, unknown>; sourceRefs: string[] }[];
  proposedSignals: { category: string; observation: string; evidenceRefs: string[]; confidence: number }[];
  provider: string; model: string; promptName: string; promptVersion: string;
};
export type TutorPractice = {
  practiceRef: string; status: 'active' | 'submitted'; topicRef: string; topicCode: string; topicTitle: string; groupCode: string; groupTitle: string;
  question: { id: string; number: string; prompt: string; sharedStem: string; marks: number;
    equations: string[]; assetIds: string[]; answer: string; result?: AssessmentResult | null };
  assetUrls: string[]; hintCount: number; latestHint?: string | null; feedbackVisible: boolean;
  createdAt: string; submittedAt?: string | null;
};
export type TutorSignal = { signalRef: string; studentName: string; subjectId: string; topicRef: string; topicCode: string;
  topicTitle: string; category: string; observation: string; confidence: number; evidenceCount: number;
  promptName: string; promptVersion: string; createdAt: string };
export type RealtimeCredential = { connectionRef: string; clientSecret: string; expiresAt: string; model: string; voiceReady: boolean; reconnect: boolean };
export type RealtimeLanguageMode = 'auto' | 'french_conversation' | 'french_vocabulary' | 'french_pronunciation';
