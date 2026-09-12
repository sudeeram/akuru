'use client';
/* React Compiler is not enabled here. Effects intentionally synchronise local form drafts and hash navigation. */
/* eslint-disable react/react-compiler */
import { useEffect, useState } from 'react';
import {
  ArrowRight,
  BookOpen,
  CalendarDays,
  Check,
  ChevronRight,
  ClipboardCheck,
  Clock3,
  LayoutDashboard,
  Library,
  LogOut,
  TrendingUp,
  Users,
  Sparkles,
  ShieldCheck,
} from 'lucide-react';
import {
  SidebarProvider,
  Sidebar,
  SidebarHeader,
  SidebarContent,
  SidebarFooter,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarInset,
  SidebarTrigger,
  useSidebar,
} from '@/components/ui/sidebar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  api,
  errorMessage,
  ApiError,
  type State,
  type Student,
} from '@/lib/api';
import { Heading, SubjectIcon } from '@/features/shared';
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

const studentNav = [
  ['today', 'Today', LayoutDashboard],
  ['subjects', 'My subjects', BookOpen],
  ['practice', 'Practice', ClipboardCheck],
  ['exams', 'Mock exams', Clock3],
  ['progress', 'My progress', TrendingUp],
  ['plan', 'Study plan', CalendarDays],
] as const;
const parentNav = [
  ['today', 'Family overview', LayoutDashboard],
  ['students', 'Children & courses', Users],
  ['library', 'Content library', Library],
  ['reviews', 'Assessment reviews', ClipboardCheck],
  ['assignments', 'Assignments', CalendarDays],
  ['progress', 'Learning progress', TrendingUp],
] as const;
const adminNav = [
  ['today', 'Admin overview', LayoutDashboard],
  ['accounts', 'Accounts & enrolments', Users],
  ['library', 'Documents & textbooks', Library],
  ['units', 'Textbook units', BookOpen],
  ['coverage', 'Grade & term coverage', CalendarDays],
  ['questions', 'Question mapping', ClipboardCheck],
] as const;
export default function Portal() {
  const [data, setData] = useState<State | null>(null),
    [loading, setLoading] = useState(true),
    [view, setView] = useState('today'),
    [error, setError] = useState(''),
    [notice, setNotice] = useState('');
  const [username, setUsername] = useState(''),
    [password, setPassword] = useState(''),
    [busy, setBusy] = useState(false),
    [selected, setSelected] = useState(''),
    [subject, setSubject] = useState('maths');
  usePortalTools(data?.user.id);
  async function refresh() {
    try {
      const next = await api('state');
      setData(next);
      if (next.user.role === 'student') setSelected(next.user.id);
      const allowed =
        next.user.role === 'admin'
          ? adminNav
          : next.user.role === 'parent'
            ? parentNav
            : studentNav;
      const candidate = location.hash.slice(1);
      if (!allowed.some((n) => n[0] === candidate)) setView('today');
    } catch (e: unknown) {
      if (e instanceof ApiError && e.status === 401) setData(null);
      else setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    void refresh();
    const update = () => {
      const candidate = location.hash.slice(1);
      if (
        [...studentNav, ...parentNav, ...adminNav].some(
          (n) => n[0] === candidate,
        )
      )
        setView(candidate);
    };
    update();
    window.addEventListener('hashchange', update);
    return () => window.removeEventListener('hashchange', update);
  }, []);
  const notify = (message: string) => {
    setNotice(message);
    setTimeout(() => setNotice(''), 4500);
  };
  const go = (next: string, s?: string) => {
    setView(next);
    location.hash = next;
    if (s) setSubject(s);
    setError('');
    window.scrollTo({ top: 0 });
  };
  async function login(e: React.SyntheticEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      await api('auth/login', { username, password });
      await refresh();
      setView('today');
      location.hash = 'today';
      setPassword('');
    } catch (e: unknown) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
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
            <label htmlFor="username">Username</label>
            <Input
              id="username"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
            <label htmlFor="password">Password</label>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
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
              {busy ? 'Signing in…' : 'Sign in'}
              <ArrowRight size={18} />
            </Button>
            <p className="fineprint">
              Accounts are created by an AKURU administrator. No external AI
              services are connected yet.
            </p>
          </form>
        </div>
      </div>
    );
  if (data.user.mustChangePassword)
    return <PasswordChange data={data} refresh={refresh} />;
  const parent = data.user.role === 'parent';
  const admin = data.user.role === 'admin';
  const child = data.students.find((s) => s.id === selected) ||
    data.students[0] || {
      id: '',
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
  const effectiveSubject = child.subjects.includes(subject)
    ? subject
    : child.subjects[0];
  const props = {
    data,
    child,
    subject: effectiveSubject,
    setSubject,
    refresh,
    notify,
    go,
    selected,
    setSelected,
  };
  return (
    <SidebarProvider
      style={{ '--sidebar-width': '244px' } as React.CSSProperties}
    >
      <Sidebar className="app-sidebar">
        <SidebarHeader>
          <div className="brand">
            <span className="brand-mark">A</span>AKURU
            <span className="brand-dot">●</span>
          </div>
          <div className="portal-label">
            {admin
              ? 'ADMIN SPACE'
              : parent
                ? 'PARENT SPACE'
                : 'MY LEARNING SPACE'}
          </div>
        </SidebarHeader>
        <SidebarContent>
          <PortalNavigation
            parent={parent}
            admin={admin}
            view={view}
            go={go}
            pending={
              data.attempts.filter((a) => a.status === 'needs-review').length
            }
          />
          <div className="sidebar-note">
            <Sparkles size={20} />
            <strong>
              {parent
                ? 'Small steps. Lasting growth.'
                : 'Curiosity looks good on you.'}
            </strong>
            <p>
              {parent
                ? 'Every child learns at their own pace. Make room for theirs.'
                : 'A question is always a good place to start.'}
            </p>
          </div>
        </SidebarContent>
        <SidebarFooter>
          <div className="account">
            <span className="avatar">
              {admin ? 'A' : parent ? 'P' : child.name[0]}
            </span>
            <div>
              <strong>
                {admin ? data.user.name : parent ? data.user.name : child.name}
              </strong>
              <small>
                {admin
                  ? 'Curriculum administrator'
                  : parent
                    ? 'Parent'
                    : `${child.grade} · ${child.term}`}
              </small>
            </div>
            <Button
              variant="ghost"
              aria-label="Sign out"
              onClick={async () => {
                await api('auth/logout', {});
                setData(null);
                setView('today');
              }}
            >
              <LogOut size={18} />
            </Button>
          </div>
        </SidebarFooter>
      </Sidebar>
      <SidebarInset className="app-inset">
        <header className="topbar">
          <div className="breadcrumb">
            <SidebarTrigger />
            <span>
              {admin
                ? 'Admin portal'
                : parent
                  ? 'Family portal'
                  : 'Student portal'}
            </span>
            <ChevronRight size={14} />
            <strong>
              {nav.find((n) => n[0] === view)?.[1] || 'Learning workspace'}
            </strong>
          </div>
          <div className="topbar-right">
            <span className="local-dot" />
            AKURU portal
            <span className="top-avatar">
              {admin ? 'A' : parent ? 'P' : child.name[0]}
            </span>
          </div>
        </header>
        <div id="main-content" className="main-content">
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
          {admin ? (
            <AdminWorkspace
              key={view}
              data={data}
              view={view}
              refresh={refresh}
              notify={notify}
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
              <ParentHome data={data} go={go} choose={setSelected} />
            ) : (
              <StudentHome data={data} child={child} go={go} />
            )
          ) : view === 'subjects' && !parent ? (
            <Subjects {...props} />
          ) : view === 'practice' && !parent ? (
            <Practice {...props} />
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
        <footer className="app-footer">
          <span>AKURU · A little progress, every day.</span>
          <span>iGCSE · Admin-reviewed learning material</span>
        </footer>
      </SidebarInset>
    </SidebarProvider>
  );
}

function PasswordChange({ data, refresh }: { data: State; refresh: () => Promise<void> }) {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  return (
    <div className="login-page">
      <div className="login-story">
        <div className="brand"><span className="brand-mark">A</span>AKURU<span className="brand-dot">●</span></div>
        <div><div className="akuru-bot-scene"><div className="bot-sticker bot-checklist" /></div><h1>Protect your<br /><em>learning space.</em></h1></div>
      </div>
      <div className="login-form-wrap">
        <form className="login-form" onSubmit={async (event) => {
          event.preventDefault();
          if (newPassword !== confirmPassword) return setError('The new passwords do not match.');
          setBusy(true); setError('');
          try {
            await api('auth/change-password', { currentPassword, newPassword });
            await refresh();
          } catch (caught) { setError(errorMessage(caught)); }
          finally { setBusy(false); }
        }}>
          <span className="pill"><ShieldCheck size={14} /> FIRST SIGN-IN</span>
          <h2>Choose your own password.</h2>
          <p>Welcome, {data.user.name}. Replace the temporary password before continuing.</p>
          <label htmlFor="current-password">Temporary password</label>
          <Input id="current-password" type="password" autoComplete="current-password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required />
          <label htmlFor="new-password">New password · at least 12 characters</label>
          <Input id="new-password" type="password" autoComplete="new-password" minLength={12} value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required />
          <label htmlFor="confirm-password">Confirm new password</label>
          <Input id="confirm-password" type="password" autoComplete="new-password" minLength={12} value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required />
          {error && <div className="error" role="alert">{error}</div>}
          <Button type="submit" className="primary login-submit" disabled={busy}>{busy ? 'Saving…' : 'Save password'}<ArrowRight size={18} /></Button>
        </form>
      </div>
    </div>
  );
}
function StudentHome({
  data,
  child,
  go,
}: {
  data: State;
  child: Student;
  go: (v: string, s?: string) => void;
}) {
  const weekStart = new Date();
  weekStart.setHours(0, 0, 0, 0);
  weekStart.setDate(weekStart.getDate() - ((weekStart.getDay() + 6) % 7));
  const attempts = data.attempts.filter(
    (a) => Date.parse(a.createdAt) >= weekStart.getTime(),
  );
  const pending = data.assignments.filter((a) => !a.completed);
  return (
    <>
      <Heading
        eyebrow={`${child.grade.toUpperCase()} · YOUR LEARNING JOURNEY`}
        title={`Hello, ${child.name}. Ready to explore?`}
      >
        A fresh question. A new connection. A little more confidence.
      </Heading>
      <div className="dashboard-grid">
        <div>
          <section className="focus-card">
            <div className="focus-copy">
              <span className="focus-label">
                <span />
                TODAY’S FOCUS
              </span>
              <h2>
                Small steps.
                <br />
                Bigger understanding.
              </h2>
              <p>
                Start with a question and see where
                <br />
                your curiosity takes you.
              </p>
              <Button
                className="white-button"
                onClick={() => go('practice', 'maths')}
              >
                Let’s practise
                <ArrowRight size={18} />
              </Button>
            </div>
            <div
              className="akuru-focus-bot"
              aria-label="AKURU BOT studying with a book"
            />
          </section>
          <div className="section-heading">
            <h2>My subjects</h2>
            <button className="text-button" onClick={() => go('subjects')}>
              View all
              <ArrowRight size={15} />
            </button>
          </div>
          <div className="subject-grid">
            {data.subjects
              .filter((s) => child.subjects.includes(s.id))
              .map((s) => (
                <button
                  className="subject-card"
                  key={s.id}
                  onClick={() => go('subjects', s.id)}
                >
                  <div className="spread">
                    <SubjectIcon subject={s} />
                    <ArrowRight size={17} />
                  </div>
                  <h3>{s.name}</h3>
                  <p>{s.topic}</p>
                  <div className="subject-meta">
                    <span>{child.courses[s.id]?.level}</span>
                    <span>
                      {data.questions.filter((q) => q.subject === s.id).length}{' '}
                      demo topics
                    </span>
                  </div>
                </button>
              ))}
          </div>
        </div>
        <aside className="right-rail">
          <section className="panel">
            <div className="section-heading compact">
              <h3>Your week, so far</h3>
              <TrendingUp size={19} />
            </div>
            <div className="week-days">
              {'MTWTFSS'.split('').map((d, i) => (
                <span
                  key={i}
                  className={
                    i === (new Date().getDay() + 6) % 7 ? 'current' : ''
                  }
                >
                  {d}
                  <i>{i === (new Date().getDay() + 6) % 7 ? '•' : ''}</i>
                </span>
              ))}
            </div>
            <div className="stats-pair">
              <div>
                <strong>{attempts.length}</strong>
                <span>Questions tried</span>
              </div>
              <div>
                <strong>{new Set(attempts.map((a) => a.subject)).size}</strong>
                <span>Subjects explored</span>
              </div>
            </div>
            <p className="muted small">Every attempt is a step forward.</p>
          </section>
          <section className="panel">
            <div className="section-heading compact">
              <h3>Up next</h3>
              <CalendarDays size={18} />
            </div>
            {pending.length ? (
              pending.slice(0, 3).map((a) => (
                <button
                  key={a.id}
                  className="up-next"
                  onClick={() => {
                    sessionStorage.setItem('akuru-next-question', a.questionId);
                    go('practice', a.subject);
                  }}
                >
                  <span className="mini-icon">
                    <BookOpen size={17} />
                  </span>
                  <span>
                    <strong>{a.title}</strong>
                    <small>Due {a.due}</small>
                  </span>
                  <ChevronRight size={16} />
                </button>
              ))
            ) : (
              <p className="muted">
                You’re all caught up. Choose a subject to keep exploring.
              </p>
            )}
            <button className="text-button full" onClick={() => go('plan')}>
              Open study plan
              <ArrowRight size={15} />
            </button>
          </section>
          <section className="tip-card">
            <span className="eyebrow">A GOOD LEARNING HABIT</span>
            <h3>Explain it out loud.</h3>
            <p>
              If you can teach an idea to someone else, you’re starting to make
              it your own.
            </p>
            <span className="tip-line" />
          </section>
        </aside>
      </div>
    </>
  );
}
function ParentHome({
  data,
  go,
  choose,
}: {
  data: State;
  go: (v: string) => void;
  choose: (id: string) => void;
}) {
  const pending = data.attempts.filter((a) => a.status === 'needs-review');
  return (
    <>
      <Heading
        eyebrow="A SPACE FOR EVERY LEARNER"
        title="Your family, moving forward."
        action={
          <Button className="primary" onClick={() => go('assignments')}>
            Assign practice
            <ArrowRight size={17} />
          </Button>
        }
      >
        Different grades. Different strengths. Their own paths.
      </Heading>
      <div className="metric-grid">
        {(
          [
            ['Learners', data.students.length, Users],
            ['Questions attempted', data.attempts.length, ClipboardCheck],
            ['Awaiting review', pending.length, BookOpen],
            [
              'Active assignments',
              data.assignments.filter((a) => !a.completed).length,
              CalendarDays,
            ],
          ] as [string, number, typeof Users][]
        ).map(([label, value, Icon]) => (
          <div className="metric panel" key={label}>
            <Icon size={21} />
            <strong>{value}</strong>
            <span>{label}</span>
          </div>
        ))}
      </div>
      <div className="section-heading">
        <h2>Your learners</h2>
        <button className="text-button" onClick={() => go('students')}>
          View courses
          <ArrowRight size={16} />
        </button>
      </div>
      <div className="learner-grid">
        {data.students.map((s, i) => {
          const attempts = data.attempts.filter((a) => a.studentId === s.id);
          return (
            <article className="panel learner-card" key={s.id}>
              <div className="spread">
                <span className={`big-avatar shade-${i}`}>{s.name[0]}</span>
                <span className="pill">{s.grade}</span>
              </div>
              <h2>{s.name}</h2>
              <p>{s.subjects.length} subjects · Individual learning plan</p>
              <div className="learner-subjects">
                {s.subjects.map((id) => (
                  <span key={id}>
                    {data.subjects.find((x) => x.id === id)?.name}
                  </span>
                ))}
              </div>
              <div className="learner-summary">
                <strong>{attempts.length}</strong> questions tried{' '}
                <span>·</span>{' '}
                {attempts.filter((a) => a.status === 'needs-review').length} to
                review
              </div>
              <Button
                variant="outline"
                className="full"
                onClick={() => {
                  choose(s.id);
                  go('progress');
                }}
              >
                View {s.name}’s progress
                <ArrowRight size={16} />
              </Button>
            </article>
          );
        })}
      </div>
      <div className="section-heading">
        <h2>A little attention goes a long way</h2>
      </div>
      <div className="two-cols">
        <button className="panel action-card" onClick={() => go('reviews')}>
          <span className="subject-icon orange">
            <ClipboardCheck />
          </span>
          <div>
            <h3>
              {pending.length
                ? `${pending.length} answers ready for your review`
                : 'Ready for their next discovery'}
            </h3>
            <p>Give personal feedback on written answers and working.</p>
          </div>
          <ArrowRight />
        </button>
        <button className="panel action-card" onClick={() => go('library')}>
          <span className="subject-icon blue">
            <Library />
          </span>
          <div>
            <h3>Open your learning library</h3>
            <p>Read resources prepared by your Admin.</p>
          </div>
          <ArrowRight />
        </button>
      </div>
    </>
  );
}

function PortalNavigation({
  parent,
  admin,
  view,
  go,
  pending,
}: {
  parent: boolean;
  admin: boolean;
  view: string;
  go: (view: string) => void;
  pending: number;
}) {
  const { setOpenMobile } = useSidebar();
  const nav = admin ? adminNav : parent ? parentNav : studentNav;
  return (
    <SidebarMenu>
      {nav.map(([id, label, Icon]) => (
        <SidebarMenuItem key={id}>
          <SidebarMenuButton
            onClick={() => {
              go(id);
              setOpenMobile(false);
            }}
            isActive={view === id}
            className="nav-item"
          >
            <Icon size={19} />
            <span>{label}</span>
            {id === 'reviews' && pending > 0 && (
              <b className="nav-count">{pending}</b>
            )}
          </SidebarMenuButton>
        </SidebarMenuItem>
      ))}
    </SidebarMenu>
  );
}
