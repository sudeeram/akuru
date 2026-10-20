'use client';
import {
  ArrowRight,
  BookOpen,
  CalendarDays,
  ClipboardCheck,
  Library,
  TrendingUp,
} from 'lucide-react';
import type { State, Student } from '@/api';
import { Button } from '@/components/ui/button';
import {
  ActivityTimeline,
  AssignmentList,
  ChildSwitcher,
  DashboardCard,
  MetricCard,
  PageHeader,
  StudentSummaryCard,
  SubjectProgressCard,
} from '@/components/portal/dashboard-widgets';
import { learnerSummary, markedScore } from '@/lib/dashboard-summary';
type HomeProps = {
  data: State;
  child: Student;
  go: (view: string, subject?: string) => void;
};
const subjectName = (data: State, id: string) =>
  data.subjects.find((subject) => subject.id === id)?.name ?? id;

function LearningOverview({
  data,
  child,
  go,
  parent,
}: HomeProps & { parent: boolean }) {
  const summary = learnerSummary(data.attempts, data.assignments, child.id);
  return (
    <div className="ak-dashboard-columns">
      <div className="ak-stack">
        <DashboardCard
          title={parent ? 'Subject performance' : 'My subjects'}
          description="Marks from checked or reviewed practice · not a mastery estimate"
          action={
            <Button
              variant="ghost"
              size="sm"
              onClick={() => go(parent ? 'progress' : 'subjects')}
            >
              View all <ArrowRight size={14} />
            </Button>
          }
        >
          <div className="ak-subject-grid">
            {child.subjects.map((id) => (
              <SubjectProgressCard
                key={id}
                subjectId={id}
                title={subjectName(data, id)}
                description={child.courses[id]?.level ?? child.level}
                value={markedScore(summary.attempts, id)}
                label="Checked practice marks"
                onOpen={() => go(parent ? 'progress' : 'subjects', id)}
              />
            ))}
          </div>
          {!child.subjects.length && (
            <p>Your subjects will appear after your account is configured.</p>
          )}
        </DashboardCard>
        <DashboardCard title="Recent learning">
          <ActivityTimeline
            items={summary.recent.map((item) => ({
              id: item.id,
              title: item.title,
              detail: `${subjectName(data, item.subject)} · ${item.status === 'needs-review' ? 'Awaiting review' : item.status.replaceAll('-', ' ')}`,
              date: new Date(item.createdAt).toLocaleDateString(),
            }))}
          />
        </DashboardCard>
      </div>
      <div className="ak-stack">
        <DashboardCard
          title="Up next"
          description="Open assignments, earliest due first"
          action={
            <Button
              variant="ghost"
              size="sm"
              onClick={() => go(parent ? 'assignments' : 'plan')}
            >
              View all
            </Button>
          }
        >
          <AssignmentList
            items={summary.assignments.slice(0, 4).map((item) => ({
              ...item,
              subject: subjectName(data, item.subject),
              due: `Due ${item.due}`,
              status: 'Assigned',
            }))}
            onOpen={(item) => {
              if (parent) {
                go('assignments');
                return;
              }
              const assignment = summary.assignments.find(
                (entry) => entry.id === item.id,
              );
              if (assignment) {
                sessionStorage.setItem(
                  'akuru-next-question',
                  assignment.questionId,
                );
                go('practice', assignment.subject);
              }
            }}
          />
        </DashboardCard>
        {parent ? (
          <>
            <DashboardCard title="A little attention goes a long way">
              <p>
                {summary.pending.length
                  ? `${summary.pending.length} ${summary.pending.length === 1 ? 'answer is' : 'answers are'} ready for your feedback.`
                  : 'There are no answers awaiting your review for this learner.'}
              </p>
              <Button variant="outline" onClick={() => go('reviews')}>
                Assessment reviews <ArrowRight size={16} />
              </Button>
            </DashboardCard>
            <Button variant="outline" onClick={() => go('library')}>
              <Library size={17} /> Open learning library
            </Button>
          </>
        ) : (
          <DashboardCard title="A good learning habit">
            <span className="ak-icon ak-tone-green">
              <BookOpen size={20} />
            </span>
            <h3 style={{ marginTop: 14 }}>Explain it out loud.</h3>
            <p>
              If you can teach an idea to someone else, you’re starting to make
              it your own.
            </p>
          </DashboardCard>
        )}
      </div>
    </div>
  );
}
export function ParentHome({
  data,
  child,
  go,
  choose,
}: HomeProps & { choose: (id: string) => void }) {
  const summary = learnerSummary(data.attempts, data.assignments, child.id);
  return (
    <div className="ak-live-home">
      <PageHeader
        eyebrow="FAMILY OVERVIEW"
        title="Your family, moving forward."
        description="A clear view of their learning, and where a little support can help."
        action={
          <Button onClick={() => go('assignments')}>
            Assign practice <ArrowRight size={16} />
          </Button>
        }
      />
      <div className="ak-dashboard-heading">
        <div>
          <h2>Your learner’s week</h2>
          <p>Choose a learner to see their assignments and recent work.</p>
        </div>
        <ChildSwitcher
          learners={data.students}
          value={child.id}
          onChange={choose}
        />
      </div>
      <StudentSummaryCard
        avatar={child.avatar}
        name={child.name}
        grade={child.grade}
        term={child.term}
        subjects={child.subjects.map((id) => subjectName(data, id))}
        action={
          <Button variant="outline" onClick={() => go('students')}>
            View courses <ArrowRight size={16} />
          </Button>
        }
      />
      <div className="ak-metrics">
        <MetricCard
          label="Questions this week"
          value={summary.weekly.length}
          detail="Attempts since Monday"
          icon={ClipboardCheck}
        />
        <MetricCard
          label="Enrolled subjects"
          value={child.subjects.length}
          detail={`${child.grade} · ${child.term}`}
          icon={BookOpen}
          tone="violet"
        />
        <MetricCard
          label="Active assignments"
          value={summary.assignments.length}
          detail="For the selected learner"
          icon={CalendarDays}
          tone="amber"
        />
        <MetricCard
          label="Awaiting review"
          value={summary.pending.length}
          detail="Answers ready for feedback"
          icon={TrendingUp}
          tone="green"
        />
      </div>
      <LearningOverview data={data} child={child} go={go} parent />
    </div>
  );
}
export function StudentHome({ data, child, go }: HomeProps) {
  const summary = learnerSummary(data.attempts, data.assignments, child.id);
  const next = summary.assignments[0];
  const start = () => {
    if (next) {
      sessionStorage.setItem('akuru-next-question', next.questionId);
      go('practice', next.subject);
    } else if (child.subjects.length) go('practice', child.subjects[0]);
    else go('subjects');
  };
  return (
    <div className="ak-live-home">
      <PageHeader
        eyebrow={`${child.grade.toUpperCase()} · YOUR LEARNING JOURNEY`}
        title={`Welcome back, ${child.name}.`}
        description="A fresh question. A new connection. A little more confidence."
        action={
          <Button variant="outline" onClick={() => go('plan')}>
            <CalendarDays size={16} /> Study plan
          </Button>
        }
      />
      <div className="ak-next-step">
        <div>
          <span className="ak-eyebrow">
            {next ? 'YOUR NEXT ASSIGNMENT' : 'TODAY’S FOCUS'}
          </span>
          <h2>{next?.title ?? 'Small steps. Bigger understanding.'}</h2>
          <p>
            {next
              ? `${subjectName(data, next.subject)} · Due ${next.due}`
              : 'Start with a question and see where your curiosity takes you.'}
          </p>
          <Button onClick={start}>
            {next ? 'Open assignment' : 'Let’s practise'}{' '}
            <ArrowRight size={16} />
          </Button>
        </div>
        <div className="bot-sticker bot-checklist" aria-hidden="true" />
      </div>
      <div className="ak-metrics">
        <MetricCard
          label="Questions this week"
          value={summary.weekly.length}
          detail="Attempts since Monday"
          icon={ClipboardCheck}
        />
        <MetricCard
          label="Subjects explored"
          value={new Set(summary.weekly.map((item) => item.subject)).size}
          detail="Practised this week"
          icon={BookOpen}
          tone="violet"
        />
        <MetricCard
          label="Assignments open"
          value={summary.assignments.length}
          detail="Your next learning steps"
          icon={CalendarDays}
          tone="amber"
        />
        <MetricCard
          label="Assignments completed"
          value={summary.completed}
          detail={`${summary.totalAssignments} assigned in total`}
          icon={TrendingUp}
          tone="green"
        />
      </div>
      <LearningOverview data={data} child={child} go={go} parent={false} />
    </div>
  );
}
