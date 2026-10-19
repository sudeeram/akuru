'use client';
/* React Compiler is not enabled here. Effects intentionally synchronise authentication, legacy links and document focus. */
/* eslint-disable react/react-compiler */
import { useEffect, useRef, useState, useSyncExternalStore } from 'react';
import Link from 'next/link';
import { QueryClientProvider, useQuery } from '@tanstack/react-query';
import {
  RouterProvider,
  useNavigate,
  useRouterState,
} from '@tanstack/react-router';
import {
  ArrowRight,
  BookOpen,
  CalendarDays,
  Check,
  ClipboardCheck,
  Clock3,
  LayoutDashboard,
  Library,
  LogOut,
  TrendingUp,
  Users,
  ShieldCheck,
  Palette,
  KeyRound,
  ScanSearch,
  Images,
  FlaskConical,
  Activity,
  Bot,
  MessageCircle,
  Gauge,
  Layers3,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { api, getState, errorMessage, ApiError, type State } from '@/api';
import { PortalShell } from '@/components/portal/portal-shell';
import { ParentHome, StudentHome } from '@/features/portal-home';
import {
  Subjects,
  Practice,
  Exams,
  ProgressView,
  Plan,
} from '@/features/student';
import { Reviews, Assignments } from '@/features/parent';
import { AdminWorkspace, FamilyCourses, FamilyLibrary } from '@/features/admin';
import { usePortalTools } from '@/features/use-portal-tools';
import { TutorProfiles } from '@/features/tutor-profiles';
import { TutorSessions } from '@/features/tutor-sessions';
import { TutorHistory } from '@/features/tutor-history';
import { StudentFlashcards } from '@/features/flashcards';
import { StudentTextbooks } from '@/features/student-textbooks';
import { AccountSecurity } from '@/features/account-security';
import {
  AdminLayout,
  ParentLayout,
  PublicLayout,
  StudentLayout,
} from '@/components/portal-layouts';
import { createAkuruRouter } from '@/lib/app-router';
import { clearPrivateQueryState, queryClient } from '@/lib/query-client';
import { queryKeys } from '@/lib/query-keys';
import {
  flashcardRoute,
  studentTextbookRoute,
  pathForView,
  roleAllowsPath,
  viewForPath,
  describeRoute,
  routeBreadcrumbs,
  type PortalRole,
} from '@/lib/routes';

const studentNav = [
  ['today', 'Today', LayoutDashboard],
  ['subjects', 'My subjects', BookOpen],
  ['textbooks', 'Textbooks', Library],
  ['tutors', 'My tutors', Bot],
  ['tutor-room', 'Tutor room', MessageCircle],
  ['practice', 'Practice', ClipboardCheck],
  ['flashcards', 'Flashcards', Layers3],
  ['exams', 'Mock exams', Clock3],
  ['progress', 'My progress', TrendingUp],
  ['plan', 'Study plan', CalendarDays],
  ['security', 'Account security', KeyRound],
] as const;
const parentNav = [
  ['today', 'Family overview', LayoutDashboard],
  ['students', 'Children & courses', Users],
  ['tutors', 'Tutors', Bot],
  ['tutor-history', 'Tutor history', ShieldCheck],
  ['library', 'Content library', Library],
  ['reviews', 'Assessment reviews', ClipboardCheck],
  ['assignments', 'Assignments', CalendarDays],
  ['progress', 'Learning progress', TrendingUp],
  ['security', 'Account security', KeyRound],
] as const;
const adminNav = [
  ['today', 'Admin overview', LayoutDashboard],
  ['accounts', 'Accounts & enrolments', Users],
  ['library', 'Exam Documents', Library],
  ['units', 'Textbooks', BookOpen],
  ['coverage', 'Grade & term coverage', CalendarDays],
  ['questions', 'Question mapping', ClipboardCheck],
  ['flashcards', 'Flashcard release', Layers3],
  ['blueprints', 'Mock blueprints', Clock3],
  ['ai-accounts', 'OpenAI accounts', KeyRound],
  ['tutor-presets', 'Tutor presets', Bot],
  ['tutor-quotas', 'Tutor allowances', Gauge],
  ['tutor-history', 'Tutor history & safety', ShieldCheck],
  ['assessment-audit', 'Assessment audit', ScanSearch],
  ['media', 'Visual media', Images],
  ['evaluations', 'Evaluation gates', FlaskConical],
  ['operations', 'Operations', Activity],
  ['security', 'Account security', KeyRound],
] as const;
const router = createAkuruRouter(Portal);

export default function AkuruApplication() {
  const browserReady = useSyncExternalStore(
    () => () => undefined,
    () => true,
    () => false,
  );
  if (!browserReady)
    return (
      <div className="loading">
        <span className="brand-mark">A</span>
        <p>Opening your learning space…</p>
      </div>
    );
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}

export function Portal() {
  const navigate = useNavigate();
  const location = useRouterState({ select: (state) => state.location });
  const [signedOut, setSignedOut] = useState(false);
  const [sessionExpiryMessage, setSessionExpiryMessage] = useState('');
  const lastInteractionAt = useRef(Date.now());
  const authQuery = useQuery({
    queryKey: queryKeys.auth.state,
    queryFn: getState,
    enabled: !signedOut,
    retry: false,
  });
  const data = authQuery.data ?? null;
  const loading = authQuery.isPending && !signedOut;
  const [error, setError] = useState(''),
    [notice, setNotice] = useState('');
  const [username, setUsername] = useState(''),
    [password, setPassword] = useState(''),
    [busy, setBusy] = useState(false),
    [selected, setSelected] = useState(''),
    [subject, setSubject] = useState('maths');
  usePortalTools(data?.user.id);
  async function refresh() {
    const result = await authQuery.refetch();
    if (result.error) throw result.error;
  }
  useEffect(() => {
    if (
      authQuery.error &&
      !(authQuery.error instanceof ApiError && authQuery.error.status === 401)
    )
      setError(errorMessage(authQuery.error));
  }, [authQuery.error]);
  useEffect(() => {
    const rememberInteraction = () => {
      lastInteractionAt.current = Date.now();
    };
    const activityEvents = [
      'pointerdown',
      'keydown',
      'touchstart',
      'input',
    ] as const;
    activityEvents.forEach((eventName) =>
      window.addEventListener(eventName, rememberInteraction, {
        passive: true,
      }),
    );
    const expire = () => {
      const recentlyActive =
        Date.now() - lastInteractionAt.current <= 5 * 60 * 1000;
      setSessionExpiryMessage(
        recentlyActive
          ? 'Your AKURU session expired for security. Please sign in again to continue.'
          : 'Your session expired while you were away. Please sign in again to continue.',
      );
      setSignedOut(true);
      void clearPrivateQueryState().finally(() =>
        navigate({ to: '/login', replace: true }),
      );
    };
    window.addEventListener('akuru:unauthorized', expire);
    return () => {
      window.removeEventListener('akuru:unauthorized', expire);
      activityEvents.forEach((eventName) =>
        window.removeEventListener(eventName, rememberInteraction),
      );
    };
  }, [navigate]);
  const role = data?.user.role as PortalRole | undefined;
  const view = role ? viewForPath(role, location.pathname) : 'today';
  useEffect(() => {
    if (!data || !role) return;
    if (data.user.role === 'student' && !selected) setSelected(data.user.id);
    const legacy = window.location.hash.slice(1);
    const legacyKnown = [...studentNav, ...parentNav, ...adminNav].some(
      ([id]) => id === legacy,
    );
    if (legacyKnown) {
      window.history.replaceState(
        null,
        '',
        window.location.pathname + window.location.search,
      );
      void navigate({ to: pathForView(role, legacy) });
      return;
    }
    if (role === 'admin' && location.pathname === '/admin/library') {
      void navigate({ to: '/admin/exam-documents', replace: true });
      return;
    }
    if (!roleAllowsPath(role, location.pathname))
      void navigate({ to: pathForView(role, 'today'), replace: true });
    else if (location.pathname === '/' || location.pathname === '/login')
      void navigate({ to: pathForView(role, 'today'), replace: true });
  }, [data, role, location.pathname, navigate, selected]);
  useEffect(() => {
    if (!role) {
      document.title = 'Sign in · AKURU';
      return;
    }
    const roleNav =
      role === 'admin' ? adminNav : role === 'parent' ? parentNav : studentNav;
    const activeView = viewForPath(role, location.pathname);
    const label =
      describeRoute(location.pathname)?.label ??
      roleNav.find(([id]) => id === activeView)?.[1] ??
      'Learning workspace';
    document.title = `${label} · AKURU`;
    window.requestAnimationFrame(() =>
      document.getElementById('main-content')?.focus(),
    );
  }, [role, location.pathname]);
  const notify = (message: string) => {
    setNotice(message);
    setTimeout(() => setNotice(''), 4500);
  };
  const navigateTo = (to: string, replace = false) => {
    const withinFlashcardSession =
      location.pathname.startsWith('/flashcards/sessions/') &&
      to.startsWith('/flashcards/sessions/');
    const withinTextbookReader =
      location.pathname.startsWith('/student/textbooks') &&
      to.startsWith('/student/textbooks');
    const proceed = () => {
      if (!withinFlashcardSession && !withinTextbookReader)
        window.dispatchEvent(new Event('akuru:navigation'));
      void navigate({ to, replace });
    };
    const guard = new CustomEvent('akuru:before-navigation', {
      cancelable: true,
      detail: { to, proceed },
    });
    if (window.dispatchEvent(guard)) proceed();
  };
  const go = (next: string, s?: string) => {
    if (role) {
      const params = new URLSearchParams();
      const requested = String(location.search.learner || '');
      const learner =
        data?.students.find((item) => item.accountRef === requested) ||
        data?.students.find((item) => item.id === selected) ||
        data?.students[0];
      if (role === 'parent' && learner?.accountRef)
        params.set('learner', learner.accountRef);
      const chosen = s || String(location.search.subject || subject);
      if (learner?.subjects.includes(chosen)) params.set('subject', chosen);
      navigateTo(pathForView(role, next) + (params.size ? `?${params}` : ''));
    }
    setError('');
    window.scrollTo({ top: 0 });
  };
  async function login(e: React.SyntheticEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      await api('auth/login', { username, password });
      await clearPrivateQueryState();
      setSignedOut(false);
      setSessionExpiryMessage('');
      const loginState = await authQuery.refetch();
      if (!loginState.data)
        throw (
          loginState.error ?? new Error('AKURU could not load your account.')
        );
      const next = loginState.data;
      const nextRole = next.user.role as PortalRole;
      const intended =
        roleAllowsPath(nextRole, location.pathname) &&
        !['/', '/login'].includes(location.pathname)
          ? `${location.pathname}${location.searchStr}`
          : pathForView(nextRole, 'today');
      navigateTo(intended, true);
      setPassword('');
    } catch (e: unknown) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }
  function submitLoginOnEnter(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key !== 'Enter' || e.nativeEvent.isComposing || busy) return;
    e.preventDefault();
    e.currentTarget.form?.requestSubmit();
  }
  if (loading)
    return (
      <div className="loading">
        <span className="brand-mark">A</span>
        <p>Opening your learning space…</p>
      </div>
    );
  if (!data)
    return (
      <PublicLayout>
        <div className="login-page">
          <div className="login-story">
            <div className="brand">
              <span className="brand-mark">A</span>AKURU
              <span className="brand-dot">●</span>
            </div>
            <div>
              <div
                className="akuru-bot-scene"
                aria-label="AKURU BOT learning companions"
              >
                <div className="bot-sticker bot-curious" />
                <div className="bot-sticker bot-reader" />
                <div className="bot-sticker bot-checklist" />
              </div>
              <div className="eyebrow">A LITTLE PROGRESS, EVERY DAY</div>
              <h1>
                Big discoveries.
                <br />
                One step
                <br />
                <em>at a time.</em>
              </h1>
              <p>
                A space for your family to ask questions,
                <br />
                build understanding and grow in confidence.
              </p>
              <div className="login-subjects">
                <span>∑</span>
                <span>⚗</span>
                <span>Aa</span>
                <span>⌘</span>
              </div>
            </div>
            <span className="login-footer">YOUR OWN PATH TO UNDERSTANDING</span>
          </div>
          <div className="login-form-wrap">
            <form className="login-form" onSubmit={login}>
              <span className="pill">
                <ShieldCheck size={14} /> SECURE FAMILY PORTAL
              </span>
              <h2>Welcome back.</h2>
              <p>Sign in to your own learning space.</p>
              {sessionExpiryMessage && (
                <output className="session-expiry-message">
                  {sessionExpiryMessage}
                </output>
              )}
              <label htmlFor="username">Username</label>
              <Input
                id="username"
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                onKeyDown={submitLoginOnEnter}
                required
              />
              <label htmlFor="password">Password</label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={submitLoginOnEnter}
                required
              />
              {error && (
                <div className="error" role="alert">
                  {error}
                  {authQuery.error &&
                    !(
                      authQuery.error instanceof ApiError &&
                      authQuery.error.status === 401
                    ) && (
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => void authQuery.refetch()}
                      >
                        Retry connection
                      </Button>
                    )}
                </div>
              )}
              <Button
                type="submit"
                className="primary login-submit"
                disabled={busy}
              >
                {busy ? 'Signing in…' : 'Sign in'}
                <ArrowRight size={18} />
              </Button>
              <p className="fineprint">
                Accounts are created by an AKURU administrator. Sign in to
                access your assigned learning resources.
              </p>
            </form>
          </div>
        </div>
      </PublicLayout>
    );
  if (data.user.mustChangePassword)
    return (
      <PublicLayout>
        <PasswordChange data={data} refresh={refresh} />
      </PublicLayout>
    );
  const parent = data.user.role === 'parent';
  const admin = data.user.role === 'admin';
  const RoleLayout = admin
    ? AdminLayout
    : parent
      ? ParentLayout
      : StudentLayout;
  const child = data.students.find(
    (s) => s.accountRef === location.search.learner,
  ) ||
    data.students.find((s) => s.id === selected) ||
    data.students[0] || {
      id: '',
      username: '',
      name: 'No learners',
      initial: '',
      grade: '',
      level: 'iGCSE',
      term: '',
      parentId: '',
      subjects: [],
      courses: {},
    };
  const nav = admin ? adminNav : parent ? parentNav : studentNav;
  const requestedSubject =
    typeof location.search.subject === 'string'
      ? location.search.subject
      : subject;
  const effectiveSubject = child.subjects.includes(requestedSubject)
    ? requestedSubject
    : child.subjects[0];
  const changeContext = (learnerId: string, nextSubject?: string) => {
    const learner = data.students.find((item) => item.id === learnerId);
    if (!learner) return;
    const proceed = () => {
      setSelected(learner.id);
      const params = new URLSearchParams(location.searchStr);
      if (parent) params.set('learner', learner.accountRef);
      const chosen = nextSubject || effectiveSubject;
      if (chosen && learner.subjects.includes(chosen)) {
        params.set('subject', chosen);
        setSubject(chosen);
      } else params.delete('subject');
      void navigate({
        to: location.pathname,
        search: Object.fromEntries(params),
        replace: true,
      });
    };
    const guard = new CustomEvent('akuru:before-navigation', {
      cancelable: true,
      detail: { to: location.pathname, proceed },
    });
    if (window.dispatchEvent(guard)) proceed();
  };
  const chooseLearner = (id: string) => changeContext(id);
  const chooseSubject = (id: string) => changeContext(child.id, id);
  const props = {
    data,
    child,
    subject: effectiveSubject,
    setSubject: chooseSubject,
    refresh,
    notify,
    go,
    selected,
    setSelected: chooseLearner,
  };
  return (
    <RoleLayout>
      <PortalShell
        context={
          admin ? 'Admin portal' : parent ? 'Family portal' : 'Student portal'
        }
        title={
          describeRoute(location.pathname)?.label ??
          nav.find((n) => n[0] === view)?.[1] ??
          'Learning workspace'
        }
        breadcrumbs={routeBreadcrumbs(location.pathname)}
        onNavigatePath={navigateTo}
        focusAvailable={
          !admin &&
          !parent &&
          [
            'practice',
            'exams',
            'flashcards',
            'textbooks',
            'tutor-room',
          ].includes(view)
        }
        workspaceContext={
          !admin &&
          view !== 'security' &&
          child.id && (
            <section
              className="workspace-context"
              aria-label="Learning context"
            >
              {parent && (
                <label>
                  Learner
                  <select
                    value={child.id}
                    onChange={(event) => chooseLearner(event.target.value)}
                  >
                    {data.students.map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.name} · {item.grade}
                      </option>
                    ))}
                  </select>
                </label>
              )}
              {child.subjects.length > 0 && (
                <label>
                  Subject
                  <select
                    value={effectiveSubject || ''}
                    onChange={(event) => chooseSubject(event.target.value)}
                  >
                    {child.subjects.map((id) => (
                      <option key={id} value={id}>
                        {data.subjects.find((item) => item.id === id)?.name ||
                          id}
                      </option>
                    ))}
                  </select>
                </label>
              )}
              <small>
                {child.grade} · {child.term}
              </small>
            </section>
          )
        }
        active={view}
        onNavigate={go}
        items={[
          ...nav.map(([id, label, icon]) => ({
            id,
            label,
            icon,
            group:
              id === 'security'
                ? 'Account'
                : admin
                  ? ['today', 'operations', 'evaluations'].includes(id)
                    ? 'Overview & operations'
                    : [
                          'accounts',
                          'ai-accounts',
                          'tutor-presets',
                          'tutor-quotas',
                        ].includes(id)
                      ? 'People & tutors'
                      : 'Learning & content'
                  : ['today', 'progress', 'plan'].includes(id)
                    ? 'Overview'
                    : 'Learning',
            badge:
              id === 'reviews'
                ? data.attempts.filter((a) => a.status === 'needs-review')
                    .length
                : undefined,
          })),
          ...(admin
            ? [
                {
                  id: 'ui-features',
                  label: 'UI features',
                  icon: Palette,
                  group: 'Design system',
                  href: '/ui-features',
                },
              ]
            : []),
        ]}
        actions={
          admin ? (
            <Link href="/ui-features" className="ak-return">
              <Palette size={16} /> UI features
            </Link>
          ) : undefined
        }
        account={
          <>
            <span className="ak-account">
              <span className="ak-avatar">{data.user.name[0]}</span>
              <span>
                {data.user.name}
                <small>
                  {admin ? 'Administrator' : parent ? 'Parent' : child.grade}
                </small>
              </span>
            </span>
            <Button
              variant="ghost"
              size="icon"
              aria-label="Sign out"
              onClick={async () => {
                const proceed = async () => {
                  await api('auth/logout', {});
                  setSignedOut(true);
                  await clearPrivateQueryState();
                  window.dispatchEvent(new Event('akuru:navigation'));
                  await navigate({ to: '/login', replace: true });
                };
                const guard = new CustomEvent('akuru:before-navigation', {
                  cancelable: true,
                  detail: { to: '/login', proceed: () => void proceed() },
                });
                if (window.dispatchEvent(guard)) await proceed();
              }}
            >
              <LogOut size={18} />
            </Button>
          </>
        }
      >
        <div className="main-content">
          {error && (
            <div className="error" role="alert">
              {error}
            </div>
          )}
          {notice && (
            <output className="toast">
              <Check size={18} />
              {notice}
            </output>
          )}
          {view === 'security' ? (
            <AccountSecurity notify={notify} />
          ) : admin ? (
            <AdminWorkspace
              key={view}
              data={data}
              view={view}
              refresh={refresh}
              notify={notify}
              pathname={location.pathname}
              search={location.searchStr}
              navigate={navigateTo}
            />
          ) : !child.id ? (
            <section className="panel">
              <h2>No children linked yet</h2>
              <p>
                Ask an Admin to create a child account linked to your parent
                account.
              </p>
            </section>
          ) : view === 'today' ? (
            parent ? (
              <ParentHome
                data={data}
                child={child}
                go={go}
                choose={chooseLearner}
              />
            ) : (
              <StudentHome data={data} child={child} go={go} />
            )
          ) : view === 'subjects' && !parent ? (
            <Subjects {...props} />
          ) : view === 'textbooks' && !parent ? (
            <StudentTextbooks
              actorRef={data.user.id}
              subjects={data.subjects}
              route={studentTextbookRoute(location.pathname, location.search)}
              navigate={navigateTo}
            />
          ) : view === 'tutors' ? (
            <TutorProfiles data={data} notify={notify} />
          ) : view === 'tutor-history' && parent ? (
            <TutorHistory notify={notify} />
          ) : view === 'tutor-room' && !parent ? (
            <TutorSessions notify={notify} />
          ) : view === 'practice' && !parent ? (
            <Practice {...props} />
          ) : view === 'flashcards' && !parent ? (
            <StudentFlashcards
              actorRef={data.user.id}
              route={flashcardRoute(location.pathname, location.search)}
              navigate={navigateTo}
            />
          ) : view === 'exams' && !parent ? (
            <Exams {...props} />
          ) : view === 'plan' && !parent ? (
            <Plan {...props} />
          ) : view === 'progress' ? (
            <ProgressView {...props} />
          ) : view === 'students' && parent ? (
            <FamilyCourses data={data} />
          ) : view === 'library' && parent ? (
            <FamilyLibrary data={data} />
          ) : view === 'reviews' && parent ? (
            <Reviews {...props} />
          ) : view === 'assignments' && parent ? (
            <Assignments {...props} />
          ) : null}
        </div>
      </PortalShell>
    </RoleLayout>
  );
}

function PasswordChange({
  data,
  refresh,
}: {
  data: State;
  refresh: () => Promise<void>;
}) {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  return (
    <div className="login-page">
      <div className="login-story">
        <div className="brand">
          <span className="brand-mark">A</span>AKURU
          <span className="brand-dot">●</span>
        </div>
        <div>
          <div className="akuru-bot-scene">
            <div className="bot-sticker bot-checklist" />
          </div>
          <h1>
            Protect your
            <br />
            <em>learning space.</em>
          </h1>
        </div>
      </div>
      <div className="login-form-wrap">
        <form
          className="login-form"
          onSubmit={async (event) => {
            event.preventDefault();
            if (newPassword !== confirmPassword)
              return setError('The new passwords do not match.');
            setBusy(true);
            setError('');
            try {
              await api('auth/change-password', { newPassword });
              await refresh();
            } catch (caught) {
              setError(errorMessage(caught));
            } finally {
              setBusy(false);
            }
          }}
        >
          <span className="pill">
            <ShieldCheck size={14} /> FIRST SIGN-IN
          </span>
          <h2>Choose your own password.</h2>
          <p>
            Welcome, {data.user.name}. Replace the temporary password before
            continuing.
          </p>
          <label htmlFor="new-password">
            New password · at least 12 characters
          </label>
          <Input
            id="new-password"
            type="password"
            autoComplete="new-password"
            minLength={12}
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
          />
          <label htmlFor="confirm-password">Confirm new password</label>
          <Input
            id="confirm-password"
            type="password"
            autoComplete="new-password"
            minLength={12}
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />
          {error && (
            <div className="error" role="alert">
              {error}
            </div>
          )}
          <Button
            type="submit"
            className="primary login-submit"
            disabled={busy}
          >
            {busy ? 'Saving…' : 'Save password'}
            <ArrowRight size={18} />
          </Button>
        </form>
      </div>
    </div>
  );
}
