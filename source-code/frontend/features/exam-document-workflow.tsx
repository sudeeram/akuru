'use client';
import { useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { request } from '@/api/core/client';
import type { Schemas } from '@/lib/generated/api-contract';

type Workflow = Schemas['DocumentWorkflow'];
export function useExamWorkflows(ids: string[], refreshVersion: unknown) {
  const key = [...ids].sort().join(',');
  const client = useQueryClient();
  const query = useQuery({
    queryKey: ['admin', 'exam-workflows', key],
    enabled: Boolean(key),
    retry: false,
    refetchInterval: 15000,
    queryFn: async () => {
      const values = key.split(',');
      const groups = [];
      for (let i = 0; i < values.length; i += 100)
        groups.push(values.slice(i, i + 100));
      const responses = await Promise.all(
        groups.map((group) =>
          request<Schemas['WorkflowResponse']>(
            `admin/official-paper-reviews/workflow?${new URLSearchParams(group.map((id) => ['documentId', id]))}`,
          ),
        ),
      );
      return Object.fromEntries(
        responses
          .flatMap((r) => r.documents || [])
          .map((r) => [r.documentId, r]),
      ) as Record<string, Workflow>;
    },
  });
  useEffect(() => {
    if (key)
      void client.invalidateQueries({
        queryKey: ['admin', 'exam-workflows', key],
      });
  }, [key, client, refreshVersion]);
  return {
    data: query.isError ? {} : query.data || {},
    error: query.isError
      ? 'Workflow unavailable. Retry by refreshing the page.'
      : '',
  };
}

const colours = {
  not_started: { background: '#f1f5f9', color: '#475569', border: '#cbd5e1' },
  processing: { background: '#dbeafe', color: '#1d4ed8', border: '#93c5fd' },
  attention: { background: '#fef3c7', color: '#92400e', border: '#fcd34d' },
  complete: { background: '#dcfce7', color: '#166534', border: '#86efac' },
};
const labels = {
  not_started: 'Not started',
  processing: 'Processing',
  attention: 'Needs attention',
  complete: 'Complete',
};
export function ExamDocumentWorkflow({
  workflow,
  error,
  navigate,
}: {
  workflow?: Workflow;
  error: string;
  navigate: (href: string) => void;
}) {
  if (!workflow)
    return (
      <span role={error ? 'status' : undefined}>
        {error || 'Loading workflow…'}
      </span>
    );
  return (
    <div className="stack" style={{ minWidth: 300 }}>
      {workflow.scopes.map((scope) => (
        <div key={scope.paperId || 'unlinked'}>
          {workflow.scopes.length > 1 && <small>{scope.paperTitle}</small>}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: `repeat(${scope.steps.length}, minmax(0, 1fr))`,
              gap: 8,
            }}
          >
            {scope.steps.map((step) => (
              <details key={step.number}>
                <summary
                  aria-label={`${step.number}. ${step.label}: ${labels[step.state]}. ${step.checked != null ? `${step.checked}/${step.total} checked, ${step.completed} ready` : `${step.completed}/${step.total} complete`}`}
                  style={{ cursor: 'pointer', listStyle: 'none' }}
                >
                  <span
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: 30,
                      height: 30,
                      borderRadius: 5,
                      border: `1px solid ${colours[step.state].border}`,
                      background: colours[step.state].background,
                      color: colours[step.state].color,
                      fontWeight: 700,
                    }}
                  >
                    {step.number}
                  </span>
                  <span
                    style={{ display: 'block', fontSize: 11, maxWidth: 85 }}
                  >
                    {step.label}
                  </span>
                  <span style={{ display: 'block', fontSize: 11 }}>
                    {step.checked ?? step.completed}/{step.total}
                    {step.checked != null ? ' checked' : ''}
                  </span>
                  {step.checked != null && (
                    <small>{step.completed} ready</small>
                  )}
                </summary>
                <div style={{ maxWidth: 280 }}>
                  <strong>
                    {step.label} · {labels[step.state]}
                  </strong>
                  <p>{step.detail}</p>
                  <button
                    type="button"
                    className="text-link"
                    onClick={() => navigate(step.href)}
                  >
                    Open this step
                  </button>
                </div>
              </details>
            ))}
          </div>
          {scope.steps.length === 4 && (
            <small>
              Tutor practice · Formal exam:{' '}
              {scope.formalExamPublished ? 'published' : 'not published'}
            </small>
          )}
        </div>
      ))}
    </div>
  );
}
