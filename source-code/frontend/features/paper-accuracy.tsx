'use client';
import { useEffect, useRef, useState } from 'react';
import { getPaperReview, type PaperReview, type Doc } from '@/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  DashboardCard,
  PageHeader,
} from '@/components/portal/dashboard-widgets';
import { StatusBadge } from '@/components/portal/badges';
import {
  reviewAccuracyRows,
  reviewProvenance,
} from '@/lib/paper-review-presentation';
import { QuestionAnalysisPanel } from './question-analysis';

export function PaperAccuracyPage({
  paperId,
  documents,
  navigate,
}: {
  paperId: string;
  documents: Doc[];
  navigate: (path: string) => void;
}) {
  const [review, setReview] = useState<PaperReview | null>(null);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [model, setModel] = useState('');
  const [scope, setScope] = useState('all');
  const [lowestFirst, setLowestFirst] = useState(true);
  const [selected, setSelected] = useState<{
    number: string;
    part?: string;
  } | null>(null);
  const details = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (selected) details.current?.scrollIntoView({ block: 'start' });
  }, [selected]);
  useEffect(() => {
    let active = true;
    void getPaperReview(paperId)
      .then((value) => {
        if (active) setReview(value);
      })
      .catch((cause) => {
        if (active)
          setError(
            cause instanceof Error
              ? cause.message
              : 'Unable to load paper accuracy.',
          );
      });
    return () => {
      active = false;
    };
  }, [paperId]);
  const name =
    documents.find((document) => document.id === paperId)?.name ||
    'Official paper';
  const rows = reviewAccuracyRows(
    review?.questions || [],
    search,
    model,
    scope,
    lowestFirst,
  );
  const chosen = review?.questions.find(
    (question) => question.number === selected?.number,
  );
  const openReview = (number?: string, part?: string) => {
    const query = new URLSearchParams();
    if (number) query.set('record', number);
    if (part !== undefined) query.set('section', part);
    navigate(
      `/admin/exam-documents/review/${paperId}${query.size ? `?${query}` : ''}`,
    );
  };
  return (
    <div className="stack">
      <PageHeader
        title="Paper accuracy confidence"
        eyebrow="EXAM DOCUMENTS"
        description={name}
        action={
          <Button variant="outline" onClick={() => openReview()}>
            Back to question review
          </Button>
        }
      />
      <p>
        Question and subpart confidence estimates are separate from approval.
        Overall question confidence follows the weakest subpart. Open details to
        see source checks, reasons, models and history.
      </p>
      {error && <p role="alert">{error}</p>}
      {!review && !error && <output>Loading accuracy assessments…</output>}
      {review && (
        <DashboardCard
          title="Questions and subparts"
          description={`${review.questionCount} questions · ${review.questions.reduce((sum, question) => sum + question.data.parts.length, 0)} subparts`}
        >
          <div className="stack">
            <div className="form-grid">
              <label htmlFor="accuracy-question">
                Find question
                <Input
                  id="accuracy-question"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Question 4"
                />
              </label>
              <label htmlFor="accuracy-model">
                Model or method
                <Input
                  id="accuracy-model"
                  value={model}
                  onChange={(event) => setModel(event.target.value)}
                />
              </label>
              <label>
                Show
                <select
                  value={scope}
                  onChange={(event) => setScope(event.target.value)}
                >
                  <option value="all">Questions and subparts</option>
                  <option value="questions">Questions only</option>
                  <option value="subparts">Subparts only</option>
                </select>
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={lowestFirst}
                  onChange={(event) => setLowestFirst(event.target.checked)}
                />{' '}
                Lowest confidence first
              </label>
            </div>
            {/* Keyboard focus lets users scroll a wide table without a pointer. */}
            {/* oxlint-disable jsx-a11y/no-noninteractive-tabindex */}
            <section
              className="admin-table-wrap"
              style={{ overflowX: 'auto' }}
              tabIndex={0}
              aria-label="Accuracy confidence table"
            >
              <table
                className="admin-table"
                style={{ minWidth: 980, width: '100%' }}
              >
                <caption>
                  Accuracy confidence for each question and subpart
                </caption>
                <thead>
                  <tr>
                    <th scope="col">Question / part</th>
                    <th scope="col">Marks</th>
                    <th scope="col">Review status</th>
                    <th scope="col">Confidence</th>
                    <th scope="col">Paper</th>
                    <th scope="col">Scheme</th>
                    <th scope="col">Report</th>
                    <th scope="col">Assessed</th>
                    <th scope="col">Model</th>
                    <th scope="col">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => {
                    const provenance = row.analysis
                      ? reviewProvenance(row.analysis, row.label)
                      : [];
                    const models = [
                      ...new Set(
                        provenance.map(
                          (source) =>
                            source.modelName ||
                            source.modelId ||
                            'Not recorded',
                        ),
                      ),
                    ];
                    return (
                      <tr
                        key={`${row.question.number}-${row.label ?? 'question'}`}
                      >
                        <th scope="row">
                          Q{row.question.number}
                          {row.label !== undefined
                            ? ` (${row.label})`
                            : ' · overall'}
                        </th>
                        <td>{row.marks}</td>
                        <td>
                          <StatusBadge
                            status={row.status}
                            label={row.status.replaceAll('_', ' ')}
                            size="xs"
                          />
                        </td>
                        <td>
                          <strong>
                            {row.percent != null
                              ? `${row.percent}%`
                              : row.analysis && !row.analysis.isCurrent
                                ? 'Reassess'
                                : 'Not assessed'}
                          </strong>
                        </td>
                        {(['paper', 'scheme', 'report'] as const).map(
                          (role) => {
                            const source = row.estimate?.sourceChecks.find(
                              (source) => source.role === role,
                            );
                            return (
                              <td key={role}>
                                {row.analysis?.isCurrent &&
                                source?.percent != null
                                  ? `${source.percent}%`
                                  : '—'}
                                {source?.status === 'no_comment' && (
                                  <span className="small"> · no comment</span>
                                )}
                              </td>
                            );
                          },
                        )}
                        <td>
                          {row.analysis
                            ? new Date(
                                row.analysis.createdAt,
                              ).toLocaleDateString()
                            : '—'}
                        </td>
                        <td>{models.join(', ') || 'Not recorded'}</td>
                        <td aria-label="Question actions">
                          <div className="button-row">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() =>
                                setSelected({
                                  number: row.question.number,
                                  part: row.label,
                                })
                              }
                            >
                              Details
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() =>
                                openReview(row.question.number, row.label)
                              }
                            >
                              Review
                            </Button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </section>
            {/* oxlint-enable jsx-a11y/no-noninteractive-tabindex */}
            {rows.length === 0 && (
              <p>No questions or subparts match these filters.</p>
            )}
          </div>
        </DashboardCard>
      )}
      {chosen && (
        <div ref={details} className="stack">
          <h2>
            Question {chosen.number}
            {selected?.part !== undefined
              ? ` · part ${selected.part}`
              : ' · overall'}
          </h2>
          <QuestionAnalysisPanel
            key={`${chosen.number}-${selected?.part ?? 'overall'}`}
            paperId={paperId}
            number={chosen.number}
            accuracy={chosen.accuracyAnalysis}
            extraction={chosen.extractionAnalysis}
            partLabel={selected?.part}
            dirty={false}
            onSelectPart={(part) =>
              setSelected({ number: chosen.number, part })
            }
          />
          {!chosen.accuracyAnalysis && !chosen.extractionAnalysis && (
            <p>
              No source-comparison or provenance history has been recorded yet.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
