import type { FlashcardMode } from '@/api';

export type PortalRole = 'admin' | 'parent' | 'student';

const roleViews: Record<PortalRole, Record<string, string>> = {
  admin: {
    today: '/admin',
    accounts: '/admin/accounts',
    'community-reports': '/admin/community-reports',
    library: '/admin/exam-documents',
    units: '/admin/textbooks',
    coverage: '/admin/coverage',
    questions: '/admin/questions',
    flashcards: '/admin/flashcards',
    blueprints: '/admin/blueprints',
    'ai-accounts': '/admin/ai-accounts',
    'tutor-presets': '/admin/tutor-presets',
    'tutor-quotas': '/admin/tutor-quotas',
    'tutor-history': '/admin/tutor-history',
    'assessment-audit': '/admin/assessment-audit',
    media: '/admin/media',
    evaluations: '/admin/evaluations',
    operations: '/admin/operations',
    profile: '/admin/profile',
    security: '/admin/security',
  },
  parent: {
    today: '/parent',
    students: '/parent/students',
    tutors: '/parent/tutors',
    'tutor-history': '/parent/tutor-history',
    library: '/parent/library',
    reviews: '/parent/reviews',
    assignments: '/parent/assignments',
    progress: '/parent/progress',
    profile: '/parent/profile',
    security: '/parent/security',
  },
  student: {
    today: '/student',
    subjects: '/student/subjects',
    community: '/student/community',
    textbooks: '/student/textbooks',
    tutors: '/student/tutors',
    'tutor-room': '/student/tutor-room',
    practice: '/student/practice',
    flashcards: '/flashcards',
    exams: '/student/exams',
    progress: '/student/progress',
    plan: '/student/study-plan',
    profile: '/student/profile',
    security: '/student/security',
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
  return describeRoute(pathname)?.role === role
    ? describeRoute(pathname)!.view
    : 'today';
}

export function roleAllowsPath(role: PortalRole, pathname: string) {
  const route = describeRoute(pathname);
  return !!route && (route.role === 'public' || route.role === role);
}

export function flashcardRoute(
  pathname: string,
  search: Record<string, unknown>,
): FlashcardRoute {
  const deck = pathname.match(/^\/flashcards\/decks\/([^/]+)(?:\/start)?$/);
  const session = pathname.match(
    /^\/flashcards\/sessions\/([^/]+)\/cards\/(\d+)$/,
  );
  const rawMode = typeof search.mode === 'string' ? search.mode : undefined;
  const rawDifficulty =
    typeof search.difficulty === 'string' ? search.difficulty : undefined;
  const rawCount = Number(search.count);
  return {
    deckRef: deck ? decodeURIComponent(deck[1]) : undefined,
    sessionRef: session ? decodeURIComponent(session[1]) : undefined,
    position: session ? Math.max(1, Number(session[2])) : undefined,
    mode: flashcardModes.includes(rawMode as FlashcardMode)
      ? (rawMode as FlashcardMode)
      : undefined,
    difficulty: flashcardDifficulties.includes(
      rawDifficulty as (typeof flashcardDifficulties)[number],
    )
      ? (rawDifficulty as (typeof flashcardDifficulties)[number])
      : undefined,
    count: rawCount === 20 || rawCount === 30 ? rawCount : undefined,
  };
}

export const flashcardPaths = {
  library: '/flashcards',
  deck: (deckRef: string) => `/flashcards/decks/${encodeURIComponent(deckRef)}`,
  start: (
    deckRef: string,
    mode: FlashcardMode,
    difficulty?: string,
    count: 20 | 30 = 20,
  ) =>
    `/flashcards/decks/${encodeURIComponent(deckRef)}/start?mode=${mode}${difficulty ? `&difficulty=${difficulty}` : ''}&count=${count}`,
  card: (sessionRef: string, position: number) =>
    `/flashcards/sessions/${encodeURIComponent(sessionRef)}/cards/${Math.max(1, position)}`,
};

export const studentTextbookPaths = {
  library: '/student/textbooks',
  book: (bookRef: string) =>
    `/student/textbooks/${encodeURIComponent(bookRef)}`,
  topic: (bookRef: string, topicRef: string, page = 1) =>
    `/student/textbooks/${encodeURIComponent(bookRef)}/topics/${encodeURIComponent(topicRef)}?page=${Math.max(1, page)}`,
  visual: (bookRef: string, topicRef: string, source = 1, page = 1) =>
    `/student/textbooks/${encodeURIComponent(bookRef)}/topics/${encodeURIComponent(topicRef)}?view=visual&source=${Math.max(1, source)}&page=${Math.max(1, page)}`,
};

export function studentTextbookRoute(
  pathname: string,
  search: Record<string, unknown>,
) {
  const match = pathname.match(
    /^\/student\/textbooks(?:\/([^/]+)(?:\/topics\/([^/]+))?)?$/,
  );
  return {
    bookRef: match?.[1] ? decodeURIComponent(match[1]) : undefined,
    topicRef: match?.[2] ? decodeURIComponent(match[2]) : undefined,
    view: search.view === 'visual' ? ('visual' as const) : ('text' as const),
    source: Math.max(1, Number(search.source) || 1),
    page: Math.max(1, Number(search.page) || 1),
  };
}

export type RouteDefinition = {
  path: string;
  role: PortalRole | 'public';
  view: string;
  label: string;
};
const titles: Record<string, string> = {
  today: 'Overview',
  accounts: 'Accounts & enrolments',
  community: 'Community',
  'community-reports': 'Community reports',
  library: 'Exam Documents',
  units: 'Textbooks',
  coverage: 'Grade & term coverage',
  questions: 'Question mapping',
  flashcards: 'Flashcards',
  blueprints: 'Mock blueprints',
  'ai-accounts': 'OpenAI accounts',
  'tutor-presets': 'Tutor presets',
  'tutor-quotas': 'Tutor allowances',
  'tutor-history': 'Tutor history',
  'assessment-audit': 'Assessment audit',
  media: 'Visual media',
  evaluations: 'Evaluation gates',
  operations: 'Operations',
  profile: 'My profile',
  security: 'Account security',
  students: 'Children & courses',
  tutors: 'Tutors',
  reviews: 'Assessment reviews',
  assignments: 'Assignments',
  progress: 'Learning progress',
  subjects: 'My subjects',
  textbooks: 'Textbooks',
  'tutor-room': 'Tutor room',
  practice: 'Practice',
  exams: 'Mock exams',
  plan: 'Study plan',
};
export const staticApplicationRoutes: RouteDefinition[] = [
  { path: '/', role: 'public', view: 'login', label: 'Sign in' },
  { path: '/login', role: 'public', view: 'login', label: 'Sign in' },
  ...Object.entries(roleViews).flatMap(([role, views]) =>
    Object.entries(views).map(([view, path]) => ({
      path,
      role: role as PortalRole,
      view,
      label:
        role === 'parent' && view === 'library'
          ? 'Content library'
          : titles[view] || view,
    })),
  ),
  {
    path: '/admin/library',
    role: 'admin',
    view: 'library',
    label: 'Exam Documents',
  },
  {
    path: '/admin/textbooks/new',
    role: 'admin',
    view: 'units',
    label: 'Add textbook',
  },
  {
    path: '/admin/textbooks/review',
    role: 'admin',
    view: 'units',
    label: 'Textbook review queue',
  },
  ...[
    ['past-papers', 'Past papers'],
    ['mark-schemes', 'Marking schemes'],
    ['examiner-reports', 'Examiner reports'],
    ['references', 'Reference materials'],
  ].map(([segment, label]) => ({
    path: `/admin/exam-documents/${segment}`,
    role: 'admin' as const,
    view: 'library',
    label,
  })),
];
export const dynamicApplicationRoutes: RouteDefinition[] = [
  {
    path: '/admin/textbooks/$bookRef',
    role: 'admin',
    view: 'units',
    label: 'Manage textbook',
  },
  {
    path: '/admin/textbooks/$bookRef/topics/$topicRef',
    role: 'admin',
    view: 'units',
    label: 'Manage topic',
  },
  {
    path: '/admin/textbooks/review/$documentRef',
    role: 'admin',
    view: 'units',
    label: 'Review textbook document',
  },
  {
    path: '/admin/exam-documents/review/$paperId',
    role: 'admin',
    view: 'library',
    label: 'Official-paper review',
  },
  {
    path: '/flashcards/decks/$deckRef',
    role: 'student',
    view: 'flashcards',
    label: 'Flashcard deck',
  },
  {
    path: '/flashcards/decks/$deckRef/start',
    role: 'student',
    view: 'flashcards',
    label: 'Choose a review set',
  },
  {
    path: '/flashcards/sessions/$sessionRef/cards/$position',
    role: 'student',
    view: 'flashcards',
    label: 'Flashcard study',
  },
  {
    path: '/student/textbooks/$bookRef',
    role: 'student',
    view: 'textbooks',
    label: 'Textbook contents',
  },
  {
    path: '/student/textbooks/$bookRef/topics/$topicRef',
    role: 'student',
    view: 'textbooks',
    label: 'Read topic',
  },
];
export const applicationPaths = staticApplicationRoutes.map(
  (route) => route.path,
);
const validParameter = (name: string, value: string) => {
  if (name === 'position') return /^[1-9]\d{0,5}$/.test(value);
  if (name === 'paperId')
    return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(
      value,
    );
  if (name === 'bookRef') return /^book_[A-Za-z0-9_-]{1,150}$/.test(value);
  if (name === 'topicRef') return /^topic_[A-Za-z0-9_-]{1,150}$/.test(value);
  return /^[A-Za-z0-9_-]{1,160}$/.test(value);
};
export function describeRoute(
  pathname: string,
): (RouteDefinition & { params: Record<string, string> }) | undefined {
  const fixed = staticApplicationRoutes.find(
    (route) => route.path === pathname,
  );
  if (fixed) return { ...fixed, params: {} };
  const segments = pathname.split('/');
  for (const route of dynamicApplicationRoutes) {
    const expected = route.path.split('/');
    if (expected.length !== segments.length) continue;
    const params: Record<string, string> = {};
    const matches = expected.every((segment, index) => {
      if (!segment.startsWith('$')) return segment === segments[index];
      let value: string;
      try {
        value = decodeURIComponent(segments[index]);
      } catch {
        return false;
      }
      if (!validParameter(segment.slice(1), value)) return false;
      params[segment.slice(1)] = value;
      return true;
    });
    if (matches) return { ...route, params };
  }
  return undefined;
}
export function isApplicationPath(pathname: string) {
  return !!describeRoute(pathname);
}
export function routeBreadcrumbs(pathname: string) {
  const route = describeRoute(pathname);
  if (!route) return [];
  const crumbs: { label: string; path?: string }[] = [];
  const base =
    route.role === 'public' ? '/' : pathForView(route.role, route.view);
  if (base !== pathname)
    crumbs.push({
      label:
        route.role === 'public' ? 'AKURU' : titles[route.view] || 'Workspace',
      path: base,
    });
  if (route.params.bookRef && route.params.topicRef)
    crumbs.push({
      label: 'Textbook',
      path: `/${route.role}/textbooks/${route.params.bookRef}`,
    });
  if (route.params.documentRef)
    crumbs.push({ label: 'Review queue', path: '/admin/textbooks/review' });
  crumbs.push({ label: route.label });
  return crumbs;
}

/** Only presentation/context fields belong in URLs, never private drafts or credentials. */
export function workspaceSearch(search: Record<string, unknown>) {
  const result: Record<string, string> = {};
  const allowed = [
    'q',
    'course',
    'subject',
    'status',
    'kind',
    'learner',
    'grade',
    'term',
    'textbook',
    'record',
    'mode',
    'difficulty',
    'count',
    'view',
    'source',
    'page',
    'from',
    'days',
    'section',
    'filter',
  ];
  for (const key of allowed) {
    const value = search[key];
    if (
      (typeof value === 'string' || typeof value === 'number') &&
      String(value).length <= 200 &&
      !Array.from(String(value)).some(
        (character) => character.charCodeAt(0) < 32,
      )
    )
      result[key] = String(value);
  }
  if (result.mode && !flashcardModes.includes(result.mode as FlashcardMode))
    delete result.mode;
  if (
    result.difficulty &&
    !flashcardDifficulties.includes(
      result.difficulty as (typeof flashcardDifficulties)[number],
    )
  )
    delete result.difficulty;
  if (result.count && !['20', '30'].includes(result.count)) delete result.count;
  for (const key of ['page', 'source'])
    if (result[key] && !/^[1-9]\d{0,5}$/.test(result[key])) delete result[key];
  if (result.learner && !/^[A-Za-z0-9_-]{1,160}$/.test(result.learner))
    delete result.learner;
  return result;
}
