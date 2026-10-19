import type catalogue from '@/lib/avatar-catalogue.json';
export type AvatarField = keyof typeof catalogue.options;
export type AvatarConfig = { version: 1 } & {
  [Field in AvatarField]: keyof (typeof catalogue.options)[Field];
};
export type AvatarResponse = { avatar: AvatarConfig | null };
