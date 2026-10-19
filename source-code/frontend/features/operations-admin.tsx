'use client';
/* eslint-disable react/react-compiler */
import { useCallback, useEffect, useState } from 'react';
import { api, errorMessage } from '@/api';
import { Button } from '@/components/ui/button';
import {
  DashboardCard,
  MetricCard,
} from '@/components/portal/dashboard-widgets';
import { Activity, TriangleAlert } from 'lucide-react';
import { LoadingState } from '@/components/portal/workspace';
import { Empty } from './shared';

type Operations = {
  documentJobs: Record<string, number>;
  last24Hours: {
    aiCalls: number;
    aiTokens: number;
    familyTokens: number;
    aiFailures: number;
    averageLatencyMs: number;
  };
  alerts: string[];
  recentAudit: { action: string; targetType: string; createdAt: string }[];
};

export function OperationsAdmin() {
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);
  const [data, setData] = useState<Operations | null>(null),
    [error, setError] = useState(''),
    [loading, setLoading] = useState(true);
  const load = useCallback(async () => {
    setLoading(true);
    try {
      setData((await api('operations/admin/status')) as Operations);
      setError('');
      setUpdatedAt(new Date());
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    void load();
  }, [load]);
  if (loading && !data)
    return <LoadingState message="Loading operational status…" />;
  if (error)
    return (
      <section className="panel stack">
        <div className="error" role="alert">
          {error}
        </div>
        <Button onClick={() => void load()}>Retry</Button>
      </section>
    );
  if (!data)
    return (
      <Empty title="Status unavailable">
        AKURU could not load operational status.
      </Empty>
    );
  return (
    <div className="stack">
      <div className="spread">
        <p className="small">
          Last refreshed: {updatedAt?.toLocaleTimeString() || 'Not yet loaded'}
        </p>
        <Button
          variant="outline"
          disabled={loading}
          onClick={() => void load()}
        >
          {loading ? 'Refreshing…' : 'Refresh status'}
        </Button>
      </div>
      <DashboardCard title="Operational alerts">
        {data.alerts.length ? (
          data.alerts.map((alert) => (
            <div className="error" key={alert}>
              {alert}
            </div>
          ))
        ) : (
          <div className="success">No active job or provider alerts.</div>
        )}
      </DashboardCard>
      <section className="metric-grid">
        {[
          ['AI calls · 24h', data.last24Hours.aiCalls],
          ['Provider tokens · 24h', data.last24Hours.aiTokens],
          ['Family tokens · 24h', data.last24Hours.familyTokens],
          ['AI failures · 24h', data.last24Hours.aiFailures],
          ['Average AI latency', `${data.last24Hours.averageLatencyMs} ms`],
          ['Failed document jobs', data.documentJobs.failed || 0],
        ].map(([label, value]) => (
          <MetricCard
            key={label}
            label={String(label)}
            value={value}
            detail="Existing operational summary"
            icon={String(label).includes('fail') ? TriangleAlert : Activity}
          />
        ))}
      </section>
      <DashboardCard title="Recent security and content audit">
        {data.recentAudit.length ? (
          data.recentAudit.map((event, index) => (
            <article className="card" key={`${event.createdAt}-${index}`}>
              <strong>{event.action}</strong>
              <p>
                {event.targetType} ·{' '}
                {new Date(event.createdAt).toLocaleString()}
              </p>
            </article>
          ))
        ) : (
          <Empty title="No audit events yet">
            Administrative actions will appear here.
          </Empty>
        )}
      </DashboardCard>
    </div>
  );
}
