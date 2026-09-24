/** Versioned curriculum coverage operations for Admin workflows. */
import { request } from '../core/client';
import type { CurriculumPlan, CurriculumPlanPeriod } from './curriculum.types';

export const getCurriculumPlan = (subjectId: string) =>
  request<CurriculumPlan>(`admin/curriculum-plans/${subjectId}`);
export const saveCurriculumPlan = (subjectId: string, periods: CurriculumPlanPeriod[]) =>
  request<CurriculumPlan>(`admin/curriculum-plans/${subjectId}`, { method: 'POST', body: { periods } });
export const createCurriculumPlanDraft = (subjectId: string) =>
  request<CurriculumPlan>(`admin/curriculum-plans/${subjectId}/draft`, { method: 'POST', body: {} });
export const publishCurriculumPlan = (subjectId: string, confirmPublishedChanges = false) =>
  request<CurriculumPlan>(`admin/curriculum-plans/${subjectId}/publish`, {
    method: 'POST',
    body: { confirmSubject: true, confirmTextbook: true, confirmPublishedChanges },
  });
