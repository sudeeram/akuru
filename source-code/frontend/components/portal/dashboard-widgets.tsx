'use client';

import type { ReactNode } from 'react';
import {
  ArrowUpRight,
  BookOpen,
  CircleAlert,
  Inbox,
  type LucideIcon,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';

export function PageHeader({
  eyebrow,
  title,
  description,
  action,
  level = 1,
}: {
  eyebrow?: string;
  title: string;
  description?: ReactNode;
  action?: ReactNode;
  level?: 1 | 2;
}) {
  const Title = level === 1 ? 'h1' : 'h2';
  return (
    <div className="ak-page-heading page-heading">
      <div>
        {eyebrow && <span className="ak-eyebrow">{eyebrow}</span>}
        <Title>{title}</Title>
        {description && <p>{description}</p>}
      </div>
      {action}
    </div>
  );
}
export function DashboardCard({
  title,
  description,
  action,
  children,
  className = '',
}: {
  title: string;
  description?: ReactNode;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`ak-card ${className}`}>
      <div className="ak-card-heading">
        <div>
          <h2>{title}</h2>
          {description && <p>{description}</p>}
        </div>
        {action}
      </div>
      <div className="ak-card-body">{children}</div>
    </section>
  );
}
export function MetricCard({
  label,
  value,
  detail,
  icon: Icon,
  tone = 'blue',
}: {
  label: string;
  value: ReactNode;
  detail: string;
  icon: LucideIcon;
  tone?: string;
}) {
  return (
    <article className="ak-metric">
      <div className={`ak-icon ak-tone-${tone}`}>
        <Icon size={21} />
      </div>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  );
}
export function ChildSwitcher({
  learners,
  value,
  onChange,
}: {
  learners: { id: string; name: string; grade: string }[];
  value: string;
  onChange: (id: string) => void;
}) {
  return (
    <label className="ak-field ak-child-switcher">
      <span>Learner</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {learners.map((child) => (
          <option key={child.id} value={child.id}>
            {child.name} · {child.grade}
          </option>
        ))}
      </select>
    </label>
  );
}
export function StudentSummaryCard({
  name,
  grade,
  term,
  subjects,
  action,
}: {
  name: string;
  grade: string;
  term: string;
  subjects: string[];
  action?: ReactNode;
}) {
  return (
    <section className="ak-student-summary">
      <span className="ak-student-avatar">
        {name
          .split(' ')
          .map((word) => word[0])
          .slice(0, 2)
          .join('')}
      </span>
      <div>
        <span className="ak-eyebrow">LEARNER OVERVIEW</span>
        <h2>{name}</h2>
        <p>
          {grade} · {term}
        </p>
        <div className="ak-chips">
          {subjects.map((subject) => (
            <span key={subject}>{subject}</span>
          ))}
        </div>
      </div>
      {action && <div className="ak-summary-action">{action}</div>}
    </section>
  );
}
export function SubjectProgressCard({
  title,
  description,
  value,
  label,
  onOpen,
}: {
  title: string;
  description: ReactNode;
  value: number | null;
  label: string;
  onOpen?: () => void;
}) {
  return (
    <article className="ak-subject-progress">
      <div className="ak-row">
        <span className="ak-icon ak-tone-blue">
          <BookOpen size={18} />
        </span>
        <div>
          <h3>{title}</h3>
          <p>{description}</p>
        </div>
        {onOpen && (
          <Button
            variant="ghost"
            size="icon"
            aria-label={`Open ${title}`}
            onClick={onOpen}
          >
            <ArrowUpRight />
          </Button>
        )}
      </div>
      <div className="ak-progress-label">
        <span>{label}</span>
        <strong>
          {value === null ? 'Not available' : `${Math.round(value)}%`}
        </strong>
      </div>
      {value !== null && (
        <Progress value={value} aria-label={`${title}: ${label}`} />
      )}
    </article>
  );
}
export type ActivityItem = {
  id: string;
  title: string;
  detail: string;
  date: string;
};
export function ActivityTimeline({ items }: { items: ActivityItem[] }) {
  return items.length ? (
    <ol className="ak-timeline">
      {items.map((item) => (
        <li key={item.id}>
          <span className="ak-timeline-dot" />
          <div>
            <strong>{item.title}</strong>
            <p>{item.detail}</p>
            <small>{item.date}</small>
          </div>
        </li>
      ))}
    </ol>
  ) : (
    <EmptyState
      title="No recent activity"
      description="Completed learning activities will appear here."
    />
  );
}
export type AssignmentItem = {
  id: string;
  title: string;
  subject: string;
  due: string;
  status: string;
};
export function AssignmentList({
  items,
  onOpen,
}: {
  items: AssignmentItem[];
  onOpen: (item: AssignmentItem) => void;
}) {
  return items.length ? (
    <div className="ak-assignment-list">
      {items.map((item) => (
        <button type="button" key={item.id} onClick={() => onOpen(item)}>
          <span className="ak-icon ak-tone-violet">
            <BookOpen size={18} />
          </span>
          <span className="ak-assignment-copy">
            <strong>{item.title}</strong>
            <small>
              {item.subject} · {item.due}
            </small>
          </span>
          <StatusPill status={item.status} />
          <ArrowUpRight size={16} />
        </button>
      ))}
    </div>
  ) : (
    <EmptyState
      title="All caught up"
      description="New assignments will appear here when they are ready."
    />
  );
}
export function StatusPill({ status }: { status: string }) {
  const tone = /overdue|failed/i.test(status)
    ? 'rose'
    : /review|due|pending/i.test(status)
      ? 'amber'
      : /complete|published|ready|checked/i.test(status)
        ? 'green'
        : /failed|overdue/i.test(status)
          ? 'rose'
          : 'blue';
  return <span className={`ak-status ak-tone-${tone}`}>{status}</span>;
}
export function EmptyState({
  title,
  description,
  action,
  error = false,
}: {
  title: string;
  description: ReactNode;
  action?: ReactNode;
  error?: boolean;
}) {
  const Icon = error ? CircleAlert : Inbox;
  return (
    <div className="ak-empty" role={error ? 'alert' : undefined}>
      <Icon size={30} />
      <h3>{title}</h3>
      <p>{description}</p>
      {action}
    </div>
  );
}
export function DashboardSkeleton() {
  return (
    <output className="ak-skeleton" aria-label="Loading dashboard">
      <span className="sr-only">Loading dashboard…</span>
      <div />
      <div className="ak-metrics">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} />
        ))}
      </div>
      <div />
    </output>
  );
}
