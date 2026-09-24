/** Learning-document metadata, extraction and processing contracts. */
export type LearningDocumentMetadata = {
  kind: 'textbook' | 'reference' | 'past_paper' | 'mark_scheme' | 'examiner_report';
  courseId: string;
  subjectId: string;
  title: string;
  sourceDocumentId?: string;
  edition?: string;
  year?: string;
  session?: string;
  component?: string;
  variant?: string;
  publisher?: string;
  isbn?: string;
  sourceUrl?: string;
};

export type Doc = {
  course: string;
  textbookId?: string;
  paperId?: string;
  legacy?: boolean;
  id: string;
  name: string;
  subject: string;
  kind: string;
  status: string;
  notes: string;
  processingProgress?: number;
  processingError?: string | null;
  edition?: string | null;
};
export type ExtractionBlock = {
  id: string;
  sequenceNumber: number;
  kind: string;
  text: string;
  latex?: string | null;
  boundingBox: Record<string, number>;
  method: string;
  confidence: number;
  needsReview: boolean;
  sourceAssetId?: string | null;
  metadata: Record<string, unknown>;
};
export type ExtractionPage = {
  id: string;
  pageNumber: number;
  widthPoints: number;
  heightPoints: number;
  renderAssetId: string;
  originalRenderAssetId?: string | null;
  printedPageLabel?: string | null;
  method: string;
  confidence: number;
  needsReview: boolean;
  metadata: Record<string, unknown>;
  blocks: ExtractionBlock[];
};
export type DocumentExtraction = {
  status: string;
  pages: ExtractionPage[];
};
export type DocumentJob = {
  stage: string;
  status: string;
  progress: number;
  attemptCount: number;
  extractionVersion: string;
  errorCode?: string | null;
  errorMessage?: string | null;
  result: Record<string, unknown>;
  queuedAt: string;
  startedAt?: string | null;
  completedAt?: string | null;
};
