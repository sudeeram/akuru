import type { State } from '@/api';
import type { PortalRole } from './routes';

/** Build a self-profile from the existing authorized portal response. */
export function profileDetails(data: State) {
  const role = data.user.role;
  if (!['admin', 'parent', 'student'].includes(role))
    throw new Error('Unsupported profile role');
  const student =
    role === 'student'
      ? data.students.find((item) => item.id === data.user.id)
      : undefined;
  const children =
    role === 'parent'
      ? data.students.filter((item) => item.parentId === data.user.id)
      : [];
  const account = data.accounts.find((item) => item.id === data.user.id);
  const initials =
    data.user.name
      .trim()
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => Array.from(part)[0])
      .join('')
      .toUpperCase() || 'A';
  return {
    role: role as PortalRole,
    roleName:
      role === 'admin'
        ? 'Administrator'
        : role === 'parent'
          ? 'Parent'
          : 'Student',
    initials,
    student,
    children,
    subjects: student
      ? data.subjects.filter((subject) => student.subjects.includes(subject.id))
      : [],
    lastLoginAt: student?.lastLoginAt ?? account?.lastLoginAt,
  };
}
