import catalogue from './avatar-catalogue.json';
import type { AvatarConfig, AvatarField } from '@/api/avatars/avatar.types';
export const avatarCatalogue = catalogue;
export const avatarPresets = catalogue.presets as AvatarConfig[];
export function parseAvatar(value: unknown): AvatarConfig | null {
  if (!value || typeof value !== 'object') return null;
  const record = value as Record<string, unknown>;
  const fields = Object.keys(catalogue.options) as AvatarField[];
  if (record.version !== 1 || Object.keys(record).length !== fields.length + 1)
    return null;
  for (const field of fields)
    if (
      typeof record[field] !== 'string' ||
      !Object.hasOwn(catalogue.options[field], record[field] as string)
    )
      return null;
  return record as AvatarConfig;
}
export function surpriseAvatar(): AvatarConfig {
  const next = {
    ...avatarPresets[Math.floor(Math.random() * avatarPresets.length)],
  };
  for (const field of Object.keys(catalogue.options) as AvatarField[]) {
    if (field === 'base') continue;
    const choices = Object.keys(catalogue.options[field]);
    Object.assign(next, {
      [field]: choices[Math.floor(Math.random() * choices.length)],
    });
  }
  return next;
}
