'use client';
import { useState } from 'react';
import type { AvatarConfig } from '@/api';
import { StudentAvatar } from '@/components/portal/student-avatar';
import { StudentAvatarEditor } from './student-avatar-editor';
import {
  ArrowRight,
  BookOpen,
  GraduationCap,
  KeyRound,
  ShieldCheck,
  UserRound,
  Users,
} from 'lucide-react';
import type { State, Student } from '@/api';
import {
  PageHeader,
  DashboardCard,
  MetricCard,
  EmptyState,
} from '@/components/portal/dashboard-widgets';
import { Button } from '@/components/ui/button';
import { CommunitySettingsPanel } from './community';
import { profileDetails } from '@/lib/profile';
import { pathForView } from '@/lib/routes';

function Details({ rows }: { rows: [string, string][] }) {
  return (
    <dl className="profile-details">
      {rows.map(([label, value]) => (
        <div key={label}>
          <dt>{label}</dt>
          <dd>{value || 'Not configured'}</dd>
        </div>
      ))}
    </dl>
  );
}
function CourseList({ student, data }: { student: Student; data: State }) {
  return (
    <ul className="profile-courses">
      {student.subjects.map((id) => {
        const subject = data.subjects.find((item) => item.id === id),
          course = student.courses[id];
        return (
          <li key={id}>
            <span className="profile-course-icon">
              <BookOpen size={18} />
            </span>
            <div>
              <strong>{subject?.name || id}</strong>
              <small>
                {[course?.level || student.level, course?.syllabus]
                  .filter(Boolean)
                  .join(' · ') || 'Enrolled course'}
              </small>
            </div>
            <span className="pill">Enrolled</span>
          </li>
        );
      })}
    </ul>
  );
}
export function AccountProfile({
  data,
  navigate,
  refresh,
  notify,
}: {
  data: State;
  navigate: (path: string) => void;
  refresh: () => Promise<void>;
  notify: (message: string) => void;
}) {
  const profile = profileDetails(data);
  const { role, student, children } = profile;
  const [editorOpen, setEditorOpen] = useState(false);
  const [savedAvatar, setSavedAvatar] = useState<
    AvatarConfig | null | undefined
  >(undefined);
  const avatar =
    savedAvatar === undefined ? student?.avatar || null : savedAvatar;
  const open = (view: string) => navigate(pathForView(role, view));
  return (
    <div className="account-profile">
      <PageHeader
        eyebrow={`${profile.roleName.toUpperCase()} · ACCOUNT`}
        title="My profile"
        description="Your account, your learning space."
        action={
          <Button variant="outline" onClick={() => open('security')}>
            <KeyRound size={16} />
            Password settings
          </Button>
        }
      />
      <section className="profile-banner" aria-label="Profile summary">
        <div className="profile-banner-pattern" aria-hidden="true" />
        <div className="profile-identity">
          <div className="profile-avatar-actions">
            <span className="profile-avatar">
              <StudentAvatar
                avatar={role === 'student' ? avatar : null}
                fallback={profile.initials}
              />
            </span>
            {role === 'student' && (
              <button type="button" onClick={() => setEditorOpen(true)}>
                {avatar ? 'Edit avatar' : 'Create my avatar'}
              </button>
            )}
          </div>
          <div>
            <span className="profile-role">{profile.roleName}</span>
            <h2>{data.user.name}</h2>
            <p>
              @{data.user.username}
              {student
                ? ` · ${student.grade} · ${student.term || 'Term not configured'}`
                : ''}
            </p>
          </div>
        </div>
      </section>
      {role === 'student' && editorOpen && (
        <StudentAvatarEditor
          current={avatar}
          onClose={() => setEditorOpen(false)}
          onSaved={(next) => {
            setSavedAvatar(next);
            notify(
              next ? 'Your avatar is saved.' : 'Your initials are restored.',
            );
            void refresh()
              .then(() => setSavedAvatar(undefined))
              .catch(() =>
                notify(
                  'Avatar saved. Refresh the page to update other account icons.',
                ),
              );
          }}
        />
      )}
      <div className="ak-metric-grid profile-metrics">
        <MetricCard
          label="Your role"
          value={profile.roleName}
          detail="Your AKURU workspace"
          icon={UserRound}
        />
        {role === 'student' ? (
          <MetricCard
            label="Enrolled subjects"
            value={profile.subjects.length}
            detail="Configured by your Administrator"
            icon={BookOpen}
          />
        ) : role === 'parent' ? (
          <MetricCard
            label="Linked children"
            value={children.length}
            detail="Your family learning space"
            icon={Users}
          />
        ) : (
          <MetricCard
            label="Workspace"
            value="Administration"
            detail="Accounts, curriculum and review"
            icon={ShieldCheck}
          />
        )}
        <MetricCard
          label="Password settings"
          value={data.user.mustChangePassword ? 'Update required' : 'Available'}
          detail="Manage your password securely"
          icon={KeyRound}
        />
      </div>
      <div className="profile-columns">
        <aside className="profile-sidebar">
          <DashboardCard
            title="Account information"
            description="Your sign-in details"
          >
            <Details
              rows={[
                ['Full name', data.user.name],
                ['Username', `@${data.user.username}`],
                ['Account role', profile.roleName],
              ]}
            />
            {profile.lastLoginAt && (
              <p className="profile-note">
                Last recorded sign-in:{' '}
                {new Date(profile.lastLoginAt).toLocaleString()}
              </p>
            )}
            <p className="profile-note">
              Contact your Administrator if your name or account details need
              correcting.
            </p>
          </DashboardCard>
          <DashboardCard
            title="Account security"
            description="Keep access to your account private"
          >
            <div className="profile-security">
              <ShieldCheck size={26} />
              <div>
                <strong>
                  {data.user.mustChangePassword
                    ? 'Set your own password'
                    : 'Password management'}
                </strong>
                <p>
                  {data.user.mustChangePassword
                    ? 'Replace your temporary password to secure your account.'
                    : 'Use your account security page to change your password.'}
                </p>
              </div>
            </div>
            <Button variant="outline" onClick={() => open('security')}>
              Open account security
              <ArrowRight size={15} />
            </Button>
          </DashboardCard>
        </aside>
        <div className="profile-main">
          {role === 'student' && (
            <>
              <DashboardCard
                title="Learning information"
                description="Your current enrolment"
              >
                <Details
                  rows={[
                    ['Programme', student?.level || 'Not configured'],
                    ['Grade', student?.grade || 'Not configured'],
                    ['Current term', student?.term || 'Not configured'],
                    [
                      'Enrolment',
                      student && !student.needsConfiguration
                        ? 'Configured'
                        : 'Administrator confirmation needed',
                    ],
                  ]}
                />
              </DashboardCard>
              <DashboardCard
                title="My courses"
                description="Subjects enrolled for your learning journey"
                action={
                  <Button variant="ghost" onClick={() => open('subjects')}>
                    Explore subjects
                    <ArrowRight size={15} />
                  </Button>
                }
              >
                {student?.subjects.length ? (
                  <CourseList student={student} data={data} />
                ) : (
                  <EmptyState
                    title="No subjects configured"
                    description="Your Administrator can confirm your grade, term and enrolled subjects."
                  />
                )}
              </DashboardCard>
              <CommunitySettingsPanel actorRef={data.user.id} compact />
            </>
          )}
          {role === 'parent' && (
            <DashboardCard
              title="My family"
              description="Children linked to your Parent account"
              action={
                <Button variant="ghost" onClick={() => open('students')}>
                  Children & courses
                  <ArrowRight size={15} />
                </Button>
              }
            >
              {children.length ? (
                <div className="profile-family">
                  {children.map((child) => (
                    <article className="profile-child" key={child.id}>
                      <header>
                        <span
                          className="profile-child-avatar"
                          aria-hidden="true"
                        >
                          <StudentAvatar
                            avatar={child.avatar}
                            fallback={child.initial}
                          />
                        </span>
                        <div>
                          <h3>{child.name}</h3>
                          <p>
                            {child.level} · {child.grade} ·{' '}
                            {child.term || 'Term not configured'}
                          </p>
                        </div>
                      </header>
                      {child.needsConfiguration && (
                        <p className="profile-note">
                          Enrolment needs Administrator confirmation.
                        </p>
                      )}
                      {child.subjects.length ? (
                        <CourseList student={child} data={data} />
                      ) : (
                        <p className="profile-note">
                          No subjects configured yet.
                        </p>
                      )}
                    </article>
                  ))}
                </div>
              ) : (
                <EmptyState
                  title="No children linked yet"
                  description="Ask your Administrator to link your children's accounts."
                />
              )}
            </DashboardCard>
          )}
          {role === 'admin' && (
            <DashboardCard
              title="Your administration workspace"
              description="The tools available in your Admin account"
            >
              <div className="profile-admin-tools">
                {(
                  [
                    [
                      'accounts',
                      'Accounts & enrolments',
                      'Manage family accounts and learner enrolments.',
                      Users,
                    ],
                    [
                      'units',
                      'Textbooks & curriculum',
                      'Organise textbooks and reviewed learning content.',
                      BookOpen,
                    ],
                    [
                      'library',
                      'Exam document review',
                      'Review official sources and publication readiness.',
                      GraduationCap,
                    ],
                  ] as const
                ).map(([view, title, description, ToolIcon]) => {
                  return (
                    <button type="button" key={view} onClick={() => open(view)}>
                      <ToolIcon size={21} />
                      <span>
                        <strong>{title}</strong>
                        <small>{description}</small>
                      </span>
                      <ArrowRight size={16} />
                    </button>
                  );
                })}
              </div>
            </DashboardCard>
          )}
          <DashboardCard
            title={
              role === 'admin' ? 'Continue in AKURU' : 'Your next destination'
            }
            description="Go straight to the pages you use most"
          >
            <div className="profile-shortcuts">
              <Button onClick={() => open('today')}>
                My overview
                <ArrowRight size={15} />
              </Button>
              <Button
                variant="outline"
                onClick={() =>
                  open(
                    role === 'student'
                      ? 'plan'
                      : role === 'parent'
                        ? 'assignments'
                        : 'operations',
                  )
                }
              >
                {role === 'student'
                  ? 'Study plan'
                  : role === 'parent'
                    ? 'Family assignments'
                    : 'Operations'}
              </Button>
              {role !== 'admin' && (
                <Button variant="outline" onClick={() => open('progress')}>
                  Learning progress
                </Button>
              )}
            </div>
          </DashboardCard>
        </div>
      </div>
    </div>
  );
}
