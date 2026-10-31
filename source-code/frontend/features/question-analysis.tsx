'use client';
import { useState } from 'react';
import {
  getQuestionAnalysisHistory,
  type QuestionAnalysis,
} from '@/api/assessments/official-paper-review.api';
import { Button } from '@/components/ui/button';
import { DashboardCard } from '@/components/portal/dashboard-widgets';
import { reviewProvenance } from '@/lib/paper-review-presentation';

const sourceName = (role: string) =>
  ({
    paper: 'Question paper',
    scheme: 'Marking scheme',
    report: 'Examiner report',
  })[role] || role;
const dateLabel = (value: string) => new Date(value).toLocaleString();

function AnalysisDetails({
  analysis,
  partLabel,
}: {
  analysis: QuestionAnalysis;
  partLabel?: string;
}) {
  const estimate =
    partLabel == null
      ? analysis.question
      : analysis.parts.find((part) => part.label === partLabel);
  const provenanceRecords = reviewProvenance(analysis, partLabel);
  return (
    <div className="stack">
      <p>
        {partLabel != null && <>Part {partLabel}: </>}
        <strong>
          {analysis.stage === 'accuracy'
            ? 'Accuracy confidence'
            : 'Extraction estimate'}
          : {estimate?.percent ?? 'Not assessed'}
          {estimate ? '%' : ''}
        </strong>
        {' · '}
        {dateLabel(analysis.createdAt)} · assessment v{analysis.version}
        {!analysis.isCurrent && ' · Earlier content — reassessment needed'}
      </p>
      <p className="small">
        This estimate helps prioritise source review. It does not change
        question or subpart approval.
      </p>
      <p className="small">Assessment method: {analysis.methodVersion}.</p>
      <ul>
        {estimate?.reasons.map((reason, index) => (
          <li key={index}>{reason}</li>
        ))}
      </ul>
      <details>
        <summary>Source checks and extraction provenance</summary>
        <div className="stack">
          {provenanceRecords.map((provenance) => {
            const check = estimate?.sourceChecks.find(
              (source) => source.role === provenance.role,
            );
            const source = analysis.sourceManifest.find(
              (source) => source.role === provenance.role,
            );
            return (
              <section className="panel stack" key={provenance.role}>
                <strong>{sourceName(provenance.role)}</strong>
                <p>
                  {check?.status.replaceAll('_', ' ')}
                  {check?.percent != null ? ` · ${check.percent}%` : ''}
                  {check?.pages.length
                    ? ` · PDF pages ${check.pages.join(', ')}`
                    : ''}
                </p>
                <ul>
                  {check?.reasons.map((reason, index) => (
                    <li key={index}>{reason}</li>
                  ))}
                </ul>
                <p>
                  {source?.filename || 'Source unavailable'}
                  {source?.version ? ` · source v${source.version}` : ''}
                </p>
                <p className="small">
                  PDF extraction:{' '}
                  {source?.pageExtractionMethods.join(', ') || 'Not recorded'}.
                </p>
                <p>
                  Interpretation: {provenance.method.replaceAll('_', ' ')}
                  {provenance.provider ? ` · ${provenance.provider}` : ''}.{' '}
                  Model:{' '}
                  {provenance.modelName ||
                    provenance.modelId ||
                    (['native_pdf', 'ocr', 'deterministic', 'manual'].includes(
                      provenance.method,
                    )
                      ? 'Not used'
                      : 'Not recorded')}
                  {provenance.modelId && provenance.modelName
                    ? ` (${provenance.modelId})`
                    : ''}
                  .
                </p>
                <p className="small">
                  {provenance.modelId &&
                    `Model ID source: ${(provenance.modelIdentitySource || 'operator_recorded').replaceAll('_', ' ')}. `}
                  {provenance.processedAt
                    ? `Analysed ${dateLabel(provenance.processedAt)}. `
                    : ''}
                  Guidelines: {provenance.guidelineId || 'Not recorded'}{' '}
                  {provenance.guidelineVersion || ''}. Prompt:{' '}
                  {provenance.promptVersion || 'Not recorded'}.
                </p>
                {provenance.notes && (
                  <p className="small">{provenance.notes}</p>
                )}
              </section>
            );
          })}
        </div>
      </details>
    </div>
  );
}

export function QuestionAnalysisPanel({
  paperId,
  number,
  accuracy,
  extraction,
  partLabel,
  dirty,
  onSelectPart,
}: {
  paperId: string;
  number: string;
  accuracy?: QuestionAnalysis | null;
  extraction?: QuestionAnalysis | null;
  partLabel?: string;
  dirty: boolean;
  onSelectPart: (label: string) => void;
}) {
  const [history, setHistory] = useState<QuestionAnalysis[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  if (!accuracy && !extraction) return null;
  return (
    <DashboardCard
      title="Accuracy confidence & provenance"
      description="Dated source comparisons and the methods or models used."
    >
      <div className="stack">
        {dirty && (
          <p className="small">
            These confidence estimates apply to the saved question. Save changes
            before reassessment.
          </p>
        )}
        <AnalysisDetails
          analysis={accuracy || extraction!}
          partLabel={partLabel}
        />
        {accuracy?.isCurrent && (
          <details>
            <summary>Subparts by lowest confidence</summary>
            <div className="button-row">
              {[...accuracy.parts]
                .sort((a, b) => a.percent - b.percent)
                .map((part) => (
                  <Button
                    key={part.label}
                    variant="outline"
                    aria-pressed={part.label === partLabel}
                    onClick={() => onSelectPart(part.label)}
                  >
                    Part {part.label} · {part.percent}%
                  </Button>
                ))}
            </div>
          </details>
        )}
        {accuracy && !extraction && (
          <p className="small">
            Original extraction model: not recorded. The model details above
            describe this accuracy assessment.
          </p>
        )}
        <Button
          variant="outline"
          disabled={busy}
          onClick={async () => {
            if (history) {
              setHistory(null);
              return;
            }
            setBusy(true);
            setError('');
            try {
              setHistory(await getQuestionAnalysisHistory(paperId, number));
            } catch (cause) {
              setError(
                cause instanceof Error
                  ? cause.message
                  : 'Unable to load analysis history.',
              );
            } finally {
              setBusy(false);
            }
          }}
        >
          {history
            ? 'Hide analysis history'
            : busy
              ? 'Loading history…'
              : 'View analysis history'}
        </Button>
        {error && <p role="alert">{error}</p>}
        {history?.map((analysis) => (
          <details key={analysis.id}>
            <summary>
              {analysis.stage === 'accuracy'
                ? 'Accuracy assessment'
                : 'Extraction analysis'}{' '}
              v{analysis.version} · {dateLabel(analysis.createdAt)}
            </summary>
            <AnalysisDetails analysis={analysis} partLabel={partLabel} />
          </details>
        ))}
      </div>
    </DashboardCard>
  );
}
