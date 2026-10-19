import type { ReactNode } from 'react';
import {
  CheckCircle2,
  Clock3,
  CircleAlert,
  Info,
  Eye,
  EyeOff,
  Users,
} from 'lucide-react';
import { badgeStatus, badgeCount, type BadgeTone } from '@/lib/badges';
const icons = {
  check: CheckCircle2,
  clock: Clock3,
  alert: CircleAlert,
  info: Info,
  eye: Eye,
  hidden: EyeOff,
  users: Users,
};
export function StatusBadge({
  status,
  label,
  size = 'sm',
  tone,
}: {
  status: string;
  label?: string;
  size?: 'xs' | 'sm';
  tone?: BadgeTone;
}) {
  const presentation = badgeStatus(status),
    text = label || presentation.label,
    Icon = icons[presentation.icon];
  return (
    <span
      className="ak-badge ak-badge-status"
      data-tone={tone || presentation.tone}
      data-size={size}
      aria-label={`Status: ${text}`}
    >
      <Icon aria-hidden="true" />
      <span>{text}</span>
    </span>
  );
}
export function MetadataBadge({
  children,
  size = 'sm',
}: {
  children: ReactNode;
  size?: 'xs' | 'sm';
}) {
  return (
    <span
      className="ak-badge ak-badge-meta"
      data-tone="neutral"
      data-size={size}
    >
      {children}
    </span>
  );
}
export function CountBadge({ count, label }: { count: number; label: string }) {
  return (
    <span
      className="ak-badge ak-badge-count"
      data-tone="info"
      aria-label={`${Math.max(0, Math.floor(Number.isFinite(count) ? count : 0))} ${label}`}
    >
      {badgeCount(count)}
    </span>
  );
}

export function ReviewBadge({
  state,
  children,
}: {
  state: 'required' | 'partial' | 'complete';
  children: string;
}) {
  return (
    <StatusBadge
      status={
        state === 'complete'
          ? 'reviewed'
          : state === 'partial'
            ? 'partially reviewed'
            : 'review required'
      }
      label={children}
    />
  );
}
