/** Aggregate portal state and shared presentation contracts. */
import type { Attempt, Exam } from '../assessments/assessments.types';
import type { MasteryGroup, ImprovementRecommendation, TopicMastery } from '../mastery/mastery.types';
import type { Doc } from '../documents/documents.types';

export type Lesson = { explanation: string; points: string[]; hints: string[] };
export type UiFeaturesAccess = {
  allowed: true;
  user: { name: string; role: 'admin' };
};

export type Subject = {
  id: string;
  name: string;
  symbol: string;
  color: string;
  topic: string;
  topics: string[];
  course: string;
};

export type Student = {
  accountRef: string;
  lastLoginAt?: string | null;
  parentId: string;
  username: string;
  term: string;
  progression: { grade: string; term: string }[];
  needsConfiguration?: boolean;
  id: string;
  name: string;
  initial: string;
  grade: string;
  level: string;
  subjects: string[];
  courses: Record<string, { level: string; syllabus: string }>;
};
export type Question = {
  topicRefs?: string[];
  course?: string;
  id: string;
  subject: string;
  topic: string;
  title: string;
  prompt: string;
  marks: number;
  type: string;
  unit?: string;
  diagram: string;
  source: string;
  assetIds?: string[];
  equations?: string[];
  assessmentId?: string;
};

export type EducationalMedia = {
  id: string; subjectId: string; topicId: string; sourceChunkId: string; kind: string; title: string;
  altText: string; prompt: string; promptVersion: string; parameters: Record<string, unknown>;
  sourceManifest: { documentTitle?: string; topicCode?: string; page?: number }[]; provider: string;
  model: string; responseId?: string | null; contentType: string; status: string; reviewNotes: string;
  createdAt: string; reviewedAt?: string | null; contentUrl: string;
};
export type MediaSource = { id: string; subjectId: string; topicRef: string; topicCode: string; topicTitle: string; groupCode: string; documentTitle: string; page: number; excerpt: string };
export type Assignment = {
  id: string;
  studentId: string;
  subject: string;
  title: string;
  due: string;
  questionId: string;
  completed: boolean;
};

export type State = {
  catalog: {
    courses: string[];
    activeCourses: string[];
    grades: string[];
    terms: string[];
    kinds: string[];
    progressionPairs: { grade: string; term: string }[];
  };
  accounts: { id: string; publicRef: string; username: string; name: string; role: string; lastLoginAt?: string | null }[];
  drafts: Record<string, string>;
  user: {
    id: string;
    username: string;
    name: string;
    role: string;
    mustChangePassword: boolean;
  };
  subjects: Subject[];
  questions: Question[];
  students: Student[];
  attempts: Attempt[];
  assignments: Assignment[];
  documents: Doc[];
  exams: Exam[];
  assessmentBlueprints: { id: string; name: string; subjectId: string; grade: number; term: number; targetMarks: number; durationMinutes: number; questionCount: number; skills: string[]; difficultyProfile: Record<string, number>; status: string }[];
  officialPapers: { id: string; subjectId: string; title: string; questionCount: number; marks: number }[];
  reviews: {
    id: string;
    studentId: string;
    feedback: string;
    createdAt: string;
  }[];
  plans: Record<
    string,
    {
      id: string;
      studentId: string;
      version: number;
      updatedAt: string;
      generationReason: 'evidence' | 'request';
      items: {
        id: string;
        subject: string;
        topic: string;
        topicRef: string;
        topicCode: string;
        topicTitle: string;
        groupLabel: string;
        groupCode: string;
        groupTitle: string;
        activityType: string;
        minutes: number;
        reason: string;
        source: string;
        sourceUrl: string;
        successCondition: string;
        scheduledFor: string;
        status: string;
      }[];
    }
  >;
  mastery: Record<string, TopicMastery[]>;
  masteryGroups?: Record<string, MasteryGroup[]>;
  recommendations: Record<string, ImprovementRecommendation[]>;
};
export type BankQuestion = Question & {
  paperId: string;
  number: string;
  status: string;
  topicRefs: string[];
  explanation: string;
  points: string[];
  hints: string[];
  answer: number | null;
};
