import { request } from '../core/client';
import type { Schemas } from '@/lib/generated/api-contract';
export type CommunitySettings = Schemas['CommunitySettings'];
export type CommunitySettingsDraft = Schemas['CommunitySettingsDraft'];
export type CommunityMember = Schemas['CommunityMember'];
export type CommunityPage = Schemas['CommunityPage'];
export type CommunityFeed = Schemas['CommunityFeed'];
export type CommunityReports = Schemas['CommunityReports'];
export type CommunityChoice = Schemas['CommunityChoice'];
export const getCommunitySettings = () =>
  request<CommunitySettings>('community/settings');
export const saveCommunitySettings = (body: CommunitySettingsDraft) =>
  request<CommunitySettings>('community/settings', { method: 'PATCH', body });
export const getCommunitySubjects = (course: string) =>
  request<{ subjects: CommunityChoice[] }>(
    `community/subjects?${new URLSearchParams({ course })}`,
  );
export const getCommunityMembers = (params: Record<string, string>) =>
  request<CommunityPage>(`community/members?${new URLSearchParams(params)}`);
export const followCommunityMember = (ref: string, following: boolean) =>
  request(`community/members/${encodeURIComponent(ref)}/follow`, {
    method: following ? 'DELETE' : 'POST',
  });
export const blockCommunityMember = (ref: string, remove = false) =>
  request(`community/members/${encodeURIComponent(ref)}/block`, {
    method: remove ? 'DELETE' : 'POST',
  });
export const getCommunityBlocks = (page: number) =>
  request<CommunityPage>(`community/blocks?page=${page}`);
export const getCommunityFeed = (page = 1) =>
  request<CommunityFeed>(`community/feed?page=${page}`);
export const readCommunityNotice = (ref: string, read: boolean) =>
  request(`community/notifications/${encodeURIComponent(ref)}`, {
    method: 'PATCH',
    body: { read },
  });
export const reportCommunityMember = (
  ref: string,
  reason: Schemas['ReportDraft']['reason'],
) =>
  request(`community/members/${encodeURIComponent(ref)}/report`, {
    method: 'POST',
    body: { reason },
  });
export const getCommunityReports = (status: string, page: number) =>
  request<CommunityReports>(
    `community/reports?${new URLSearchParams({ status, page: String(page) })}`,
  );
export const reviewCommunityReport = (
  ref: string,
  action: Schemas['ReportDecision']['action'],
) =>
  request(`community/reports/${encodeURIComponent(ref)}`, {
    method: 'PATCH',
    body: { action },
  });
