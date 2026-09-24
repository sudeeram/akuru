/** Curriculum plan, period and topic contracts. */
export type CurriculumPlanPeriod = { grade: number; term: number; topicRefs: string[] };
export type CurriculumPlanTopic = { topicRef: string; code: string; title: string; groupRef: string; groupCode: string; groupTitle: string };
export type CurriculumPlanTopicGroup = { groupRef: string; code: string; title: string; topics: CurriculumPlanTopic[] };
export type CurriculumPlan = {
  versionNumber: number; status: string; subjectId: string; textbookTitle: string;
  textbookEdition: string;
  groupLabel: 'unit' | 'module'; groups: CurriculumPlanTopicGroup[];
  periods: (CurriculumPlanPeriod & { topicRefs: string[] })[];
  publishedPeriods: (CurriculumPlanPeriod & { topicRefs: string[] })[];
  changes: { topicRef: string; code: string; title: string; change: 'added' | 'removed' | 'moved'; fromPeriod?: string | null; toPeriod?: string | null }[];
  requiresPublishedChangeConfirmation: boolean; basedOnVersion?: number | null; createdAt?: string | null; publishedAt?: string | null;
};
