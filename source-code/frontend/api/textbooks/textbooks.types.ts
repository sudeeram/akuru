/** Textbook structure, source-role, readiness and visual asset contracts. */
export type TextbookStructureTopic = {
  topicRef: string; code: string; title: string; sequence: number; syllabusRef: string;
  description: string; status: string; documentCount: number; removable: boolean;
  content: { state: string; ready: boolean; contentVersion: number; supersededVersionCount: number; hasDraftChanges: boolean; documentCount: number;
    primaryDocumentCount: number; processingCount: number; needsReviewCount: number; failedCount: number;
    unresolvedPageCount: number; unresolvedBlockCount: number; averageConfidence: number;
    checks: { code: string; passed: boolean; message: string }[] };
};
export type TextbookStructureGroup = {
  groupRef: string; code: string; title: string; summary: string; sequence: number;
  status: string; removable: boolean; topics: TextbookStructureTopic[]; totalTopicCount: number;
  reviewedTopicCount: number; publishedTopicCount: number; studentEligibleTopicCount: number;
};
export type TextbookStructure = {
  textbookRef: string; courseId: string; subjectId: string; title: string; edition: string;
  publisher: string; groupLabel: 'unit' | 'module'; groupDisplayLabel: 'Unit' | 'Module';
  status: string; structureVersion: number; groups: TextbookStructureGroup[];
};

export type TopicQualityReport = { topicRef: string; topicCode: string; topicTitle: string; thresholds: Record<string, number>; passed: boolean; resolution: string; documents: { documentId: string; filename: string; role: string; reviewStatus: string; pageCount: number; equationCount: number; diagramCount: number; passed: boolean; checks: { code: string; threshold: number; value: number; passed: boolean }[] }[] };
export type TopicSourceRole = 'primary' | 'supporting' | 'reference' | 'visual_reference';
export type TopicDocumentSource = { documentId: string; documentVersionId: string; filename: string;
  role: TopicSourceRole; sequence: number; reviewStatus: string; documentStatus: string;
  libraryReviewState: string; unresolvedPageCount: number; unresolvedBlockCount: number;
  includedInRetrieval: boolean; usedByPublishedVersion: boolean; publishableBlockCount: number;
  visualAssetCount: number; selectedVisualCount: number; approvedVisualCount: number;
  pendingVisualCount: number; duplicateOf: string[] };
export type TopicReviewChecklist = { topicRef: string; topicTitle: string; remainingPages: number; remainingBlocks: number; notationBlocks: number; tableBlocks: number; visualBlocks: number; pendingVisualAssets: number; checks: { code: string; label: string; passed: boolean; message: string; href: string }[] };
export type TopicVisualAsset = { assetRef: string; documentId: string; documentVersionId: string; documentAssetId: string; filename: string; sourceRole: string; kind: string; page: number; printedPage?: string | null; boundingBox: Record<string, unknown>; extractedCaption: string; status: 'unselected'|'selected'|'approved'|'rejected'; caption: string; altText: string; contentUrl: string };
export type TopicLaunchReadiness = { topicRef: string; topicTitle: string; overallStatus: 'ready' | 'blocked'; checks: { code: string; label: string; passed: boolean; message: string; href: string }[] };
export type TopicRetrievalPreflight = { preflightRef: string; topicRef: string; contentVersion: number; passed: boolean; queries: string[]; results: { query: string; passed: boolean; reasons: string[]; page?: number | null; passage?: string | null; score: number }[]; createdAt: string };
