import type { ReactNode } from 'react';
import type { PortalRole } from '@/lib/routes';

export function PublicLayout({ children }: { children: ReactNode }) {
  return <div data-layout="public">{children}</div>;
}

function AuthenticatedRoleLayout({ role, children }: { role: PortalRole; children: ReactNode }) {
  return <div data-layout={`${role}-portal`}>{children}</div>;
}

export const AdminLayout = ({ children }: { children: ReactNode }) =>
  <AuthenticatedRoleLayout role="admin">{children}</AuthenticatedRoleLayout>;
export const ParentLayout = ({ children }: { children: ReactNode }) =>
  <AuthenticatedRoleLayout role="parent">{children}</AuthenticatedRoleLayout>;
export const StudentLayout = ({ children }: { children: ReactNode }) =>
  <AuthenticatedRoleLayout role="student">{children}</AuthenticatedRoleLayout>;
