/** Explainable topic mastery and improvement recommendation contracts. */
export type TopicMastery = {
  topicRef: string; topicCode: string; topicTitle: string; groupLabel: string; groupCode: string; groupTitle: string; subjectId: string;
  score: number; preciseScore: number; confidence: 'low' | 'medium' | 'high'; provisional: boolean;
  evidenceCount: number; evidenceWeight: number; varietyCount: number; trend: number; lastEvidenceAt: string;
  dimensions: { dimension: string; score: number; evidenceWeight: number }[];
  recentEvents: { id: string; previousScore?: number | null; newScore: number; previousConfidence?: string | null; newConfidence: string; explanation: string; createdAt: string }[];
};
export type MasteryGroup = { groupLabel: string; groupCode: string; groupTitle: string; subjectId: string; score: number; confidence: 'low' | 'medium' | 'high'; evidenceWeight: number; topicCount: number; explanation: string; topics: TopicMastery[] };
export type ImprovementRecommendation = {
  id: string; diagnosisId: string; studentId: string; subjectId: string; topicRef: string;
  topicCode: string; topicTitle: string; groupLabel: string; groupCode: string; groupTitle: string; category: string; description: string; observedEvidence: string[];
  occurrenceCount: number; activityType: 'review' | 'targeted_practice' | 'spaced_retry' | 'unit_check';
  title: string; reason: string; action: string; successCondition: string; sourceTitle: string;
  sourcePage: number; sourceUrl: string; questionId?: string | null;
  reviewStatus: 'approved' | 'pending_review' | 'rejected'; reviewReason: string; createdAt: string;
};
