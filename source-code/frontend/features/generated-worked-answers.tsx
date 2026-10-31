'use client';
/* eslint-disable jsx-a11y/label-has-associated-control */
import { useEffect, useState } from 'react';
import { request } from '@/api/core/client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { DashboardCard } from '@/components/portal/dashboard-widgets';
import { toast } from '@/components/ui/toast';
import { LearningImage } from './learning-media';

type Axis = { label: string; minimum: number; maximum: number; tick: number };
type Step = {
  partLabel: string;
  explanation: string;
  showPoints: boolean;
  circleIndexes: number[];
  fits: { pointIndexes: number[]; fromX: number; toX: number; label: string }[];
};
type Solution = {
  schemaVersion: 'graph-v1';
  title: string;
  xAxis: Axis;
  yAxis: Axis;
  points: { x: number; y: number }[];
  steps: Step[];
  limitations: string;
};
type WorkedAnswer = {
  id: string;
  revision: number;
  status: string;
  solution: Solution | null;
  errorCode?: string;
  label: string;
  sourceHash: string;
  sourceManifest: {
    versions: {
      role: string;
      filename: string;
      version: number;
      sha256: string;
    }[];
  };
  graphInput: { verificationNote: string };
  provenance: { model?: string; checks?: string[] };
};
const emptyAxis = (): Axis => ({
  label: '',
  minimum: 0,
  maximum: 40,
  tick: 10,
});

export function GeneratedWorkedAnswers({
  paperId,
  number,
  revision,
  parts,
  dirty,
  onAttached,
  onDraftChange,
}: {
  paperId: string;
  number: string;
  revision: number;
  parts: { label: string }[];
  dirty: boolean;
  onAttached: () => void;
  onDraftChange: (dirty: boolean) => void;
}) {
  const root = `admin/official-paper-reviews/${paperId}/questions/${encodeURIComponent(number)}/worked-answers`;
  const [rows, setRows] = useState<WorkedAnswer[]>([]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [ready, setReady] = useState(false);
  const [xAxis, setX] = useState(emptyAxis);
  const [yAxis, setY] = useState(emptyAxis);
  const [points, setPoints] = useState('');
  const [selected, setSelected] = useState<string[]>([]);
  const [note, setNote] = useState('');
  const [reviewNote, setReviewNote] = useState('');
  const [edit, setEdit] = useState<Solution | null>(null);
  const [editingId, setEditingId] = useState('');
  useEffect(() => {
    onDraftChange(
      Boolean(
        edit &&
        JSON.stringify(edit) !==
          JSON.stringify(rows.find((row) => row.id === editingId)?.solution),
      ),
    );
    return () => onDraftChange(false);
  }, [edit, editingId, rows, onDraftChange]);
  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const [result, capability] = await Promise.all([
          request<WorkedAnswer[]>(root),
          request<{ ready: boolean }>(
            `admin/official-paper-reviews/${paperId}/worked-answer-capabilities`,
          ),
        ]);
        if (active) {
          setRows(result);
          setReady(capability.ready);
        }
      } catch (e) {
        if (active) {
          const message =
            e instanceof Error ? e.message : 'Unable to load worked answers.';
          setError(message);
        }
      }
    }
    void load();
    const timer = setInterval(() => void load(), 8000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [root, paperId]);
  async function run(action: () => Promise<unknown>, message: string) {
    setBusy(true);
    setError('');
    try {
      await action();
      setRows(await request<WorkedAnswer[]>(root));
      toast.add({ title: message, type: 'success' });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Request failed.');
    } finally {
      setBusy(false);
    }
  }
  async function generate(regenerate = false) {
    const values = points
      .trim()
      .split('\n')
      .map((line) =>
        line
          .trim()
          .split(/[,\s]+/)
          .map(Number),
      );
    if (
      values.length < 2 ||
      values.some((v) => v.length !== 2 || v.some((n) => !Number.isFinite(n)))
    ) {
      setError('Enter one x and y pair per line, separated by a comma.');
      return;
    }
    await run(
      () =>
        request(root, {
          method: 'POST',
          body: {
            expectedQuestionRevision: revision,
            regenerate,
            graph: {
              xAxis,
              yAxis,
              points: values.map(([x, y]) => ({ x, y })),
              partLabels: selected,
              verificationNote: note,
            },
          },
        }),
      'Worked answer queued. It will need scientific review.',
    );
  }
  return (
    <DashboardCard
      title="AI-generated worked answers"
      description="Generate a private graph solution from verified data, then review it before attaching it to the question."
    >
      <div className="stack">
        <p>
          AI-generated worked answer — not an official Pearson answer. Official
          marking rules remain authoritative.
        </p>
        {error && <p role="alert">{error}</p>}
        {!ready && (
          <output>
            Generation is not configured. An operator must enable worked answers
            and configure an enabled OpenAI account. Existing approved answers
            can still be reviewed.
          </output>
        )}
        <details>
          <summary>Generate a graph solution</summary>
          <div className="stack">
            <p>
              Verify the values and axes against the original paper first. This
              version supports plotted points, anomaly circles and straight
              best-fit lines.
            </p>
            {[
              { name: 'Horizontal axis', value: xAxis, set: setX },
              { name: 'Vertical axis', value: yAxis, set: setY },
            ].map((axis) => (
              <fieldset key={axis.name}>
                <legend>{axis.name}</legend>
                <div className="form-grid">
                  <label>
                    Label including units
                    <Input
                      value={axis.value.label}
                      onChange={(e) =>
                        axis.set({ ...axis.value, label: e.target.value })
                      }
                    />
                  </label>
                  {(['minimum', 'maximum', 'tick'] as const).map((key) => (
                    <label key={key}>
                      {key}
                      <Input
                        type="number"
                        step="any"
                        value={axis.value[key]}
                        onChange={(e) =>
                          axis.set({
                            ...axis.value,
                            [key]: Number(e.target.value),
                          })
                        }
                      />
                    </label>
                  ))}
                </div>
              </fieldset>
            ))}
            <label>
              Verified data: x, y — one pair per line
              <Textarea
                value={points}
                onChange={(e) => setPoints(e.target.value)}
                placeholder={'0, 21.0\n5, 22.3'}
              />
            </label>
            <fieldset>
              <legend>Subparts to explain</legend>
              {parts.map((p) => (
                <label key={p.label} style={{ marginRight: 16 }}>
                  <input
                    type="checkbox"
                    checked={selected.includes(p.label)}
                    onChange={(e) =>
                      setSelected(
                        e.target.checked
                          ? [...selected, p.label]
                          : selected.filter((v) => v !== p.label),
                      )
                    }
                  />{' '}
                  {p.label}
                </label>
              ))}
            </fieldset>
            <label>
              Source verification note (at least 20 characters)
              <Textarea
                value={note}
                onChange={(e) => setNote(e.target.value)}
              />
            </label>
            {dirty && (
              <p>
                Save your question changes before generating or attaching an
                answer.
              </p>
            )}
            <Button
              disabled={
                busy ||
                dirty ||
                !ready ||
                !revision ||
                note.trim().length < 20 ||
                !selected.length
              }
              onClick={() => void generate()}
            >
              Generate draft
            </Button>
            {rows.length > 0 && (
              <Button
                variant="outline"
                disabled={
                  busy ||
                  dirty ||
                  !ready ||
                  note.trim().length < 20 ||
                  !selected.length
                }
                onClick={() => void generate(true)}
              >
                Generate a replacement draft
              </Button>
            )}
          </div>
        </details>
        {rows.map((row) => (
          <section className="panel stack" key={row.id}>
            <strong>{row.label}</strong>
            <p>
              Status: {row.status.replaceAll('_', ' ')} · revision{' '}
              {row.revision}
              {row.provenance?.model ? ` · ${row.provenance.model}` : ''}
            </p>
            <details>
              <summary>Verified source versions</summary>
              <p>{row.graphInput?.verificationNote}</p>
              <p className="small">
                Source fingerprint: {row.sourceHash?.slice(0, 16)}
              </p>
              <ul>
                {row.sourceManifest?.versions?.map((source) => (
                  <li key={source.role}>
                    {source.role}: {source.filename} · version {source.version}{' '}
                    · checksum {source.sha256.slice(0, 16)}
                  </li>
                ))}
              </ul>
            </details>
            {row.errorCode && (
              <p role="alert">
                Generation failed: {row.errorCode}. Check inputs and provider
                settings before generating again.
              </p>
            )}
            {row.solution?.steps?.map((step, index) => (
              <details key={step.partLabel}>
                <summary>Part {step.partLabel} — preview worked answer</summary>
                <LearningImage
                  src={`/api/v1/${root}/${row.id}/steps/${index}/image?revision=${row.revision}`}
                  description={step.explanation}
                />
                <p>{step.explanation}</p>
                <p className="small">{row.solution?.limitations}</p>
              </details>
            ))}
            {row.provenance?.checks && (
              <p className="small">
                Checks: {row.provenance.checks.join('; ')}. Scientific
                correctness still needs review.
              </p>
            )}
            {['awaiting_review', 'approved', 'rejected'].includes(
              row.status,
            ) && (
              <>
                <label>
                  Review note (at least 20 characters)
                  <Textarea
                    value={reviewNote}
                    onChange={(e) => setReviewNote(e.target.value)}
                  />
                </label>
                <div className="button-row">
                  <Button
                    variant="outline"
                    onClick={() => {
                      setEditingId(row.id);
                      setEdit(structuredClone(row.solution));
                    }}
                  >
                    Edit explanation and plotting instructions
                  </Button>
                  <Button
                    disabled={busy || reviewNote.trim().length < 20}
                    onClick={() =>
                      void run(
                        () =>
                          request(`${root}/${row.id}/review`, {
                            method: 'POST',
                            body: {
                              expectedRevision: row.revision,
                              action: 'approve',
                              reviewNote,
                            },
                          }),
                        'Worked answer approved. Attach it to the question before release.',
                      )
                    }
                  >
                    Approve worked answer
                  </Button>
                  <Button
                    variant="outline"
                    disabled={busy || reviewNote.trim().length < 20}
                    onClick={() =>
                      void run(
                        () =>
                          request(`${root}/${row.id}/review`, {
                            method: 'POST',
                            body: {
                              expectedRevision: row.revision,
                              action: 'reject',
                              reviewNote,
                            },
                          }),
                        'Worked answer rejected.',
                      )
                    }
                  >
                    Reject
                  </Button>
                </div>
                {editingId === row.id && edit && (
                  <div className="stack">
                    <label>
                      Title
                      <Input
                        value={edit.title}
                        onChange={(e) =>
                          setEdit({ ...edit, title: e.target.value })
                        }
                      />
                    </label>
                    {edit.steps.map((step, i) => (
                      <fieldset key={step.partLabel}>
                        <legend>Part {step.partLabel}</legend>
                        <label>
                          Explanation
                          <Textarea
                            value={step.explanation}
                            onChange={(e) =>
                              setEdit({
                                ...edit,
                                steps: edit.steps.map((s, j) =>
                                  j === i
                                    ? { ...s, explanation: e.target.value }
                                    : s,
                                ),
                              })
                            }
                          />
                        </label>
                        <p className="small">
                          Data points are numbered from 1. Verified source
                          values are immutable; generate again to correct source
                          inputs.
                        </p>
                        <label>
                          Circle point numbers, separated by commas
                          <Input
                            value={step.circleIndexes
                              .map((n) => n + 1)
                              .join(',')}
                            onChange={(e) =>
                              setEdit({
                                ...edit,
                                steps: edit.steps.map((s, j) =>
                                  j === i
                                    ? {
                                        ...s,
                                        circleIndexes: e.target.value.trim()
                                          ? e.target.value
                                              .split(',')
                                              .map((n) => Number(n) - 1)
                                          : [],
                                      }
                                    : s,
                                ),
                              })
                            }
                          />
                        </label>
                        {step.fits.map((fit, k) => (
                          <div className="form-grid" key={k}>
                            <label>
                              Line: {fit.label} · point numbers
                              <Input
                                value={fit.pointIndexes
                                  .map((n) => n + 1)
                                  .join(',')}
                                onChange={(e) =>
                                  setEdit({
                                    ...edit,
                                    steps: edit.steps.map((s, j) =>
                                      j === i
                                        ? {
                                            ...s,
                                            fits: s.fits.map((f, l) =>
                                              l === k
                                                ? {
                                                    ...f,
                                                    pointIndexes: e.target.value
                                                      .split(',')
                                                      .map(
                                                        (n) => Number(n) - 1,
                                                      ),
                                                  }
                                                : f,
                                            ),
                                          }
                                        : s,
                                    ),
                                  })
                                }
                              />
                            </label>
                            {(['fromX', 'toX'] as const).map((key) => (
                              <label key={key}>
                                {key}
                                <Input
                                  type="number"
                                  step="any"
                                  value={fit[key]}
                                  onChange={(e) =>
                                    setEdit({
                                      ...edit,
                                      steps: edit.steps.map((s, j) =>
                                        j === i
                                          ? {
                                              ...s,
                                              fits: s.fits.map((f, l) =>
                                                l === k
                                                  ? {
                                                      ...f,
                                                      [key]: Number(
                                                        e.target.value,
                                                      ),
                                                    }
                                                  : f,
                                              ),
                                            }
                                          : s,
                                      ),
                                    })
                                  }
                                />
                              </label>
                            ))}
                          </div>
                        ))}
                      </fieldset>
                    ))}
                    <label>
                      Limitations
                      <Textarea
                        value={edit.limitations}
                        onChange={(e) =>
                          setEdit({ ...edit, limitations: e.target.value })
                        }
                      />
                    </label>
                    <Button
                      disabled={busy || reviewNote.trim().length < 20}
                      onClick={() =>
                        void run(async () => {
                          await request(`${root}/${row.id}/review`, {
                            method: 'POST',
                            body: {
                              expectedRevision: row.revision,
                              action: 'edit',
                              solution: edit,
                              reviewNote,
                            },
                          });
                          setEdit(null);
                          setEditingId('');
                        }, 'Edits saved. Preview and approve the revised answer.')
                      }
                    >
                      Save edited draft
                    </Button>
                  </div>
                )}
                {row.status === 'approved' && (
                  <Button
                    disabled={busy || dirty}
                    onClick={() =>
                      void run(async () => {
                        await request(`${root}/${row.id}/attach`, {
                          method: 'POST',
                          body: { expectedQuestionRevision: revision },
                        });
                        onAttached();
                      }, 'Approved generated answer attached. Review the question before publishing.')
                    }
                  >
                    Attach approved answer to question
                  </Button>
                )}
              </>
            )}
          </section>
        ))}
      </div>
    </DashboardCard>
  );
}
