/** Presentation only: statuses and counts remain owned by the backend. */
export type BadgeTone =
  | 'success'
  | 'warning'
  | 'danger'
  | 'info'
  | 'neutral'
  | 'accent';
export type BadgeIcon =
  | 'check'
  | 'clock'
  | 'alert'
  | 'info'
  | 'eye'
  | 'hidden'
  | 'users';
const groups: Record<BadgeTone, string[]> = {
  success: [
    'approved',
    'published',
    'checked',
    'reviewed',
    'completed',
    'complete',
    'ready',
    'released',
    'passed',
    'confirmed',
    'enrolled',
    'resolved',
    'healthy',
    'on track',
    'available',
    'connected',
    'visible',
    'final document confirmed',
  ],
  warning: [
    'needs review',
    'awaiting review',
    'pending',
    'pending review',
    'review',
    'in review',
    'review required',
    'needs correction',
    'ready for approval',
    'name change required',
    'unreviewed',
    'partially reviewed',
    'partial',
    'due soon',
    'confirmation required',
    'attention required',
    'low',
    'limited',
    'medium',
    'exhausted',
    'paused',
  ],
  danger: [
    'failed',
    'error',
    'rejected',
    'blocked',
    'overdue',
    'needs attention',
    'urgent',
    'high',
    'critical',
    'unavailable',
  ],
  info: [
    'active',
    'in progress',
    'processing',
    'queued',
    'submitted',
    'scheduled',
    'running',
    'following',
    'follows you',
    'streaming',
    'live',
    'connecting',
    'reconnecting',
  ],
  neutral: [
    'draft',
    'hidden',
    'inactive',
    'archived',
    'superseded',
    'excluded',
    'dismissed',
    'disabled',
    'offline',
    'not started',
    'incomplete',
    'unpublished',
    'not ready',
    'not checked',
    'not configured',
  ],
  accent: ['following each other'],
};
const labels: Record<string, string> = {
  'needs review': 'Awaiting review',
  pending: 'Awaiting review',
  active: 'In progress',
  review: 'In review',
  'review required': 'Needs review',
  'pending review': 'Awaiting review',
  failed: 'Needs attention',
};
export function badgeStatus(status: string): {
  tone: BadgeTone;
  label: string;
  icon: BadgeIcon;
} {
  const normalized = status
    .trim()
    .toLowerCase()
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ');
  const tone =
    (Object.keys(groups) as BadgeTone[]).find((key) =>
      groups[key].includes(normalized),
    ) || 'neutral';
  const icon: BadgeIcon =
    normalized === 'visible'
      ? 'eye'
      : normalized === 'hidden'
        ? 'hidden'
        : ['following', 'follows you', 'following each other'].includes(
              normalized,
            )
          ? 'users'
          : tone === 'success'
            ? 'check'
            : tone === 'danger'
              ? 'alert'
              : tone === 'warning' || tone === 'info'
                ? 'clock'
                : 'info';
  return {
    tone,
    label:
      labels[normalized] ||
      (normalized
        ? normalized[0].toUpperCase() + normalized.slice(1)
        : 'Not specified'),
    icon,
  };
}
export function badgeCount(count: number): string {
  const safe = Number.isFinite(count) ? Math.max(0, Math.floor(count)) : 0;
  return safe > 99 ? '99+' : String(safe);
}
