'use client';
import {
  MetadataBadge,
  StatusBadge,
  CountBadge,
} from '@/components/portal/badges';
import { useState, type ReactNode } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Bell, Users, ShieldCheck, UserPlus, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { parseAvatar } from '@/lib/student-avatar';
import { StudentAvatar } from '@/components/portal/student-avatar';
import { EditorDrawer, useWorkspaceGuard } from '@/components/portal/workspace';
import {
  getCommunitySettings,
  saveCommunitySettings,
  getCommunityMembers,
  getCommunitySubjects,
  getCommunityFeed,
  followCommunityMember,
  blockCommunityMember,
  getCommunityBlocks,
  readCommunityNotice,
  reportCommunityMember,
  getCommunityReports,
  reviewCommunityReport,
  errorMessage,
  type CommunitySettings,
  type CommunitySettingsDraft,
  type CommunityMember,
} from '@/api';

const key = (actor: string) => ['community', actor];

function CommunityCard({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <section className="community-card">
      <header>
        <h2>{title}</h2>
        {description && <p>{description}</p>}
      </header>
      <div className="community-card-body">{children}</div>
    </section>
  );
}
function QueryFailure({ retry }: { retry: () => void }) {
  return (
    <div className="error" role="alert">
      Community could not be loaded.{' '}
      <Button variant="outline" onClick={retry}>
        Try again
      </Button>
    </div>
  );
}
function Pagination({
  page,
  more,
  setPage,
}: {
  page: number;
  more: boolean;
  setPage: (page: number) => void;
}) {
  return (
    <nav className="community-pagination" aria-label="Community pages">
      <Button
        variant="outline"
        disabled={page === 1}
        onClick={() => setPage(page - 1)}
      >
        Previous
      </Button>
      <span>Page {page}</span>
      <Button
        variant="outline"
        disabled={!more}
        onClick={() => setPage(page + 1)}
      >
        Next
      </Button>
    </nav>
  );
}

export function CommunitySettingsPanel({
  actorRef,
  compact = false,
}: {
  actorRef: string;
  compact?: boolean;
}) {
  const query = useQuery({
    queryKey: [...key(actorRef), 'settings'],
    queryFn: getCommunitySettings,
  });
  if (query.isPending) return <output>Loading community preferences…</output>;
  if (query.isError) return <QueryFailure retry={() => void query.refetch()} />;
  return (
    <CommunityPreferences
      key={JSON.stringify(query.data)}
      actorRef={actorRef}
      settings={query.data}
      compact={compact}
    />
  );
}
function CommunityPreferences({
  actorRef,
  settings,
  compact,
}: {
  actorRef: string;
  settings: CommunitySettings;
  compact: boolean;
}) {
  const cache = useQueryClient();
  const [open, setOpen] = useState(false);
  const initialDraft = {
    publicName: settings.publicName,
    enabled: settings.enabled,
    visibleSubjectIds: settings.visibleSubjectIds,
  };
  const [draft, setDraft] = useState<Required<CommunitySettingsDraft>>({
    publicName: settings.publicName,
    enabled: settings.enabled,
    visibleSubjectIds: settings.visibleSubjectIds,
  });
  const [busy, setBusy] = useState(false),
    [message, setMessage] = useState(''),
    [error, setError] = useState('');
  const dirty =
    JSON.stringify(draft) !==
    JSON.stringify({
      publicName: settings.publicName,
      enabled: settings.enabled,
      visibleSubjectIds: settings.visibleSubjectIds,
    });
  useWorkspaceGuard(!compact && dirty, !compact && busy);
  const editor = (
    <CommunityCard
      title="Your community profile"
      description="Choose how other students see you. Your real name and login details stay private."
    >
      {settings.nameChangeRequired && (
        <p role="alert" className="error">
          An Admin has hidden your community profile. Choose a different public
          name to rejoin.
        </p>
      )}
      <output aria-live="polite" className="community-feedback">
        {settings.enabled
          ? 'Your community profile is visible.'
          : 'Your community profile is hidden.'}
      </output>
      <form
        className="stack"
        onSubmit={async (e) => {
          e.preventDefault();
          setBusy(true);
          setError('');
          try {
            const saved = await saveCommunitySettings(draft);
            setDraft({
              publicName: saved.publicName,
              enabled: saved.enabled,
              visibleSubjectIds: saved.visibleSubjectIds,
            });
            if (compact) setOpen(false);
            setMessage('Community preferences saved.');
            await cache.invalidateQueries({ queryKey: key(actorRef) });
          } catch (e) {
            setError(errorMessage(e));
          } finally {
            setBusy(false);
          }
        }}
      >
        <fieldset disabled={busy} className="community-settings-fields">
          <label htmlFor="community-public-name">
            Public name
            <Input
              id="community-public-name"
              value={draft.publicName}
              minLength={3}
              maxLength={32}
              required
              onChange={(e) =>
                setDraft({ ...draft, publicName: e.target.value })
              }
              placeholder="Choose a name, such as OrbitNova"
              autoComplete="off"
            />
          </label>
          <small>
            3–32 letters, numbers, spaces, hyphens or underscores. Choose a name
            that does not identify you personally.
          </small>
          <label className="community-check">
            <input
              type="checkbox"
              checked={draft.enabled}
              onChange={(e) =>
                setDraft({ ...draft, enabled: e.target.checked })
              }
            />
            Let other students discover and follow me
          </label>
          <p>
            Other participating students in your course can see your public
            name, AKURU avatar and the subjects you select below. Your marks and
            learning history stay private.
          </p>
          <fieldset>
            <legend>Subjects to show (optional)</legend>
            <div className="community-subject-choices">
              {settings.subjects.map((s) => (
                <label key={s.id} className="community-check">
                  <input
                    type="checkbox"
                    checked={draft.visibleSubjectIds.includes(s.id)}
                    onChange={(e) =>
                      setDraft({
                        ...draft,
                        visibleSubjectIds: e.target.checked
                          ? [...draft.visibleSubjectIds, s.id]
                          : draft.visibleSubjectIds.filter((id) => id !== s.id),
                      })
                    }
                  />
                  {s.name}
                </label>
              ))}
            </div>
          </fieldset>
          <p>
            Switch participation off to hide your profile and pause new follows.
            Existing connections stay private and return when you rejoin.
            Blocking removes connections permanently; unblocking will not
            restore them.
          </p>
          <Button type="submit" disabled={!dirty || busy}>
            {busy ? 'Saving…' : 'Save community preferences'}
          </Button>
        </fieldset>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        {message && <output aria-live="polite">{message}</output>}
      </form>
    </CommunityCard>
  );
  if (!compact) return editor;
  return (
    <>
      <CommunityCard
        title="Community identity"
        description="Your public name and visibility to other students"
      >
        <div className="community-identity-summary">
          <div>
            <strong>{settings.publicName || 'No public name yet'}</strong>
            <StatusBadge
              status={
                settings.enabled && !settings.nameChangeRequired
                  ? 'visible'
                  : 'hidden'
              }
            />
          </div>
          <p>
            {settings.nameChangeRequired
              ? 'Choose a new public name before rejoining.'
              : 'Manage your public name, participation and visible subjects.'}
          </p>
          <Button variant="outline" onClick={() => setOpen(true)}>
            Manage community profile
          </Button>
        </div>
      </CommunityCard>
      <EditorDrawer
        open={open}
        onOpenChange={(next) => {
          setOpen(next);
          if (!next) {
            setDraft(initialDraft);
            setError('');
            setMessage('');
          }
        }}
        title="Manage community profile"
        description="Choose what other students can see. Your account details stay private."
        dirty={dirty}
        busy={busy}
      >
        {editor}
      </EditorDrawer>
    </>
  );
}

export function CommunityNotificationButton({
  actorRef,
  open,
}: {
  actorRef: string;
  open: () => void;
}) {
  const feed = useQuery({
    queryKey: [...key(actorRef), 'feed', 'badge'],
    queryFn: () => getCommunityFeed(),
    refetchInterval: 60000,
    refetchOnWindowFocus: true,
  });
  const count = feed.data?.unreadCount || 0;
  return (
    <Button
      variant="outline"
      size="sm"
      onClick={open}
      aria-label={`Community notifications, ${count} unread`}
    >
      <Bell size={16} />
      <span className="community-notice-label">Feed</span>
      {count > 0 && (
        <CountBadge count={count} label="unread community notifications" />
      )}
    </Button>
  );
}

export function StudentCommunity({
  actorRef,
  search,
  navigate,
}: {
  actorRef: string;
  search: Record<string, unknown>;
  navigate: (path: string) => void;
}) {
  const tabs = [
    'discover',
    'following',
    'followers',
    'feed',
    'settings',
    'blocked',
  ] as const;
  const tab = tabs.includes(search.section as (typeof tabs)[number])
    ? (search.section as (typeof tabs)[number])
    : 'discover';
  const page = Math.max(1, Number(search.page) || 1);
  const course = typeof search.course === 'string' ? search.course : '';
  const subject = typeof search.subject === 'string' ? search.subject : '';
  const q = typeof search.q === 'string' ? search.q : '';
  const cache = useQueryClient();
  const settings = useQuery({
    queryKey: [...key(actorRef), 'settings'],
    queryFn: getCommunitySettings,
  });
  const effectiveCourse = course || settings.data?.courses[0]?.id || '';
  const enabled = !!settings.data?.enabled && !settings.data.nameChangeRequired;
  const params = {
    kind: tab,
    course: effectiveCourse,
    subject,
    q,
    page: String(page),
  };
  const members = useQuery({
    queryKey: [...key(actorRef), 'members', params],
    queryFn: () => getCommunityMembers(params),
    enabled:
      enabled &&
      ['discover', 'following', 'followers'].includes(tab) &&
      (tab !== 'discover' || !!effectiveCourse),
  });
  const subjectOptions = useQuery({
    queryKey: [...key(actorRef), 'subjects', effectiveCourse],
    queryFn: () => getCommunitySubjects(effectiveCourse),
    enabled: enabled && !!effectiveCourse && tab === 'discover',
  });
  const feed = useQuery({
    queryKey: [...key(actorRef), 'feed', page],
    queryFn: () => getCommunityFeed(page),
    enabled: enabled && tab === 'feed',
    refetchInterval: 60000,
  });
  const blocked = useQuery({
    queryKey: [...key(actorRef), 'blocked', page],
    queryFn: () => getCommunityBlocks(page),
    enabled: !!settings.data && tab === 'blocked',
  });
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(''),
    [notice, setNotice] = useState('');
  const [report, setReport] = useState<CommunityMember | null>(null),
    [reason, setReason] = useState<
      'inappropriate_name' | 'impersonation' | 'other_concern'
    >('inappropriate_name');
  const [blocking, setBlocking] = useState<CommunityMember | null>(null);
  const change = (next: Record<string, string>) => {
    const values = {
      section: tab,
      course: effectiveCourse,
      subject,
      q,
      ...next,
    };
    navigate(
      `/student/community?${new URLSearchParams(Object.entries(values).filter(([, v]) => v))}`,
    );
  };
  const action = async (work: () => Promise<unknown>, success: string) => {
    if (busy) return;
    setBusy(true);
    setError('');
    try {
      await work();
      setNotice(success);
      setReport(null);
      setBlocking(null);
      await cache.invalidateQueries({ queryKey: key(actorRef) });
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  };
  const person = (member: CommunityMember, controls = true) => (
    <article key={member.ref} className="community-person">
      <div className="community-person-identity">
        <span className="community-avatar">
          <StudentAvatar
            avatar={parseAvatar(member.avatar)}
            fallback="★"
            label={`${member.publicName}'s avatar`}
          />
        </span>
        <div>
          <h3>{member.publicName}</h3>
          {member.subjects.length > 0 && (
            <p className="ak-badge-wrap">
              {member.subjects.map((s) => (
                <MetadataBadge size="xs" key={s.id}>
                  {s.name}
                </MetadataBadge>
              ))}
            </p>
          )}
          {(member.following || member.followsYou) && (
            <StatusBadge
              size="xs"
              status={
                member.following && member.followsYou
                  ? 'following each other'
                  : member.followsYou
                    ? 'follows you'
                    : 'following'
              }
            />
          )}
        </div>
      </div>
      {controls && (
        <div className="community-person-actions">
          <Button
            disabled={busy}
            variant={member.following ? 'outline' : 'default'}
            onClick={() =>
              void action(
                () => followCommunityMember(member.ref, member.following),
                member.following
                  ? 'Unfollowed.'
                  : 'You are now following this learner.',
              )
            }
          >
            {member.following
              ? 'Unfollow'
              : member.followsYou
                ? 'Follow back'
                : 'Follow'}
            {!member.following && <UserPlus size={15} />}
          </Button>
          <Button
            variant="ghost"
            disabled={busy}
            onClick={() => {
              setReason('inappropriate_name');
              setReport(member);
            }}
          >
            Report
          </Button>
          <Button
            variant="ghost"
            disabled={busy}
            onClick={() => setBlocking(member)}
          >
            Block
          </Button>
        </div>
      )}
    </article>
  );
  return (
    <div className="community-workspace stack">
      <header className="community-heading">
        <div>
          <p className="eyebrow">LEARN TOGETHER</p>
          <h1>Community</h1>
          <p>
            Find familiar learning journeys. Make a connection, one follow at a
            time.
          </p>
        </div>
        <Users size={32} />
      </header>
      <nav className="community-tabs" aria-label="Community sections">
        {tabs.map((t) => (
          <Button
            key={t}
            variant={tab === t ? 'default' : 'outline'}
            aria-current={tab === t ? 'page' : undefined}
            onClick={() =>
              change({ section: t, page: '1', q: '', subject: '' })
            }
          >
            {t === 'blocked'
              ? 'Blocked learners'
              : t[0].toUpperCase() + t.slice(1)}
          </Button>
        ))}
      </nav>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {notice && (
        <output aria-live="polite" className="community-feedback">
          {notice}
        </output>
      )}
      {settings.isPending ? (
        <output>Opening your community…</output>
      ) : settings.isError ? (
        <QueryFailure retry={() => void settings.refetch()} />
      ) : tab === 'settings' ? (
        <CommunitySettingsPanel actorRef={actorRef} />
      ) : tab === 'blocked' ? (
        <CommunityCard
          title="Blocked learners"
          description="Unblocking lets an eligible learner find you again. Previous connections are not restored."
        >
          {blocked.isPending ? (
            <output>Loading blocked learners…</output>
          ) : blocked.isError ? (
            <QueryFailure retry={() => void blocked.refetch()} />
          ) : (
            <>
              <div className="community-grid">
                {blocked.data.members.map((m) => (
                  <div key={m.ref}>
                    {person(m, false)}
                    <Button
                      variant="outline"
                      disabled={busy}
                      onClick={() =>
                        void action(
                          () => blockCommunityMember(m.ref, true),
                          'Learner unblocked.',
                        )
                      }
                    >
                      Unblock
                    </Button>
                  </div>
                ))}
              </div>
              {!blocked.data.members.length && <p>No blocked learners.</p>}
              <Pagination
                page={page}
                more={blocked.data.hasMore}
                setPage={(p) => change({ page: String(p) })}
              />
            </>
          )}
        </CommunityCard>
      ) : !enabled ? (
        <CommunityCard
          title="Your community starts with a public name"
          description="Participation is optional. Your private account details are never shown to other learners."
        >
          <p>
            {settings.data.nameChangeRequired
              ? 'Please choose a new public name before rejoining.'
              : 'Create your public identity to discover students in your course and follow their journey.'}
          </p>
          <Button onClick={() => change({ section: 'settings', page: '1' })}>
            Set up my community profile
          </Button>
        </CommunityCard>
      ) : tab === 'feed' ? (
        <CommunityCard
          title="Your Feed"
          description="Follow notifications live here. Exam results and learning activity are not shared."
        >
          {feed.isPending ? (
            <output>Loading your Feed…</output>
          ) : feed.isError ? (
            <QueryFailure retry={() => void feed.refetch()} />
          ) : (
            <>
              {!feed.data.notifications.length && (
                <div className="community-empty">
                  <Bell />
                  <h3>No connection updates yet</h3>
                  <p>
                    Discover students in your course. When someone follows you,
                    their notification will appear here.
                  </p>
                  <Button
                    variant="outline"
                    onClick={() => change({ section: 'discover', page: '1' })}
                  >
                    Discover learners
                  </Button>
                </div>
              )}
              {feed.data.notifications.map((n) => (
                <div
                  key={n.ref}
                  className="community-event"
                  data-unread={!n.read}
                >
                  <p>
                    <strong>{n.actor.publicName}</strong> started following you.
                  </p>
                  <time dateTime={n.createdAt}>
                    {new Date(n.createdAt).toLocaleString()}
                  </time>
                  {person(n.actor)}
                  <Button
                    variant="ghost"
                    disabled={busy}
                    onClick={() =>
                      void action(
                        () => readCommunityNotice(n.ref, !n.read),
                        n.read ? 'Marked unread.' : 'Marked read.',
                      )
                    }
                  >
                    Mark {n.read ? 'unread' : 'read'}
                  </Button>
                </div>
              ))}
              <Pagination
                page={page}
                more={feed.data.hasMore}
                setPage={(p) => change({ page: String(p) })}
              />
            </>
          )}
        </CommunityCard>
      ) : (
        <CommunityCard
          title={
            tab === 'discover'
              ? 'Discover learners'
              : tab === 'followers'
                ? 'Your followers'
                : 'Learners you follow'
          }
          description={
            tab === 'discover'
              ? 'Explore your course. You do not need to study the same subjects to follow someone.'
              : 'Your connections can continue even when courses change.'
          }
        >
          <form
            className="community-filters"
            onSubmit={(e) => {
              e.preventDefault();
              const value = new FormData(e.currentTarget).get('publicName');
              change({ q: typeof value === 'string' ? value : '', page: '1' });
            }}
          >
            <label htmlFor="community-public-search">
              Public name
              <div className="community-search">
                <Input
                  id="community-public-search"
                  name="publicName"
                  key={q}
                  defaultValue={q}
                  maxLength={64}
                  placeholder="Search public names…"
                />
                <Button
                  type="submit"
                  variant="outline"
                  aria-label="Search public names"
                >
                  <Search size={16} />
                </Button>
              </div>
            </label>
            {tab === 'discover' && (
              <>
                <label>
                  Course
                  <select
                    value={effectiveCourse}
                    onChange={(e) =>
                      change({ course: e.target.value, subject: '', page: '1' })
                    }
                  >
                    {settings.data.courses.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Subject (optional)
                  <select
                    value={subject}
                    disabled={
                      !effectiveCourse ||
                      subjectOptions.isPending ||
                      subjectOptions.isError
                    }
                    onChange={(e) =>
                      change({ subject: e.target.value, page: '1' })
                    }
                  >
                    <option value="">All subjects</option>
                    {subjectOptions.data?.subjects.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name}
                      </option>
                    ))}
                  </select>
                </label>
              </>
            )}
          </form>
          {subjectOptions.isError && tab === 'discover' && (
            <QueryFailure retry={() => void subjectOptions.refetch()} />
          )}
          {tab === 'discover' && !effectiveCourse ? (
            <p>
              No current course is assigned. Ask your Parent or an Admin to
              check your enrolment.
            </p>
          ) : members.isPending ? (
            <output>Finding learners…</output>
          ) : members.isError ? (
            <QueryFailure retry={() => void members.refetch()} />
          ) : (
            <>
              <div className="community-grid">
                {members.data?.members.map((m) => person(m))}
              </div>
              {!members.data?.members.length && (
                <div className="community-empty">
                  <Users />
                  <h3>
                    {q || subject
                      ? 'No matching learners'
                      : 'No learners here yet'}
                  </h3>
                  <p>
                    {q || subject
                      ? 'Try another public name or remove the subject filter.'
                      : 'Only students who have enabled their community profile appear here.'}
                  </p>
                </div>
              )}
              <Pagination
                page={page}
                more={members.data?.hasMore || false}
                setPage={(p) => change({ page: String(p) })}
              />
            </>
          )}
        </CommunityCard>
      )}
      <EditorDrawer
        open={!!report}
        onOpenChange={(open) => {
          if (!open) setReport(null);
        }}
        title="Report community profile"
        description="Your report is private and reviewed by an AKURU Admin."
        busy={busy}
      >
        <p>Report {report?.publicName}</p>
        <label>
          Reason
          <select
            value={reason}
            onChange={(e) => setReason(e.target.value as typeof reason)}
          >
            <option value="inappropriate_name">
              Inappropriate public name
            </option>
            <option value="impersonation">Impersonation</option>
            <option value="other_concern">Another profile concern</option>
          </select>
        </label>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        <Button
          disabled={busy || !report}
          onClick={() =>
            report &&
            void action(
              () => reportCommunityMember(report.ref, reason),
              'Report sent privately to an Admin.',
            )
          }
        >
          Send report
        </Button>
      </EditorDrawer>
      <EditorDrawer
        open={!!blocking}
        onOpenChange={(open) => {
          if (!open) setBlocking(null);
        }}
        title="Block learner"
        description="Blocking removes follows in both directions and prevents you from finding or following each other."
        busy={busy}
      >
        <p>
          Block {blocking?.publicName}? You can unblock them from Blocked
          learners. Connections will not be restored automatically.
        </p>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        <Button
          disabled={busy || !blocking}
          onClick={() =>
            blocking &&
            void action(
              () => blockCommunityMember(blocking.ref),
              'Learner blocked. Both connections have been removed.',
            )
          }
        >
          Block learner
        </Button>
      </EditorDrawer>
    </div>
  );
}

export function CommunityModeration({ actorRef }: { actorRef: string }) {
  const [status, setStatus] = useState('open'),
    [page, setPage] = useState(1),
    [busy, setBusy] = useState(false),
    [error, setError] = useState('');
  const [selected, setSelected] = useState<{
    ref: string;
    publicName: string;
  } | null>(null);
  const cache = useQueryClient();
  const reports = useQuery({
    queryKey: [...key(actorRef), 'reports', status, page],
    queryFn: () => getCommunityReports(status, page),
  });
  const review = async (
    ref: string,
    action: 'dismissed' | 'name_change_required',
  ) => {
    setBusy(true);
    setError('');
    try {
      await reviewCommunityReport(ref, action);
      setSelected(null);
      await cache.invalidateQueries({ queryKey: key(actorRef) });
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="community-workspace stack">
      <header className="community-heading">
        <div>
          <p className="eyebrow">STUDENT SAFETY</p>
          <h1>Community reports</h1>
          <p>Review public identities without exposing reporter details.</p>
        </div>
        <ShieldCheck size={32} />
      </header>
      <CommunityCard
        title="Profile reports"
        description="A name-change request hides the profile until the student chooses a different public name."
      >
        <label>
          Status
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
          >
            <option value="open">Open</option>
            <option value="dismissed">Dismissed</option>
            <option value="name_change_required">Name change requested</option>
          </select>
        </label>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        {reports.isPending ? (
          <output>Loading reports…</output>
        ) : reports.isError ? (
          <QueryFailure retry={() => void reports.refetch()} />
        ) : (
          <>
            {!reports.data.reports.length && <p>No reports in this queue.</p>}
            {reports.data.reports.map((r) => (
              <article className="community-report" key={r.ref}>
                <h3>{r.publicName}</h3>
                <p>
                  {r.reason.replaceAll('_', ' ')} ·{' '}
                  {new Date(r.createdAt).toLocaleString()}
                </p>
                {r.status === 'open' && (
                  <div className="community-person-actions">
                    <Button
                      variant="outline"
                      disabled={busy}
                      onClick={() => void review(r.ref, 'dismissed')}
                    >
                      Dismiss
                    </Button>
                    <Button disabled={busy} onClick={() => setSelected(r)}>
                      Hide and request name change
                    </Button>
                  </div>
                )}
              </article>
            ))}
            <Pagination
              page={page}
              more={reports.data.hasMore}
              setPage={setPage}
            />
          </>
        )}
      </CommunityCard>
      <EditorDrawer
        open={!!selected}
        onOpenChange={(open) => {
          if (!open) setSelected(null);
        }}
        title="Request a new public name"
        description="This hides the student's community profile. Their account and learning access are unaffected."
        busy={busy}
      >
        <p>Request a different public name from {selected?.publicName}?</p>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        <Button
          disabled={busy || !selected}
          onClick={() =>
            selected && void review(selected.ref, 'name_change_required')
          }
        >
          Hide profile and request name change
        </Button>
      </EditorDrawer>
    </div>
  );
}
