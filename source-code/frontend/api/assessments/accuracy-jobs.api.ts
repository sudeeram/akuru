import { request } from '../core/client';
export type AccuracyReadiness = {
  questions: {
    number: string;
    status: string;
    visualBlockers: string[];
    reassessmentRequired: boolean;
    manualContentParts: string[];
    canReassess: boolean;
    analysisVersion: number;
  }[];
};
export type AccuracyJob = {
  id: string;
  number: string;
  status: string;
  errorCode?: string;
  result: { confidence?: number; model?: string; analysisVersion?: number };
};
const base = (id: string) => `admin/official-paper-reviews/${id}`;
export const getAccuracyReadiness = (id: string) =>
  request<AccuracyReadiness>(`${base(id)}/accuracy-readiness`);
export const getAccuracyJobs = (id: string) =>
  request<AccuracyJob[]>(`${base(id)}/accuracy-jobs`);
export const queueAccuracyJobs = (id: string, questions: unknown[]) =>
  request<AccuracyJob[]>(`${base(id)}/accuracy-jobs`, {
    method: 'POST',
    body: { questions },
  });
