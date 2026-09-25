import type { FlashcardMode } from '@/api';

export type PortalRole = 'admin' | 'parent' | 'student';

const roleViews: Record<PortalRole, Record<string, string>> = {
  admin: {
    today: '/admin', accounts: '/admin/accounts', library: '/admin/library',
    units: '/admin/textbooks', coverage: '/admin/coverage', questions: '/admin/questions',
    flashcards: '/admin/flashcards', blueprints: '/admin/blueprints',
    'ai-accounts': '/admin/ai-accounts', 'tutor-presets': '/admin/tutor-presets',
    'tutor-quotas': '/admin/tutor-quotas', 'tutor-history': '/admin/tutor-history',
    'assessment-audit': '/admin/assessment-audit', media: '/admin/media',
    evaluations: '/admin/evaluations', operations: '/admin/operations',
  },
  parent: {
    today: '/parent', students: '/parent/students', tutors: '/parent/tutors',
    'tutor-history': '/parent/tutor-history', library: '/parent/library',
    reviews: '/parent/reviews', assignments: '/parent/assignments', progress: '/parent/progress',
  },
  student: {
    today: '/student', subjects: '/student/subjects', tutors: '/student/tutors',
    'tutor-room': '/student/tutor-room', practice: '/student/practice', flashcards: '/flashcards',
    exams: '/student/exams', progress: '/student/progress', plan: '/student/study-plan',
  },
};

export const flashcardModes = ['review', 'difficult'] as const;
export const flashcardDifficulties = ['easy', 'difficult', 'mixed'] as const;

export type FlashcardRoute = {
  deckRef?: string;
  sessionRef?: string;
  position?: number;
  mode?: FlashcardMode;
  difficulty?: 'easy' | 'difficult' | 'mixed';
  count?: 20 | 30;
};

export function pathForView(role: PortalRole, view: string) {
  return roleViews[role][view] ?? roleViews[role].today;
}

export function viewForPath(role: PortalRole, pathname: string) {
  if (role === 'student' && pathname.startsWith('/flashcards')) return 'flashcards';
  const match = Object.entries(roleViews[role]).find(([, path]) => path === pathname);
  return match?.[0] ?? 'today';
}

export function roleAllowsPath(role: PortalRole, pathname: string) {
  if (pathname === '/' || pathname === '/login') return true;
  if (role === 'student' && pathname.startsWith('/flashcards')) return true;
  return Object.values(roleViews[role]).includes(pathname);
}

export function flashcardRoute(pathname: string, search: Record<string, unknown>): FlashcardRoute {
  const deck = pathname.match(/^\/flashcards\/decks\/([^/]+)(?:\/start)?$/);
  const session = pathname.match(/^\/flashcards\/sessions\/([^/]+)\/cards\/(\d+)$/);
  const rawMode = typeof search.mode === 'string' ? search.mode : undefined;
  const rawDifficulty = typeof search.difficulty === 'string' ? search.difficulty : undefined;
  const rawCount = Number(search.count);
  return {
    deckRef: deck ? decodeURIComponent(deck[1]) : undefined,
    sessionRef: session ? decodeURIComponent(session[1]) : undefined,
    position: session ? Math.max(1, Number(session[2])) : undefined,
    mode: flashcardModes.includes(rawMode as FlashcardMode) ? rawMode as FlashcardMode : undefined,
    difficulty: flashcardDifficulties.includes(rawDifficulty as typeof flashcardDifficulties[number]) ? rawDifficulty as typeof flashcardDifficulties[number] : undefined,
    count: rawCount === 20 || rawCount === 30 ? rawCount : undefined,
  };
}

export const flashcardPaths = {
  library: '/flashcards',
  deck: (deckRef: string) => `/flashcards/decks/${encodeURIComponent(deckRef)}`,
  start: (deckRef: string, mode: FlashcardMode, difficulty?: string, count: 20 | 30 = 20) =>
    `/flashcards/decks/${encodeURIComponent(deckRef)}/start?mode=${mode}${difficulty ? `&difficulty=${difficulty}` : ''}&count=${count}`,
  card: (sessionRef: string, position: number) =>
    `/flashcards/sessions/${encodeURIComponent(sessionRef)}/cards/${Math.max(1, position)}`,
};

export const applicationPaths = [
  '/', '/login', '/admin', '/admin/accounts', '/admin/library', '/admin/textbooks',
  '/admin/coverage', '/admin/questions', '/admin/flashcards', '/admin/blueprints',
  '/admin/ai-accounts', '/admin/tutor-presets', '/admin/tutor-quotas',
  '/admin/tutor-history', '/admin/assessment-audit', '/admin/media',
  '/admin/evaluations', '/admin/operations', '/parent', '/parent/students',
  '/parent/tutors', '/parent/tutor-history', '/parent/library', '/parent/reviews',
  '/parent/assignments', '/parent/progress', '/student', '/student/subjects',
  '/student/tutors', '/student/tutor-room', '/student/practice', '/student/exams',
  '/student/progress', '/student/study-plan', '/flashcards',
] as const;

export function isApplicationPath(pathname: string) {
  return (applicationPaths as readonly string[]).includes(pathname) ||
    /^\/flashcards\/decks\/[^/]+(?:\/start)?$/.test(pathname) ||
    /^\/flashcards\/sessions\/[^/]+\/cards\/\d+$/.test(pathname);
}
