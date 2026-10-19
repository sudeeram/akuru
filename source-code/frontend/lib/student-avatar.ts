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
  const avatar = { ...record } as AvatarConfig;
  if (!catalogue.hairByBase[avatar.base].includes(avatar.hair))
    avatar.hair = avatarPresets.find(
      (preset) => preset.base === avatar.base,
    )!.hair;
  return avatar;
}
export function avatarOptions(field: AvatarField, base: AvatarConfig['base']) {
  return Object.entries(catalogue.options[field]).filter(
    ([value]) => field !== 'hair' || catalogue.hairByBase[base].includes(value),
  );
}
export function surpriseAvatar(base?: AvatarConfig['base']): AvatarConfig {
  const next = {
    ...(avatarPresets.find((preset) => preset.base === base) ||
      avatarPresets[Math.floor(Math.random() * avatarPresets.length)]),
  };
  for (const field of Object.keys(catalogue.options) as AvatarField[]) {
    if (field === 'base') continue;
    const choices = avatarOptions(field, next.base).map(([value]) => value);
    Object.assign(next, {
      [field]: choices[Math.floor(Math.random() * choices.length)],
    });
  }
  return next;
}
