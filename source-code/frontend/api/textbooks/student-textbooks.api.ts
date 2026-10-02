import { request } from '../core/client';

export type StudentTextbookVisual = {
  assetRef: string;
  caption: string;
  altText: string;
  contentUrl: string;
};
export type StudentTextbookPage = {
  ordinal: number;
  pageNumber: number;
  printedPage: string | null;
  imageUrl: string;
  sections: { kind: string; text: string }[];
  visuals: StudentTextbookVisual[];
};
export type StudentTextbookReference = {
  ordinal: number;
  filename: string;
  pages: { ordinal: number; pageNumber: number; printedPage: string; imageUrl: string }[];
};
export type StudentTextbookTopic = {
  topicRef: string;
  code: string;
  title: string;
  pageCount: number;
  contentVersion: number;
  publishedAt: string;
};
export type StudentTextbook = {
  textbookRef: string;
  subjectId: string;
  title: string;
  edition: string;
  publisher: string;
  groupLabel: 'unit' | 'module';
  structureVersion: number;
  structurePublishedAt: string;
  groups: { code: string; title: string; topics: StudentTextbookTopic[] }[];
};
export type StudentTextbookContent = {
  textbookRef: string;
  textbookTitle: string;
  subjectId: string;
  groupCode: string;
  groupTitle: string;
  topicRef: string;
  topicCode: string;
  topicTitle: string;
  contentVersion: number;
  publishedAt: string;
  pages: StudentTextbookPage[];
  visualReferences: StudentTextbookReference[];
  additionalVisuals: StudentTextbookVisual[];
};

export const getStudentTextbooks = () => request<{ textbooks: StudentTextbook[] }>('student/textbooks');
export const getStudentTextbookTopic = (bookRef: string, topicRef: string) =>
  request<StudentTextbookContent>(`student/textbooks/${encodeURIComponent(bookRef)}/topics/${encodeURIComponent(topicRef)}`);
