'use client';
import { useState } from 'react';
import { csrfToken } from '@/api/core/csrf';

export function DrawingSubmissions({
  assessmentId,
  questionId,
  parts,
  files = {},
  disabled,
  onSaved,
}: {
  assessmentId: string;
  questionId: string;
  parts?: string[];
  files?: Record<string, string>;
  disabled?: boolean;
  onSaved: () => Promise<unknown>;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  if (!parts?.length) return null;
  return (
    <section className="panel stack" aria-label="Drawing answers">
      <h3>Your drawings</h3>
      <p>
        Upload a clear photo or PDF for each part. Include every required label
        and bond. You can replace it before submitting. Drawings are checked
        before a score is released.
      </p>
      {parts.map((part) => (
        <div key={part} className="stack">
          <label>
            Part ({part}) — {files[part] ? 'replace drawing' : 'upload drawing'}
            <input
              type="file"
              accept="image/png,image/jpeg,application/pdf"
              disabled={disabled || busy}
              onChange={async (event) => {
                const file = event.target.files?.[0];
                if (!file) return;
                setError('');
                setBusy(true);
                try {
                  if (file.size > 5 * 1024 * 1024)
                    throw new Error('Choose a file smaller than 5 MB.');
                  const csrf = csrfToken();
                  const response = await fetch(
                    `/api/v1/assessments/${assessmentId}/questions/${questionId}/drawings/${encodeURIComponent(part)}`,
                    {
                      method: 'POST',
                      headers: {
                        'Content-Type': file.type,
                        'X-Filename': file.name,
                        ...(csrf ? { 'X-CSRF-Token': csrf } : {}),
                      },
                      body: file,
                    },
                  );
                  const body = (await response.json()) as {
                    error?: { message?: string };
                  };
                  if (!response.ok)
                    throw new Error(
                      body?.error?.message || 'Drawing could not be saved.',
                    );
                  await onSaved();
                } catch (cause) {
                  setError(
                    cause instanceof Error
                      ? cause.message
                      : 'Drawing could not be saved.',
                  );
                } finally {
                  setBusy(false);
                  event.target.value = '';
                }
              }}
            />
          </label>
          {files[part] && (
            <a
              href={`/api/v1/assessments/${assessmentId}/working/${files[part]}`}
              target="_blank"
              rel="noreferrer"
            >
              View saved drawing for ({part})
            </a>
          )}
        </div>
      ))}
      {busy && <output>Saving drawing…</output>}
      {error && <p role="alert">{error}</p>}
    </section>
  );
}
