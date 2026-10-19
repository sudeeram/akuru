import { request } from '../core/client';
import type { AvatarConfig, AvatarResponse } from './avatar.types';
export const saveStudentAvatar = (avatar: AvatarConfig) =>
  request<AvatarResponse>('student/avatar', { method: 'PATCH', body: avatar });
export const resetStudentAvatar = () =>
  request<AvatarResponse>('student/avatar', { method: 'DELETE' });
