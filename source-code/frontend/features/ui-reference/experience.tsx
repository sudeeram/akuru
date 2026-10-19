'use client';
import { CountBadge } from '@/components/portal/badges';

import Link from 'next/link';
import { useEffect, useId, useRef, useState, type ReactNode } from 'react';
import {
  Activity,
  ArrowRight,
  Bell,
  BookOpen,
  CalendarDays,
  Check,
  ClipboardCheck,
  FileText,
  GraduationCap,
  Grid2X2,
  LayoutDashboard,
  List,
  Palette,
  PanelsTopLeft,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Users,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  PortalShell,
  type PortalNavItem,
} from '@/components/portal/portal-shell';
import {
  ActivityTimeline,
  AssignmentList,
  ChildSwitcher,
  DashboardCard,
  DashboardSkeleton,
  EmptyState,
  MetricCard,
  PageHeader,
  StatusPill,
  StudentSummaryCard,
  SubjectProgressCard,
} from '@/components/portal/dashboard-widgets';
import { demoAssignments, demoDocuments, demoLearners } from './fixtures';

type PreviewRole = 'Parent' | 'Student' | 'Admin';
type PreviewState =
  | 'populated'
  | 'one-child'
  | 'no-child'
  | 'empty'
  | 'overdue'
  | 'loading'
  | 'error';
const sections: PortalNavItem[] = [
  {
    id: 'ui-overview',
    label: 'Dashboard previews',
    icon: LayoutDashboard,
    group: 'Workspace',
  },
  {
    id: 'ui-layouts',
    label: 'Layouts & navigation',
    icon: PanelsTopLeft,
    group: 'Workspace',
  },
  {
    id: 'ui-learning',
    label: 'Learning widgets',
    icon: GraduationCap,
    group: 'Patterns',
  },
  {
    id: 'ui-people',
    label: 'People & profiles',
    icon: Users,
    group: 'Patterns',
  },
  {
    id: 'ui-data',
    label: 'Data & workflows',
    icon: FileText,
    group: 'Patterns',
  },
  {
    id: 'ui-feedback',
    label: 'Forms & feedback',
    icon: SlidersHorizontal,
    group: 'Patterns',
  },
  {
    id: 'ui-catalogue',
    label: 'Component catalogue',
    icon: Palette,
    group: 'Design system',
  },
];

export function UiFeaturesExperience({
  userName,
  children,
}: {
  userName: string;
  children: ReactNode;
}) {
  const detailTrigger = useRef<HTMLElement | null>(null);
  const [active, setActive] = useState('ui-overview');
  const [role, setRole] = useState<PreviewRole>('Parent');
  const [scenario, setScenario] = useState<PreviewState>('populated');
  const [selected, setSelected] = useState('maya');
  const [period, setPeriod] = useState('current');
  const [detail, setDetail] = useState<{
    title: string;
    description: string;
  } | null>(null);
  const [read, setRead] = useState<string[]>([]);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const learner =
    demoLearners.find((child) => child.id === selected) ?? demoLearners[0];
  const current = scenario === 'one-child' ? demoLearners[0] : learner;
  const noActivity = scenario === 'empty';
  const activity = noActivity
    ? [0, 0, 0, 0, 0, 0, 0]
    : period === 'current'
      ? current.activity
      : current.previous;
  const assignments = noActivity
    ? []
    : demoAssignments
        .filter((item) => item.learner === current.id)
        .map((item) =>
          scenario === 'overdue'
            ? { ...item, status: 'Overdue', due: '15 Oct 2026' }
            : item,
        );
  const pending = assignments.filter(
    (item) => item.status === 'Awaiting review',
  );
  const openDetail = (title: string, description: string) => {
    detailTrigger.current = document.activeElement as HTMLElement;
    setDetail({ title, description });
  };
  useEffect(() => {
    const restoreAnchor = () => {
      const id = window.location.hash.slice(1);
      const target =
        document.getElementById(id) ??
        (id.startsWith('ui-catalog-')
          ? document.getElementById('ui-catalogue')
          : null);
      if (!target) return;
      setActive(id.startsWith('ui-catalog-') ? 'ui-catalogue' : id);
      target.scrollIntoView({ block: 'start' });
    };
    restoreAnchor();
    window.addEventListener('hashchange', restoreAnchor);
    return () => window.removeEventListener('hashchange', restoreAnchor);
  }, []);
  const jump = (id: string) => {
    window.history.replaceState(window.history.state, '', `#${id}`);
    setActive(id);
    document.getElementById(id)?.scrollIntoView({ block: 'start' });
  };
  const notices = [
    {
      id: 'n1',
      title: 'Chemistry is ready for review',
      detail: 'A sample textbook has finished processing.',
    },
    {
      id: 'n2',
      title: 'A little feedback goes a long way',
      detail: 'Maya has an English assessment awaiting review.',
    },
  ];
  return (
    <PortalShell
      preview
      items={sections}
      active={active}
      onNavigate={jump}
      context="UI reference"
      title="Design workspace"
      account={
        <span className="ak-account">
          <span className="ak-avatar">{userName[0]}</span>
          <span>
            {userName}
            <small>Administrator</small>
          </span>
        </span>
      }
      actions={
        <>
          <Link className="ak-return" href="/admin">
            Admin portal <ArrowRight size={15} />
          </Link>
          <Sheet>
            <SheetTrigger
              render={
                <Button
                  variant="outline"
                  size="icon"
                  aria-label={`Sample notifications, ${notices.length - read.length} unread`}
                />
              }
            >
              <Bell size={18} />
              <CountBadge
                count={notices.length - read.length}
                label="unread sample notifications"
              />
            </SheetTrigger>
            <SheetContent className="ak-detail-sheet">
              <SheetHeader>
                <SheetTitle>Sample notifications</SheetTitle>
                <SheetDescription>
                  Demo only. Read states reset when you leave this page.
                </SheetDescription>
              </SheetHeader>
              <div className="ak-sheet-body">
                <Button
                  variant="outline"
                  onClick={() => setUnreadOnly(!unreadOnly)}
                >
                  {unreadOnly ? 'Show all' : 'Show unread'}
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => setRead(notices.map((item) => item.id))}
                >
                  Mark all read
                </Button>
                {notices
                  .filter((item) => !unreadOnly || !read.includes(item.id))
                  .map((item) => (
                    <div className="ak-notice" key={item.id}>
                      <strong>{item.title}</strong>
                      <p>{item.detail}</p>
                      <Button
                        variant="ghost"
                        disabled={read.includes(item.id)}
                        onClick={() => setRead([...read, item.id])}
                      >
                        {read.includes(item.id) ? 'Read' : 'Mark read'}
                      </Button>
                    </div>
                  ))}
                {unreadOnly && read.length === notices.length && (
                  <EmptyState
                    title="All caught up"
                    description="No unread sample notifications."
                  />
                )}
              </div>
            </SheetContent>
          </Sheet>
        </>
      }
      footer={
        <>
          <span>AKURU design workspace · Sample data only</span>
          <span>PreSkool-inspired · Built with AKURU components</span>
        </>
      }
    >
      <div className="ak-reference">
        <section id="ui-overview" className="ak-section">
          <PageHeader
            eyebrow="AKURU DESIGN WORKSPACE"
            title="A clearer view of every learning journey."
            description="Explore the next AKURU experience, one thoughtful detail at a time."
          />
          <div className="ak-preview-controls">
            <span className="ak-demo-badge">
              <Sparkles size={14} /> Interactive preview · Sample data
            </span>
            <label className="ak-field">
              <span>Preview state</span>
              <select
                value={scenario}
                onChange={(e) => setScenario(e.target.value as PreviewState)}
              >
                <option value="populated">Populated · two learners</option>
                <option value="one-child">One learner</option>
                <option value="no-child">No linked learners</option>
                <option value="empty">No activity</option>
                <option value="overdue">Overdue work</option>
                <option value="loading">Loading</option>
                <option value="error">Error</option>
              </select>
            </label>
          </div>
          <Tabs
            value={role}
            onValueChange={(value) => setRole(value as PreviewRole)}
          >
            <TabsList
              className="ak-role-tabs"
              aria-label="Dashboard preview role"
            >
              {(['Parent', 'Student', 'Admin'] as const).map((value) => (
                <TabsTrigger value={value} key={value}>
                  {value} dashboard
                </TabsTrigger>
              ))}
            </TabsList>
            {(['Parent', 'Student', 'Admin'] as const).map((value) => (
              <TabsContent value={value} key={value}>
                {scenario === 'loading' ? (
                  <DashboardSkeleton />
                ) : scenario === 'error' ? (
                  <DashboardCard title="Dashboard unavailable">
                    <EmptyState
                      error
                      title="We couldn’t load this overview"
                      description="Your work is safe. Try loading the preview again."
                      action={
                        <Button onClick={() => setScenario('populated')}>
                          Try again
                        </Button>
                      }
                    />
                  </DashboardCard>
                ) : scenario === 'no-child' && value !== 'Admin' ? (
                  <DashboardCard title="Your learning space">
                    <EmptyState
                      title="No learners linked yet"
                      description="An administrator can link a learner to your family account."
                      action={
                        <Button
                          variant="outline"
                          onClick={() => setScenario('populated')}
                        >
                          Show linked-learner example
                        </Button>
                      }
                    />
                  </DashboardCard>
                ) : value === 'Admin' ? (
                  <AdminPreview empty={noActivity} onOpen={openDetail} />
                ) : (
                  <>
                    <div className="ak-dashboard-heading">
                      <div>
                        <h2>
                          {value === 'Parent'
                            ? 'Your family, moving forward.'
                            : `Welcome back, ${current.name.split(' ')[0]}.`}
                        </h2>
                        <p>
                          {value === 'Parent'
                            ? 'A little attention today. A little more confidence tomorrow.'
                            : 'Your next step is waiting. Let’s make it count.'}
                        </p>
                      </div>
                      {value === 'Parent' && (
                        <ChildSwitcher
                          learners={
                            scenario === 'one-child'
                              ? [demoLearners[0]]
                              : demoLearners
                          }
                          value={current.id}
                          onChange={setSelected}
                        />
                      )}
                    </div>
                    <StudentSummaryCard
                      name={current.name}
                      grade={current.grade}
                      term={current.term}
                      subjects={current.subjects}
                      action={
                        <Button
                          variant="outline"
                          onClick={() =>
                            openDetail(
                              `${current.name}’s learning profile`,
                              `${current.grade} · ${current.term}. Enrolled in ${current.subjects.join(', ')}. This is a synthetic learner profile.`,
                            )
                          }
                        >
                          View profile <ArrowRight size={16} />
                        </Button>
                      }
                    />
                    <div className="ak-metrics">
                      <MetricCard
                        label="Questions attempted"
                        value={activity.reduce((sum, count) => sum + count, 0)}
                        detail={
                          period === 'current'
                            ? '12–18 October · sample week'
                            : '5–11 October · sample week'
                        }
                        icon={ClipboardCheck}
                      />
                      <MetricCard
                        label="Enrolled subjects"
                        value={current.subjects.length}
                        detail="Current learning programme"
                        icon={BookOpen}
                        tone="violet"
                      />
                      <MetricCard
                        label="Assignments open"
                        value={
                          assignments.filter(
                            (item) => item.status !== 'Awaiting review',
                          ).length
                        }
                        detail="Across enrolled subjects"
                        icon={CalendarDays}
                        tone="amber"
                      />
                      <MetricCard
                        label="Awaiting review"
                        value={pending.length}
                        detail="Feedback from a parent"
                        icon={Check}
                        tone="green"
                      />
                    </div>
                    {value === 'Student' && (
                      <div className="ak-next-step">
                        <div>
                          <span className="ak-eyebrow">YOUR NEXT STEP</span>
                          <h2>
                            {assignments[0]?.title ??
                              'Start with a little practice'}
                          </h2>
                          <p>
                            {assignments[0]?.subject ?? current.subjects[0]} ·
                            Build confidence, one question at a time.
                          </p>
                          <Button
                            onClick={() =>
                              openDetail(
                                'Practice preview',
                                'In the live student portal, this action opens the assigned question. No practice session is started from this design preview.',
                              )
                            }
                          >
                            Continue studying <ArrowRight size={16} />
                          </Button>
                        </div>
                        <div
                          className="bot-sticker bot-checklist"
                          aria-hidden="true"
                        />
                      </div>
                    )}
                    <div className="ak-dashboard-columns">
                      <div className="ak-stack">
                        <DashboardCard
                          title="Weekly learning activity"
                          description="Practice attempts per day"
                          action={
                            <label className="ak-field">
                              <span className="sr-only">Activity week</span>
                              <select
                                aria-label="Activity week"
                                value={period}
                                onChange={(e) => setPeriod(e.target.value)}
                              >
                                <option value="current">12–18 Oct</option>
                                <option value="previous">5–11 Oct</option>
                              </select>
                            </label>
                          }
                        >
                          <ActivityChart values={activity} />
                          <p className="ak-chart-summary">
                            {activity.reduce((a, b) => a + b, 0)} attempts ·{' '}
                            {activity.filter((count) => count > 0).length}{' '}
                            active days. Sample data.
                          </p>
                        </DashboardCard>
                        <DashboardCard
                          title="Subject performance"
                          description="Sample marked-question scores · not a mastery estimate"
                        >
                          <div className="ak-subject-grid">
                            {current.subjects.map((subject, index) => (
                              <SubjectProgressCard
                                key={subject}
                                title={subject}
                                description="Marked practice"
                                value={
                                  noActivity ? null : current.scores[index]
                                }
                                label="Marks achieved"
                                onOpen={() =>
                                  openDetail(
                                    subject,
                                    noActivity
                                      ? 'No marked practice yet. Scores become available after a marked attempt.'
                                      : `${current.scores[index]}% of available marks in the sample set. This does not measure curriculum mastery.`,
                                  )
                                }
                              />
                            ))}
                          </div>
                        </DashboardCard>
                      </div>
                      <div className="ak-stack">
                        <DashboardCard
                          title="Assignments & reviews"
                          description={`${current.name.split(' ')[0]}’s next steps`}
                        >
                          <AssignmentList
                            items={assignments}
                            onOpen={(item) =>
                              openDetail(
                                item.title,
                                `${item.subject} · Due ${item.due} · ${item.status}. This preview demonstrates the detail panel only.`,
                              )
                            }
                          />
                        </DashboardCard>
                        <DashboardCard title="Recent activity">
                          <ActivityTimeline
                            items={
                              noActivity
                                ? []
                                : [
                                    {
                                      id: '1',
                                      title: `${current.subjects[0]} practice completed`,
                                      detail: `${current.name} explored a new question.`,
                                      date: '17 Oct · Sample activity',
                                    },
                                    {
                                      id: '2',
                                      title: 'Study plan updated',
                                      detail: `Next steps prepared for ${current.name.split(' ')[0]}.`,
                                      date: '16 Oct · Sample activity',
                                    },
                                  ]
                            }
                          />
                        </DashboardCard>
                      </div>
                    </div>
                  </>
                )}
              </TabsContent>
            ))}
          </Tabs>
        </section>
        <section id="ui-layouts" className="ak-section">
          <PageHeader
            level={2}
            title="Layouts & navigation"
            description="One familiar structure across every learning workspace."
          />
          <div className="ak-layout-examples">
            <DashboardCard
              title="Grouped navigation"
              description="Learning, people and operations each have their place."
            >
              <p>
                Use the sidebar search to find a section, or collapse the
                sidebar for more working space. On smaller screens, open the
                menu in the header.
              </p>
            </DashboardCard>
            <DashboardCard
              title="Clear context"
              description="Know where you are and what comes next."
            >
              <p>
                Breadcrumbs identify the workspace. Page headings describe the
                task. One primary action gives each screen a clear next step.
              </p>
            </DashboardCard>
          </div>
        </section>
        <section id="ui-learning" className="ak-section">
          <PageHeader
            level={2}
            title="Learning widgets"
            description="Small, useful summaries that lead to the next action."
          />
          <div className="ak-subject-grid">
            {['Algebra', 'Atomic structure', 'Reading skills'].map(
              (title, i) => (
                <SubjectProgressCard
                  key={title}
                  title={title}
                  description={`${i + 2} of 8 sample activities completed`}
                  value={((i + 2) / 8) * 100}
                  label="Activity completion"
                  onOpen={() =>
                    openDetail(
                      title,
                      'A sample learning path: explore the topic, try a question, review feedback, then revisit what needs practice.',
                    )
                  }
                />
              ),
            )}
          </div>
        </section>
        <section id="ui-people" className="ak-section">
          <PeoplePreview onOpen={openDetail} />
        </section>
        <section id="ui-data" className="ak-section">
          <PageHeader
            level={2}
            title="Data & workflows"
            description="Find the right resource, understand its status, and open its details."
          />
          <DocumentTable onOpen={openDetail} />
        </section>
        <section id="ui-feedback" className="ak-section">
          <FeedbackPreview />
        </section>
        <div className="ak-legacy-gallery">{children}</div>
      </div>
      <Sheet
        open={!!detail}
        onOpenChange={(open) => {
          if (!open) setDetail(null);
        }}
      >
        <SheetContent className="ak-detail-sheet" finalFocus={detailTrigger}>
          <SheetHeader>
            <SheetTitle>{detail?.title ?? 'Preview details'}</SheetTitle>
            <SheetDescription>
              AKURU design preview · Sample data
            </SheetDescription>
          </SheetHeader>
          <div className="ak-sheet-body">
            <span className="ak-icon ak-tone-blue">
              <BookOpen />
            </span>
            <p>{detail?.description}</p>
            <div className="ak-inline-note">
              Changes in this preview are local to this page.
            </div>
            <Button variant="outline" onClick={() => setDetail(null)}>
              Close details
            </Button>
          </div>
        </SheetContent>
      </Sheet>
    </PortalShell>
  );
}

function ActivityChart({ values }: { values: number[] }) {
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  return (
    <>
      <div className="ak-chart" aria-hidden="true">
        <ResponsiveContainer width="100%" height={190}>
          <BarChart
            accessibilityLayer={false}
            data={values.map((attempts, index) => ({
              day: days[index],
              attempts,
            }))}
            margin={{ left: -20, right: 5, top: 12 }}
          >
            <CartesianGrid vertical={false} stroke="#e7edf4" />
            <XAxis
              dataKey="day"
              tickLine={false}
              axisLine={false}
              tick={{ fill: '#58677b', fontSize: 12 }}
            />
            <YAxis
              allowDecimals={false}
              tickLine={false}
              axisLine={false}
              tick={{ fill: '#58677b', fontSize: 12 }}
            />
            <Tooltip />
            <Bar
              dataKey="attempts"
              fill="#386bd6"
              radius={[5, 5, 0, 0]}
              maxBarSize={30}
              isAnimationActive={false}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="sr-only">
        {days
          .map((day, index) => `${day}: ${values[index]} attempts`)
          .join('; ')}
      </p>
    </>
  );
}
function AdminPreview({
  empty,
  onOpen,
}: {
  empty: boolean;
  onOpen: (title: string, description: string) => void;
}) {
  return (
    <>
      <div className="ak-dashboard-heading">
        <div>
          <h2>Everything in its place.</h2>
          <p>A clear view of the work that keeps learning moving.</p>
        </div>
        <span className="ak-demo-badge">18 October 2026 · Demo</span>
      </div>
      <div className="ak-metrics">
        <MetricCard
          label="Learning resources"
          value={empty ? 0 : demoDocuments.length}
          detail="Sample content library"
          icon={BookOpen}
        />
        <MetricCard
          label="Awaiting review"
          value={empty ? 0 : 2}
          detail="Ready for an administrator"
          icon={ClipboardCheck}
          tone="amber"
        />
        <MetricCard
          label="Processing"
          value={empty ? 0 : 2}
          detail="Sample document status"
          icon={Activity}
          tone="violet"
        />
        <MetricCard
          label="Published"
          value={empty ? 0 : 2}
          detail="Available to learners"
          icon={ShieldCheck}
          tone="green"
        />
      </div>
      <DocumentTable empty={empty} onOpen={onOpen} />
    </>
  );
}
function DocumentTable({
  empty = false,
  onOpen,
}: {
  empty?: boolean;
  onOpen: (title: string, description: string) => void;
}) {
  const searchId = useId();
  const [search, setSearch] = useState('');
  const [subject, setSubject] = useState('All');
  const [status, setStatus] = useState('All');
  const [date, setDate] = useState('all');
  const [ascending, setAscending] = useState(false);
  const [page, setPage] = useState(0);
  const rows = (empty ? [] : demoDocuments)
    .filter(
      (row) =>
        row.title.toLowerCase().includes(search.trim().toLowerCase()) &&
        (subject === 'All' || subject === row.subject) &&
        (status === 'All' || status === row.status) &&
        (date === 'all' || row.updated >= '2026-10-16'),
    )
    .sort((a, b) =>
      ascending
        ? a.updated.localeCompare(b.updated)
        : b.updated.localeCompare(a.updated),
    );
  const pages = Math.max(1, Math.ceil(rows.length / 4));
  const currentPage = Math.min(page, pages - 1);
  return (
    <DashboardCard
      title="Content library"
      description="Sample documents · filters apply to this preview only"
    >
      <div className="ak-filter-toolbar">
        <label className="ak-field ak-filter-search" htmlFor={searchId}>
          <span>Search resources</span>
          <span className="ak-input-icon">
            <Search size={16} />
            <Input
              id={searchId}
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(0);
              }}
              placeholder="Search by title…"
            />
          </span>
        </label>
        <label className="ak-field">
          <span>Subject</span>
          <select
            value={subject}
            onChange={(e) => {
              setSubject(e.target.value);
              setPage(0);
            }}
          >
            {['All', 'Mathematics', 'Chemistry', 'English'].map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </label>
        <label className="ak-field">
          <span>Updated</span>
          <select
            value={date}
            onChange={(e) => {
              setDate(e.target.value);
              setPage(0);
            }}
          >
            <option value="all">Any time</option>
            <option value="recent">16–18 Oct</option>
          </select>
        </label>
      </div>
      <div className="ak-status-filters" aria-label="Filter resource status">
        {['All', 'Awaiting review', 'Processing', 'Published', 'Draft'].map(
          (s) => (
            <Button
              key={s}
              size="sm"
              variant={status === s ? 'secondary' : 'ghost'}
              aria-pressed={status === s}
              onClick={() => {
                setStatus(s);
                setPage(0);
              }}
            >
              {s}
            </Button>
          ),
        )}
      </div>
      {rows.length ? (
        <div className="ak-table-scroll">
          <table className="ak-data-table">
            <caption className="sr-only">Sample learning resources</caption>
            <thead>
              <tr>
                <th scope="col">Resource</th>
                <th scope="col">Status</th>
                <th
                  scope="col"
                  aria-sort={ascending ? 'ascending' : 'descending'}
                >
                  <button
                    type="button"
                    onClick={() => {
                      setAscending(!ascending);
                      setPage(0);
                    }}
                  >
                    Updated {ascending ? '↑' : '↓'}
                  </button>
                </th>
                <th scope="col">
                  <span className="sr-only">Details</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.slice(currentPage * 4, currentPage * 4 + 4).map((row) => (
                <tr key={row.id}>
                  <td>
                    <strong>{row.title}</strong>
                    <small>{row.subject} · Learning resource</small>
                  </td>
                  <td>
                    <StatusPill status={row.status} />
                  </td>
                  <td>{row.updated}</td>
                  <td>
                    <Button
                      variant="ghost"
                      size="sm"
                      aria-label={`View ${row.title}`}
                      onClick={() =>
                        onOpen(
                          row.title,
                          `${row.subject} · ${row.status} · Updated ${row.updated}. In the live portal, review actions use the existing document workflow.`,
                        )
                      }
                    >
                      View <ArrowRight size={14} />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState
          title="No resources found"
          description="Try another search or reset the filters."
          action={
            <Button
              variant="outline"
              onClick={() => {
                setSearch('');
                setSubject('All');
                setStatus('All');
                setDate('all');
                setPage(0);
              }}
            >
              Reset filters
            </Button>
          }
        />
      )}
      <div className="ak-pagination">
        <span aria-live="polite">
          {rows.length} resources · Page {currentPage + 1} of {pages}
        </span>
        <div>
          <Button
            variant="outline"
            size="sm"
            disabled={currentPage === 0}
            onClick={() => setPage(currentPage - 1)}
          >
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={currentPage + 1 >= pages}
            onClick={() => setPage(currentPage + 1)}
          >
            Next
          </Button>
        </div>
      </div>
    </DashboardCard>
  );
}
function PeoplePreview({
  onOpen,
}: {
  onOpen: (title: string, description: string) => void;
}) {
  const [grid, setGrid] = useState(true);
  return (
    <>
      <PageHeader
        level={2}
        title="People & profiles"
        description="Recognisable, readable summaries for every learner."
        action={
          <div className="ak-view-toggle">
            <Button
              variant={grid ? 'secondary' : 'outline'}
              aria-label="Grid view"
              aria-pressed={grid}
              onClick={() => setGrid(true)}
            >
              <Grid2X2 size={17} />
            </Button>
            <Button
              variant={!grid ? 'secondary' : 'outline'}
              aria-label="List view"
              aria-pressed={!grid}
              onClick={() => setGrid(false)}
            >
              <List size={17} />
            </Button>
          </div>
        }
      />
      <div className={grid ? 'ak-people-grid' : 'ak-stack'}>
        {demoLearners.map((person) => (
          <StudentSummaryCard
            key={person.id}
            {...person}
            action={
              <Button
                variant="outline"
                onClick={() =>
                  onOpen(
                    person.name,
                    `${person.grade} · ${person.term}. ${person.subjects.join(', ')}. Sample profile.`,
                  )
                }
              >
                View learner
              </Button>
            }
          />
        ))}
      </div>
    </>
  );
}
function FeedbackPreview() {
  const [title, setTitle] = useState('');
  const [error, setError] = useState('');
  const [saved, setSaved] = useState(false);
  return (
    <>
      <PageHeader
        level={2}
        title="Forms & feedback"
        description="Clear labels, helpful validation, and feedback at the right moment."
      />
      <DashboardCard
        title="Practice reminder"
        description="Local form example · nothing is sent or saved to an account"
      >
        <form
          className="ak-demo-form"
          noValidate
          onSubmit={(e) => {
            e.preventDefault();
            setSaved(false);
            if (title.trim().length < 3) {
              setError('Enter a reminder with at least 3 characters.');
              return;
            }
            setError('');
            setSaved(true);
          }}
        >
          <label className="ak-field" htmlFor="reminder-title">
            <span>Reminder title</span>
            <Input
              id="reminder-title"
              value={title}
              onChange={(e) => {
                setTitle(e.target.value);
                setSaved(false);
              }}
              aria-invalid={!!error}
              aria-describedby={error ? 'reminder-error' : 'reminder-help'}
              placeholder="e.g. Review chemical bonding"
            />
          </label>
          <small id="reminder-help">
            A short, specific next step makes it easier to get started.
          </small>
          {error && (
            <p id="reminder-error" role="alert" className="ak-form-error">
              {error}
            </p>
          )}
          <Button type="submit">
            Preview reminder <ArrowRight size={16} />
          </Button>
          {saved && (
            <output className="ak-inline-note">
              <Check size={18} /> “{title.trim()}” is ready. This preview has
              not sent a notification.
            </output>
          )}
        </form>
      </DashboardCard>
    </>
  );
}
