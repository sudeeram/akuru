'use client';
/* Form labels wrap design-system inputs; the accessibility rule does not resolve their rendered controls. */
/* eslint-disable jsx-a11y/label-has-associated-control */
import { useEffect, useState, type PointerEvent } from 'react';
import Image from 'next/image';
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  ClipboardList,
  FileText,
  Maximize2,
  Minimize2,
  Save,
  TriangleAlert,
} from 'lucide-react';
import {
  DashboardCard,
  MetricCard,
  PageHeader,
} from '@/components/portal/dashboard-widgets';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import {
  reviewQuestionList,
  reviewNeighbours,
  reviewAttentionCount,
  reviewNavigationAllowed,
  reviewHasChanges,
} from '@/lib/paper-review-presentation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  getDocumentExtraction,
  getPaperReview,
  getReviewTopics,
  savePaperReviewQuestion,
  seedPaperReview,
  startPaperReview,
  prepareOfficialReviewDrafts,
  createPaperReviewCrop,
  getPaperReviewCrops,
  generatePaperReviewVisuals,
  errorMessage,
  type Doc,
  type DocumentExtraction,
  type PaperReview,
  type ReviewQuestionData,
  type ReviewPart,
  type ReviewStatus,
  type CoverageStatus,
  type ReviewEvidence,
} from '@/api';

const reviewStatuses: ReviewStatus[] = [
  'unreviewed',
  'needs_correction',
  'ready_for_approval',
  'approved',
  'excluded',
];
const coverageStatuses: CoverageStatus[] = [
  'unreviewed',
  'supported',
  'partial_or_uncertain',
  'outside_current_coverage',
];
const label = (value: string) => value.replaceAll('_', ' ');

function emptyPart(): ReviewPart {
  return {
    label: 'a',
    marks: 1,
    prompt: '',
    visualAssetIds: [],
    markingPoints: [],
    alternatives: [],
    examinerAdvice: '',
    paperSources: [],
    schemeSources: [],
    reportSources: [],
    coverage: 'unreviewed',
    topicRefs: [],
    coverageReason: '',
    status: 'unreviewed',
  };
}
function emptyQuestion(): ReviewQuestionData {
  return {
    marks: 1,
    sharedStem: '',
    prompt: '',
    paperSources: [],
    visualAssetIds: [],
    candidateVisualAssetIds: [],
    visualAltText: '',
    parts: [emptyPart()],
    exclusionReason: '',
  };
}

function SourcePage({
  documentId,
  extraction,
  title,
  selectedPage,
  onPage,
  onToggle,
  linked,
  partLabel,
  sourceKind,
  onCropBox,
}: {
  documentId?: string | null;
  extraction?: DocumentExtraction | null;
  title: string;
  selectedPage: number;
  onPage: (value: number) => void;
  onToggle?: (blockId?: string) => void;
  linked: ReviewEvidence[];
  partLabel: string;
  sourceKind: 'paper' | 'scheme' | 'report';
  onCropBox?: (box: { x0: number; y0: number; x1: number; y1: number }) => void;
}) {
  const page = extraction?.pages.find(
    (item) => item.pageNumber === selectedPage,
  );
  const hasLink = (blockId?: string) =>
    linked.some(
      (source) =>
        source.page === selectedPage &&
        (source.blockId || null) === (blockId || null),
    );
  return (
    <section className="pr-source-page" aria-label={`${title} evidence`}>
      <div className="pr-source-heading">
        <h3>{title}</h3>
        <span className="small">Part {partLabel}</span>
      </div>
      <div className="stack pr-source-body">
        {!documentId ? (
          <p>No source attached.</p>
        ) : !extraction ? (
          <p>Loading reviewed source pages…</p>
        ) : (
          <>
            <div className="button-row pr-page-controls">
              <Button
                variant="outline"
                size="sm"
                aria-label={`Previous ${title} page`}
                disabled={selectedPage <= 1}
                onClick={() => onPage(selectedPage - 1)}
              >
                <ArrowLeft size={14} />
              </Button>
              <label>
                PDF page{' '}
                <Input
                  type="number"
                  min={1}
                  max={extraction.pages.length}
                  value={selectedPage}
                  onChange={(event) => onPage(Number(event.target.value))}
                  style={{ width: 85 }}
                />
              </label>
              <span>of {extraction.pages.length}</span>
              <Button
                variant="outline"
                size="sm"
                aria-label={`Next ${title} page`}
                disabled={selectedPage >= extraction.pages.length}
                onClick={() => onPage(selectedPage + 1)}
              >
                <ArrowRight size={14} />
              </Button>
              {onToggle && (
                <Button
                  variant="outline"
                  disabled={!page}
                  aria-pressed={hasLink()}
                  onClick={() => onToggle()}
                >
                  {hasLink()
                    ? `Remove page link from part ${partLabel}`
                    : 'Link this page'}
                </Button>
              )}
            </div>
            {page ? (
              <>
                <span className="small">
                  {page.printedPageLabel
                    ? `Book page ${page.printedPageLabel}`
                    : `PDF page ${page.pageNumber}`}
                </span>
                <Image
                  src={`/api/v1/documents/${documentId}/assets/${page.originalRenderAssetId || page.renderAssetId}/content`}
                  alt={`${title}, page ${page.pageNumber}`}
                  width={800}
                  height={1100}
                  unoptimized
                  style={{
                    width: '100%',
                    height: 'auto',
                    maxHeight: 520,
                    objectFit: 'contain',
                    objectPosition: 'top',
                    borderRadius: 8,
                  }}
                />
                <details>
                  <summary>Extracted blocks · link exact evidence</summary>
                  {page.blocks.map((block) => (
                    <div
                      key={block.id}
                      id={`review-${sourceKind}-${block.id}`}
                      className="pr-evidence-block stack"
                      tabIndex={-1}
                    >
                      <p className="small">
                        {block.text.slice(0, 600) || block.kind}
                      </p>
                      {onToggle && (
                        <Button
                          variant="outline"
                          aria-pressed={hasLink(block.id)}
                          onClick={() => onToggle(block.id)}
                        >
                          {hasLink(block.id)
                            ? `Linked to part ${partLabel} · Remove link`
                            : 'Link this block'}
                        </Button>
                      )}
                      {sourceKind === 'paper' &&
                        onCropBox &&
                        ['diagram', 'image', 'table'].includes(block.kind) && (
                          <Button
                            variant="outline"
                            onClick={() =>
                              onCropBox({
                                x0: block.boundingBox.x0 / page.widthPoints,
                                y0: block.boundingBox.y0 / page.heightPoints,
                                x1: block.boundingBox.x1 / page.widthPoints,
                                y1: block.boundingBox.y1 / page.heightPoints,
                              })
                            }
                          >
                            Use region as crop starting point
                          </Button>
                        )}
                    </div>
                  ))}
                </details>
              </>
            ) : (
              <p>Choose a valid page.</p>
            )}
          </>
        )}
      </div>
    </section>
  );
}

type CropBox = { x0: number; y0: number; x1: number; y1: number };
function VisualCropEditor({
  paperId,
  extraction,
  pageNumber,
  initialBox,
  initialKind,
  onCreated,
}: {
  paperId: string;
  extraction: DocumentExtraction | null;
  pageNumber: number;
  initialBox: CropBox | null;
  initialKind: 'diagram' | 'table';
  onCreated: (
    assetId: string,
    altText: string,
    kind: 'diagram' | 'table',
    bounds: CropBox,
  ) => void;
}) {
  const page = extraction?.pages.find((item) => item.pageNumber === pageNumber);
  const [box, setBox] = useState<CropBox>(
    initialBox || { x0: 0.2, y0: 0.2, x1: 0.8, y1: 0.6 },
  );
  const [kind, setKind] = useState<'diagram' | 'table'>(initialKind);
  const [altText, setAltText] = useState('');
  const [dragStart, setDragStart] = useState<{ x: number; y: number } | null>(
    null,
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const clamp = (value: number) => Math.max(0, Math.min(1, value));
  const point = (event: PointerEvent<HTMLDivElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    return {
      x: clamp((event.clientX - rect.left) / rect.width),
      y: clamp((event.clientY - rect.top) / rect.height),
    };
  };
  const change = (field: keyof CropBox, value: string) =>
    setBox((current) => ({ ...current, [field]: clamp(Number(value) / 100) }));
  const valid =
    box.x1 > box.x0 + 0.02 &&
    box.y1 > box.y0 + 0.02 &&
    (box.x1 - box.x0) * (box.y1 - box.y0) <= 0.65 &&
    altText.trim().length >= 10;
  if (!page)
    return <p>Choose a question-paper page before selecting a visual.</p>;
  return (
    <section className="panel stack" aria-label="Select question visual">
      <h3>Crop a diagram or table from PDF page {pageNumber}</h3>
      <p className="small">
        Drag across the page or adjust the percentages below. Keep only the
        visual and any labels needed to answer.
      </p>
      <div
        style={{
          position: 'relative',
          width: '100%',
          maxWidth: 650,
          touchAction: 'none',
          cursor: 'crosshair',
        }}
        onPointerDown={(event) => {
          const p = point(event);
          setDragStart(p);
          setBox({ x0: p.x, y0: p.y, x1: p.x, y1: p.y });
          event.currentTarget.setPointerCapture(event.pointerId);
        }}
        onPointerMove={(event) => {
          if (!dragStart) return;
          const p = point(event);
          setBox({
            x0: Math.min(dragStart.x, p.x),
            y0: Math.min(dragStart.y, p.y),
            x1: Math.max(dragStart.x, p.x),
            y1: Math.max(dragStart.y, p.y),
          });
        }}
        onPointerUp={() => setDragStart(null)}
        onPointerCancel={() => setDragStart(null)}
      >
        <Image
          src={`/api/v1/documents/${paperId}/assets/${page.originalRenderAssetId || page.renderAssetId}/content`}
          alt={`Question paper PDF page ${pageNumber} for visual selection`}
          width={Math.round(page.widthPoints)}
          height={Math.round(page.heightPoints)}
          unoptimized
          style={{ display: 'block', width: '100%', height: 'auto' }}
        />
        <div
          aria-hidden="true"
          style={{
            position: 'absolute',
            left: `${box.x0 * 100}%`,
            top: `${box.y0 * 100}%`,
            width: `${Math.max(0, box.x1 - box.x0) * 100}%`,
            height: `${Math.max(0, box.y1 - box.y0) * 100}%`,
            border: '3px solid #0f766e',
            background: 'rgba(15,118,110,.15)',
            pointerEvents: 'none',
          }}
        />
      </div>
      <div className="button-row">
        <label>
          Visual type{' '}
          <select
            value={kind}
            onChange={(event) =>
              setKind(event.target.value as 'diagram' | 'table')
            }
          >
            <option value="diagram">Diagram or figure</option>
            <option value="table">Table</option>
          </select>
        </label>
        {(['x0', 'y0', 'x1', 'y1'] as const).map((field) => (
          <label key={field}>
            {field} %{' '}
            <Input
              type="number"
              min={0}
              max={100}
              step={0.1}
              value={Math.round(box[field] * 1000) / 10}
              onChange={(event) => change(field, event.target.value)}
              style={{ width: 90 }}
            />
          </label>
        ))}
      </div>
      <label>
        Accessible description of this visual{' '}
        <Textarea
          value={altText}
          onChange={(event) => setAltText(event.target.value)}
          placeholder="Describe the diagram labels or table structure needed to answer."
        />
      </label>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      <Button
        disabled={!valid || busy}
        onClick={() => {
          setBusy(true);
          setError('');
          void createPaperReviewCrop(paperId, {
            page: pageNumber,
            kind,
            ...box,
            altText: altText.trim(),
          })
            .then((result) => {
              onCreated(
                result.assetId,
                result.altText,
                result.kind,
                result.bounds,
              );
              setAltText('');
            })
            .catch((cause) => setError(errorMessage(cause)))
            .finally(() => setBusy(false));
        }}
      >
        Create and attach visual to this question
      </Button>
    </section>
  );
}

export function OfficialPaperReview({
  paperId,
  documents,
  navigate,
}: {
  paperId: string;
  documents: Doc[];
  navigate: (path: string) => void;
}) {
  const paper = documents.find((document) => document.id === paperId);
  const companions = documents.filter(
    (document) => document.paperId === paperId || document.id === paperId,
  );
  const [review, setReview] = useState<PaperReview | null>(null);
  const [loadingReview, setLoadingReview] = useState(true);
  const [schemeId, setSchemeId] = useState('');
  const [reportId, setReportId] = useState('');
  const [expectedCount, setExpectedCount] = useState('');
  const [draftFile, setDraftFile] = useState<File | null>(null);
  const [triageFile, setTriageFile] = useState<File | null>(null);
  const [topics, setTopics] = useState<
    { topicRef: string; code: string; title: string }[]
  >([]);
  const [selected, setSelected] = useState('');
  const [number, setNumber] = useState('');
  const [data, setData] = useState<ReviewQuestionData>(emptyQuestion());
  const [status, setStatus] = useState<ReviewStatus>('unreviewed');
  const [revision, setRevision] = useState(0);
  const [activePart, setActivePart] = useState(0);
  const [paperExtraction, setPaperExtraction] =
    useState<DocumentExtraction | null>(null);
  const [schemeExtraction, setSchemeExtraction] =
    useState<DocumentExtraction | null>(null);
  const [reportExtraction, setReportExtraction] =
    useState<DocumentExtraction | null>(null);
  const [paperPage, setPaperPage] = useState(1);
  const [schemePage, setSchemePage] = useState(1);
  const [reportPage, setReportPage] = useState(1);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [savedSnapshot, setSavedSnapshot] = useState('');
  const [cropBox, setCropBox] = useState<CropBox | null>(null);
  const [cropKind, setCropKind] = useState<'diagram' | 'table'>('diagram');
  const [replaceCandidateId, setReplaceCandidateId] = useState<string | null>(
    null,
  );
  const [availableCrops, setAvailableCrops] = useState<
    {
      assetId: string;
      page: number;
      kind: 'diagram' | 'table';
      altText: string;
      approved: boolean;
      bounds: CropBox;
    }[]
  >([]);
  const [questionFilter, setQuestionFilter] = useState('all');
  const [questionSearch, setQuestionSearch] = useState('');
  const [sourceTab, setSourceTab] = useState('paper');
  const [compareSources, setCompareSources] = useState(false);
  const [cropOpen, setCropOpen] = useState(false);
  const [linkedTarget, setLinkedTarget] = useState<string | null>(null);
  const [candidateDescriptions, setCandidateDescriptions] = useState<
    Record<string, string>
  >({});

  function chooseQuestion(row: PaperReview['questions'][number]) {
    const loaded = structuredClone(row.data);
    loaded.candidateVisualAssetIds ||= [];
    loaded.parts = loaded.parts.map((item) => ({
      ...item,
      visualAssetIds: item.visualAssetIds || [],
    }));
    setSelected(row.number);
    setNumber(row.number);
    setData(loaded);
    setStatus(row.status);
    setRevision(row.revision);
    setActivePart(0);
    setCropBox(null);
    setReplaceCandidateId(null);
    setCropOpen(false);
    setSavedSnapshot(
      JSON.stringify({ number: row.number, status: row.status, data: loaded }),
    );
    setPaperPage(row.data.paperSources[0]?.page || 1);
    setSchemePage(row.data.parts[0]?.schemeSources[0]?.page || 1);
    setReportPage(row.data.parts[0]?.reportSources[0]?.page || 1);
  }

  useEffect(() => {
    let active = true;
    void getPaperReview(paperId)
      .then((value) => {
        if (active) {
          setReview(value);
          if (value.questions[0]) chooseQuestion(value.questions[0]);
        }
      })
      .catch((cause) => {
        if (
          active &&
          !(
            cause &&
            typeof cause === 'object' &&
            'status' in cause &&
            cause.status === 404
          )
        )
          setError(errorMessage(cause));
      })
      .finally(() => {
        if (active) setLoadingReview(false);
      });
    void getReviewTopics(paperId)
      .then((value) => {
        if (active) setTopics(value);
      })
      .catch(() => {});
    void getDocumentExtraction(paperId)
      .then((value) => {
        if (active) setPaperExtraction(value);
      })
      .catch(() => {});
    void getPaperReviewCrops(paperId)
      .then((value) => {
        if (active) setAvailableCrops(value);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [paperId]);
  useEffect(() => {
    if (!review?.schemeDocumentId) return;
    let active = true;
    void getDocumentExtraction(review.schemeDocumentId)
      .then((value) => {
        if (active) setSchemeExtraction(value);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [review?.schemeDocumentId]);
  useEffect(() => {
    if (!review?.reportDocumentId) return;
    let active = true;
    void getDocumentExtraction(review.reportDocumentId)
      .then((value) => {
        if (active) setReportExtraction(value);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [review?.reportDocumentId]);
  async function act(action: () => Promise<PaperReview>, message: string) {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      const value = await action();
      setReview(value);
      if (number) {
        const row = value.questions.find(
          (question) => question.number === number,
        );
        if (row) chooseQuestion(row);
      }
      setNotice(message);
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  }
  function updatePart(next: ReviewPart) {
    setData((current) => ({
      ...current,
      parts: current.parts.map((part, index) =>
        index === activePart ? next : part,
      ),
    }));
  }
  const part = data.parts[activePart];
  const dirty = reviewHasChanges({ number, status, data }, savedSnapshot, {
    number: '',
    status: 'unreviewed',
    data: emptyQuestion(),
  });
  useEffect(() => {
    if (!linkedTarget) return;
    const frame = window.requestAnimationFrame(() => {
      const target = document.getElementById(linkedTarget);
      const disclosure = target?.closest('details');
      if (disclosure) disclosure.open = true;
      target?.scrollIntoView({ block: 'nearest' });
      target?.focus({ preventScroll: true });
      setLinkedTarget(null);
    });
    return () => window.cancelAnimationFrame(frame);
  }, [linkedTarget, sourceTab, compareSources]);
  useEffect(() => {
    if (!dirty && !busy) return;
    const beforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
    };
    const beforeNavigation = (event: Event) => {
      if (
        !reviewNavigationAllowed(busy, dirty, () =>
          window.confirm('Discard unsaved question review changes?'),
        )
      )
        event.preventDefault();
    };
    window.addEventListener('beforeunload', beforeUnload);
    window.addEventListener('akuru:before-navigation', beforeNavigation);
    return () => {
      window.removeEventListener('beforeunload', beforeUnload);
      window.removeEventListener('akuru:before-navigation', beforeNavigation);
    };
  }, [dirty, busy]);
  const canLeaveQuestion = () =>
    reviewNavigationAllowed(busy, dirty, () =>
      window.confirm('Discard unsaved question review changes?'),
    );
  const openQuestion = (row: PaperReview['questions'][number]) => {
    if (canLeaveQuestion()) chooseQuestion(row);
  };
  const addQuestion = () => {
    if (!canLeaveQuestion()) return;
    setSelected('');
    setNumber('');
    setRevision(0);
    setStatus('unreviewed');
    setData(emptyQuestion());
    setSavedSnapshot('');
    setCropOpen(false);
  };
  const neighbours = reviewNeighbours(review?.questions ?? [], selected);
  const saveQuestion = () =>
    void act(
      () =>
        savePaperReviewQuestion(paperId, {
          number,
          expectedRevision: revision,
          status,
          data,
        }),
      'Question review saved.',
    );
  const pageAsset = (
    extraction: DocumentExtraction | null,
    pageNumber: number,
  ) =>
    extraction?.pages.find((row) => row.pageNumber === pageNumber)
      ?.renderAssetId;
  function toggleLink(kind: 'paper' | 'scheme' | 'report', blockId?: string) {
    const [extraction, pageNumber, field] =
      kind === 'paper'
        ? ([paperExtraction, paperPage, 'paperSources'] as const)
        : kind === 'scheme'
          ? ([schemeExtraction, schemePage, 'schemeSources'] as const)
          : ([reportExtraction, reportPage, 'reportSources'] as const);
    const assetId = pageAsset(extraction, pageNumber);
    if (!assetId || !part) return;
    const entry = { page: pageNumber, assetId, blockId: blockId || null };
    setData((current) => {
      const chosen = current.parts[activePart];
      const isLinked = chosen[field].some(
        (source) =>
          source.page === pageNumber &&
          (source.blockId || null) === (blockId || null),
      );
      const sources = isLinked
        ? chosen[field].filter(
            (source) =>
              !(
                source.page === pageNumber &&
                (source.blockId || null) === (blockId || null)
              ),
          )
        : [...chosen[field], entry];
      const parts = current.parts.map((row, index) =>
        index === activePart ? { ...row, [field]: sources } : row,
      );
      const paperSources =
        kind === 'paper'
          ? Array.from(
              new Map(
                parts
                  .flatMap((row) => row.paperSources)
                  .map((source) => [
                    `${source.page}:${source.blockId || ''}`,
                    source,
                  ]),
              ).values(),
            )
          : current.paperSources;
      return { ...current, parts, paperSources };
    });
  }
  const sourceList = (sources: { page: number }[]) =>
    sources.map((source) => source.page).join(', ') || 'None';
  function showLinked(
    kind: 'paper' | 'scheme' | 'report',
    source: ReviewEvidence,
  ) {
    setSourceTab(kind);
    setCompareSources(false);
    (kind === 'paper'
      ? setPaperPage
      : kind === 'scheme'
        ? setSchemePage
        : setReportPage)(source.page);
    setLinkedTarget(
      source.blockId
        ? `review-${kind}-${source.blockId}`
        : `review-source-${kind}`,
    );
  }
  async function keepCandidate(crop: (typeof availableCrops)[number]) {
    const altText = (candidateDescriptions[crop.assetId] ?? crop.altText ?? '').trim();
    if (altText.length < 10) {
      setError(
        'Describe this visual in at least 10 characters before approving its crop.',
      );
      return;
    }
    setBusy(true);
    setError('');
    setNotice('');
    try {
      const result = await createPaperReviewCrop(paperId, {
        page: crop.page,
        kind: crop.kind,
        ...crop.bounds,
        altText,
      });
      setAvailableCrops((current) => [...current, result]);
      setData((current) => ({
        ...current,
        visualAssetIds: current.visualAssetIds.map((id) =>
          id === crop.assetId ? result.assetId : id,
        ),
        candidateVisualAssetIds: current.candidateVisualAssetIds.map((id) =>
          id === crop.assetId ? result.assetId : id,
        ),
        parts: current.parts.map((item) => ({
          ...item,
          visualAssetIds: item.visualAssetIds.map((id) =>
            id === crop.assetId ? result.assetId : id,
          ),
        })),
        visualAltText: current.visualAltText || altText,
      }));
      setNotice(
        'Candidate crop reviewed and attached. Save question review to keep this selection.',
      );
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  }
  const assignedIds = [
    ...new Set([
      ...data.visualAssetIds,
      ...data.parts.flatMap((item) => item.visualAssetIds),
    ]),
  ];
  const allVisualIds = [
    ...new Set([...assignedIds, ...data.candidateVisualAssetIds]),
  ];
  function setVisualLocation(
    assetId: string,
    target: 'shared' | 'unassigned' | number,
    selected: boolean,
  ) {
    setData((current) => {
      const shared = current.visualAssetIds.filter((id) => id !== assetId);
      const unassigned = current.candidateVisualAssetIds.filter(
        (id) => id !== assetId,
      );
      const parts = current.parts.map((item, index) => ({
        ...item,
        visualAssetIds:
          index === target
            ? selected
              ? [...new Set([...item.visualAssetIds, assetId])]
              : item.visualAssetIds.filter((id) => id !== assetId)
            : item.visualAssetIds,
      }));
      if (target === 'shared' && selected) shared.push(assetId);
      if (target === 'unassigned' && selected) unassigned.push(assetId);
      const assigned =
        shared.includes(assetId) ||
        parts.some((item) => item.visualAssetIds.includes(assetId));
      return {
        ...current,
        visualAssetIds: shared,
        candidateVisualAssetIds: assigned
          ? unassigned
          : unassigned.includes(assetId)
            ? unassigned
            : [...unassigned, assetId],
        parts,
      };
    });
  }

  if (loadingReview)
    return (
      <output className="panel" aria-live="polite">
        Opening the paper review workspace…
      </output>
    );
  if (!paper)
    return (
      <section className="panel">
        <p>Past paper not found.</p>
        <Button onClick={() => navigate('/admin/exam-documents/past-papers')}>
          Back to papers
        </Button>
      </section>
    );
  return (
    <div className="pr-review stack">
      <PageHeader
        eyebrow="EXAM DOCUMENTS · OFFICIAL PAPER REVIEW"
        title={paper.name}
        description="Admin-only draft. Saving or approving a question does not release it to Students."
        action={
          <Button
            variant="outline"
            disabled={busy}
            onClick={() => {
              if (!busy) navigate('/admin/exam-documents/past-papers');
            }}
          >
            <ArrowLeft size={15} /> Back to papers
          </Button>
        }
      />
      {error && (
        <p className="error pr-feedback" role="alert">
          {error}
        </p>
      )}
      {notice && (
        <output className="pr-feedback" aria-live="polite">
          {notice}
        </output>
      )}
      {review && (
        <>
          <div className="ak-metrics pr-metrics">
            <MetricCard
              label="Expected questions"
              value={review.expectedQuestionCount || 'Not set'}
              detail="Complete paper inventory"
              icon={ClipboardList}
            />
            <MetricCard
              label="Saved questions"
              value={review.questionCount}
              detail="Questions in this workspace"
              icon={FileText}
              tone="violet"
            />
            <MetricCard
              label="Approved"
              value={review.approvedCount}
              detail={
                review.wholePaperReady
                  ? 'Internal review complete'
                  : 'Internal review in progress'
              }
              icon={CheckCircle2}
              tone="green"
            />
            <MetricCard
              label="Needs attention"
              value={reviewAttentionCount(review.questions)}
              detail="Saved questions requiring review"
              icon={TriangleAlert}
              tone="amber"
            />
          </div>
          {!!review.blockers.length && (
            <details className="pr-blockers">
              <summary>
                <TriangleAlert size={16} /> {review.blockers.length} review
                blocker{review.blockers.length === 1 ? '' : 's'} · View what
                remains
              </summary>
              <ul>
                {review.blockers.map((blocker) => (
                  <li key={blocker}>{blocker}</li>
                ))}
              </ul>
            </details>
          )}
        </>
      )}
      {review?.wholePaperReady && (
        <Button
          variant="outline"
          disabled={busy || dirty}
          onClick={() => {
            setBusy(true);
            setError('');
            void prepareOfficialReviewDrafts(paperId)
              .then(() =>
                setNotice(
                  'Official paper and exact-scheme drafts prepared. Review and publish each source separately from Exam Documents. Student access remains closed until the published pairing passes.',
                ),
              )
              .catch((cause) => setError(errorMessage(cause)))
              .finally(() => setBusy(false));
          }}
        >
          Prepare official paper and scheme drafts
        </Button>
      )}
      <details className="pr-paper-details" open={!review}>
        <summary>Paper details & source attachments</summary>
        <div className="stack pr-details-body">
          <p>
            <strong>Subject:</strong> {paper.subject} ·{' '}
            <strong>Question paper:</strong> {paper.name}
          </p>
          {review?.schemeDocumentId && (
            <p>
              <strong>Marking scheme:</strong>{' '}
              {documents.find((doc) => doc.id === review.schemeDocumentId)
                ?.name || 'Attached exact source'}
            </p>
          )}
          {review?.reportDocumentId && (
            <p>
              <strong>Examiner report:</strong>{' '}
              {documents.find((doc) => doc.id === review.reportDocumentId)
                ?.name || 'Attached source'}
            </p>
          )}
          {!review ? (
            <div className="stack">
              <label>
                Exact marking scheme{' '}
                <select
                  value={schemeId}
                  onChange={(event) => setSchemeId(event.target.value)}
                >
                  <option value="">Attach later</option>
                  {companions
                    .filter((doc) => doc.kind === 'Marking scheme')
                    .map((doc) => (
                      <option key={doc.id} value={doc.id}>
                        {doc.name}
                      </option>
                    ))}
                </select>
              </label>
              <label>
                Examiner report{' '}
                <select
                  value={reportId}
                  onChange={(event) => setReportId(event.target.value)}
                >
                  <option value="">Absent or attach later</option>
                  {companions
                    .filter((doc) => doc.kind === 'Examiner report')
                    .map((doc) => (
                      <option key={doc.id} value={doc.id}>
                        {doc.name}
                      </option>
                    ))}
                </select>
              </label>
              <label>
                Expected complete question count{' '}
                <Input
                  type="number"
                  min={0}
                  max={200}
                  value={expectedCount}
                  onChange={(event) => setExpectedCount(event.target.value)}
                />
              </label>
              <Button
                disabled={busy || !paperExtraction}
                onClick={() =>
                  void act(
                    () =>
                      startPaperReview(paperId, {
                        schemeDocumentId: schemeId || null,
                        reportDocumentId: reportId || null,
                        expectedQuestionCount: Number(expectedCount) || 0,
                      }),
                    'Review workspace created.',
                  )
                }
              >
                Start Admin review
              </Button>
            </div>
          ) : (
            <>
              {(!review.schemeDocumentId || !review.reportDocumentId) && (
                <div className="button-row">
                  {!review.schemeDocumentId && (
                    <label>
                      Attach scheme{' '}
                      <select
                        value={schemeId}
                        onChange={(event) => setSchemeId(event.target.value)}
                      >
                        <option value="">Choose</option>
                        {companions
                          .filter((doc) => doc.kind === 'Marking scheme')
                          .map((doc) => (
                            <option key={doc.id} value={doc.id}>
                              {doc.name}
                            </option>
                          ))}
                      </select>
                    </label>
                  )}
                  {!review.reportDocumentId && (
                    <label>
                      Attach report{' '}
                      <select
                        value={reportId}
                        onChange={(event) => setReportId(event.target.value)}
                      >
                        <option value="">Optional</option>
                        {companions
                          .filter((doc) => doc.kind === 'Examiner report')
                          .map((doc) => (
                            <option key={doc.id} value={doc.id}>
                              {doc.name}
                            </option>
                          ))}
                      </select>
                    </label>
                  )}
                  <Button
                    variant="outline"
                    disabled={busy || (!schemeId && !reportId)}
                    onClick={() =>
                      void act(
                        () =>
                          startPaperReview(paperId, {
                            schemeDocumentId: schemeId || null,
                            reportDocumentId: reportId || null,
                          }),
                        'Source attached.',
                      )
                    }
                  >
                    Attach selected source
                  </Button>
                </div>
              )}
            </>
          )}
        </div>
      </details>
      {review && (
        <>
          {review.questionCount === 0 && (
            <section className="panel stack">
              <h3>Import draft proposals</h3>
              <p>
                Use the private unreleased bank only after uploading the exact
                source PDFs. Every imported item remains unapproved.
              </p>
              <label>
                Draft bank JSON{' '}
                <Input
                  type="file"
                  accept="application/json,.json"
                  onChange={(event) =>
                    setDraftFile(event.target.files?.[0] || null)
                  }
                />
              </label>
              <label>
                Optional coverage triage JSON{' '}
                <Input
                  type="file"
                  accept="application/json,.json"
                  onChange={(event) =>
                    setTriageFile(event.target.files?.[0] || null)
                  }
                />
              </label>
              <Button
                disabled={!draftFile || busy}
                onClick={() =>
                  void act(async () => {
                    await seedPaperReview(
                      paperId,
                      JSON.parse(await draftFile!.text()) as object,
                      triageFile
                        ? (JSON.parse(await triageFile.text()) as object)
                        : undefined,
                    );
                    await generatePaperReviewVisuals(paperId);
                    setAvailableCrops(await getPaperReviewCrops(paperId));
                    return getPaperReview(paperId);
                  }, 'Unapproved source proposals and candidate visuals imported.')
                }
              >
                Import proposals for review
              </Button>
            </section>
          )}
          {review.questionCount > 0 && (
            <details className="pr-tools">
              <summary>Candidate visual tools</summary>
              <div className="stack pr-details-body">
                <strong>Candidate question visuals</strong>
                <p className="small">
                  AKURU crops diagrams and tables from the paper first. Review
                  each attached candidate, adjust its crop if needed, and add a
                  useful description before approving the question.
                </p>
                <Button
                  variant="outline"
                  disabled={busy || dirty}
                  onClick={() => {
                    setBusy(true);
                    setError('');
                    void generatePaperReviewVisuals(paperId)
                      .then(async (result) => {
                        const updated = await getPaperReview(paperId);
                        setReview(updated);
                        setAvailableCrops(await getPaperReviewCrops(paperId));
                        const row = updated.questions.find(
                          (question) => question.number === number,
                        );
                        if (row) chooseQuestion(row);
                        setNotice(
                          `${result.created} candidate visual(s) prepared; ${result.attached} question link(s) added.`,
                        );
                      })
                      .catch((cause) => setError(errorMessage(cause)))
                      .finally(() => setBusy(false));
                  }}
                >
                  Prepare or refresh candidate visuals
                </Button>
              </div>
            </details>
          )}
          <div className="pr-actionbar" aria-label="Question review actions">
            <div>
              <strong>
                {number ? `Question ${number}` : 'Select or add a question'}
              </strong>
              <output aria-live="polite">
                {busy
                  ? 'Working…'
                  : dirty
                    ? 'Unsaved review changes.'
                    : revision
                      ? 'Saved review state.'
                      : 'New draft.'}
              </output>
            </div>
            <div className="button-row">
              <Button
                variant="outline"
                size="sm"
                disabled={busy || !neighbours.previous}
                onClick={() =>
                  neighbours.previous && openQuestion(neighbours.previous)
                }
              >
                <ArrowLeft size={14} /> Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={busy || !neighbours.next}
                onClick={() => neighbours.next && openQuestion(neighbours.next)}
              >
                Next <ArrowRight size={14} />
              </Button>
              <Button disabled={busy || !number.trim()} onClick={saveQuestion}>
                <Save size={15} /> Save question review
              </Button>
            </div>
          </div>
          <div className="pr-workspace" data-comparison={compareSources}>
            <aside className="pr-question-nav">
              <DashboardCard
                title="Questions"
                description={`${review.questions.length} saved in this paper`}
              >
                <div className="stack">
                  <Input
                    aria-label="Find question"
                    placeholder="Find question…"
                    value={questionSearch}
                    onChange={(event) => setQuestionSearch(event.target.value)}
                  />
                  <label>
                    Review status
                    <select
                      value={questionFilter}
                      onChange={(event) =>
                        setQuestionFilter(event.target.value)
                      }
                    >
                      <option value="all">All questions</option>
                      <option value="attention">Needs attention</option>
                      {reviewStatuses.map((item) => (
                        <option key={item} value={item}>
                          {label(item)}
                        </option>
                      ))}
                    </select>
                  </label>
                  <nav
                    aria-label="Question review navigation"
                    className="pr-question-list"
                  >
                    {reviewQuestionList(
                      review.questions,
                      questionFilter,
                      questionSearch,
                    ).map((question) => (
                      <button
                        key={question.number}
                        type="button"
                        disabled={busy}
                        aria-current={
                          selected === question.number ? 'step' : undefined
                        }
                        onClick={() => openQuestion(question)}
                      >
                        <span
                          className={`pr-state-dot pr-state-${question.status}`}
                          aria-hidden="true"
                        />
                        <span>
                          <strong>Question {question.number}</strong>
                          <small>{label(question.status)}</small>
                        </span>
                        <span className="pr-question-marks">
                          {question.data.marks}m
                        </span>
                      </button>
                    ))}
                    {!reviewQuestionList(
                      review.questions,
                      questionFilter,
                      questionSearch,
                    ).length && (
                      <p className="small">No questions match these filters.</p>
                    )}
                  </nav>
                  <Button
                    variant="outline"
                    disabled={busy}
                    onClick={addQuestion}
                  >
                    Add question
                  </Button>
                </div>
              </DashboardCard>
            </aside>
            <div className="pr-editor">
              <fieldset disabled={busy} className="pr-editor-fields stack">
                <DashboardCard
                  title={number ? `Question ${number}` : 'New question'}
                  description="Correct the wording and marks against the original source."
                >
                  <div className="stack">
                    <div className="two-cols">
                      <label>
                        Question number{' '}
                        <Input
                          value={number}
                          disabled={revision > 0}
                          onChange={(event) => setNumber(event.target.value)}
                        />
                      </label>
                      <label>
                        Marks{' '}
                        <Input
                          type="number"
                          min={1}
                          value={data.marks}
                          onChange={(event) =>
                            setData({
                              ...data,
                              marks: Number(event.target.value),
                            })
                          }
                        />
                      </label>
                    </div>
                    <label>
                      Shared stem{' '}
                      <Textarea
                        value={data.sharedStem}
                        onChange={(event) =>
                          setData({ ...data, sharedStem: event.target.value })
                        }
                      />
                    </label>
                    <label>
                      Full reviewed question prompt{' '}
                      <Textarea
                        rows={6}
                        value={data.prompt}
                        onChange={(event) =>
                          setData({ ...data, prompt: event.target.value })
                        }
                      />
                    </label>
                    <p className="small">
                      Linked paper pages: {sourceList(data.paperSources)}
                    </p>
                    <p className="small">
                      When you approve, AKURU links an exact question block if
                      one reviewed source block clearly matches the subpart.
                      Ambiguous wording still needs a manual block link.
                    </p>
                    <label>
                      Question status{' '}
                      <select
                        value={status}
                        onChange={(event) =>
                          setStatus(event.target.value as ReviewStatus)
                        }
                      >
                        {reviewStatuses.map((item) => (
                          <option key={item} value={item}>
                            {label(item)}
                          </option>
                        ))}
                      </select>
                    </label>
                    {status === 'excluded' && (
                      <label>
                        Exclusion reason{' '}
                        <Textarea
                          value={data.exclusionReason}
                          onChange={(event) =>
                            setData({
                              ...data,
                              exclusionReason: event.target.value,
                            })
                          }
                        />
                      </label>
                    )}
                  </div>
                </DashboardCard>
                <DashboardCard
                  title="Subpart review"
                  description="Work through the wording, marking points, evidence and coverage for each part."
                >
                  <div className="stack">
                    <div
                      className="button-row pr-part-tabs"
                      aria-label="Question subparts"
                    >
                      {data.parts.map((row, index) => (
                        <Button
                          key={index}
                          variant={activePart === index ? 'default' : 'outline'}
                          aria-pressed={activePart === index}
                          onClick={() => {
                            setActivePart(index);
                            setPaperPage(
                              row.paperSources[0]?.page || paperPage,
                            );
                            setSchemePage(
                              row.schemeSources[0]?.page || schemePage,
                            );
                            setReportPage(
                              row.reportSources[0]?.page || reportPage,
                            );
                          }}
                        >
                          {row.label} · {row.marks} marks
                        </Button>
                      ))}
                      <Button
                        variant="outline"
                        onClick={() => {
                          setData({
                            ...data,
                            parts: [
                              ...data.parts,
                              {
                                ...emptyPart(),
                                label: String.fromCharCode(
                                  97 + data.parts.length,
                                ),
                              },
                            ],
                          });
                          setActivePart(data.parts.length);
                        }}
                      >
                        Add subpart
                      </Button>
                    </div>
                    {part && (
                      <div className="panel stack">
                        <div className="two-cols">
                          <label>
                            Subpart label{' '}
                            <Input
                              value={part.label}
                              onChange={(event) =>
                                updatePart({
                                  ...part,
                                  label: event.target.value,
                                })
                              }
                            />
                          </label>
                          <label>
                            Subpart marks{' '}
                            <Input
                              type="number"
                              min={1}
                              value={part.marks}
                              onChange={(event) =>
                                updatePart({
                                  ...part,
                                  marks: Number(event.target.value),
                                })
                              }
                            />
                          </label>
                        </div>
                        <label>
                          Reviewed subpart wording{' '}
                          <Textarea
                            rows={4}
                            value={part.prompt}
                            onChange={(event) =>
                              updatePart({
                                ...part,
                                prompt: event.target.value,
                              })
                            }
                          />
                        </label>
                        <fieldset className="stack pr-fieldset">
                          <legend>Exact marking points</legend>
                          <p className="small">
                            Add one point per row. Incomplete rows can be saved
                            as draft; complete them before approval.
                          </p>
                          {part.markingPoints.map((point, index) => (
                            <div key={index} className="panel stack">
                              <strong>Point {index + 1}</strong>
                              <div className="two-cols">
                                <label>
                                  Short code (30 characters maximum)
                                  <Input
                                    maxLength={30}
                                    value={point.code}
                                    onChange={(event) =>
                                      updatePart({
                                        ...part,
                                        markingPoints: part.markingPoints.map(
                                          (row, i) =>
                                            i === index
                                              ? {
                                                  ...row,
                                                  code: event.target.value,
                                                }
                                              : row,
                                        ),
                                      })
                                    }
                                  />
                                </label>
                                <label>
                                  Kind
                                  <select
                                    value={point.kind}
                                    onChange={(event) =>
                                      updatePart({
                                        ...part,
                                        markingPoints: part.markingPoints.map(
                                          (row, i) =>
                                            i === index
                                              ? {
                                                  ...row,
                                                  kind: event.target
                                                    .value as typeof row.kind,
                                                }
                                              : row,
                                        ),
                                      })
                                    }
                                  >
                                    {[
                                      'method',
                                      'accuracy',
                                      'independent',
                                      'communication',
                                      'other',
                                    ].map((value) => (
                                      <option key={value} value={value}>
                                        {value}
                                      </option>
                                    ))}
                                  </select>
                                </label>
                              </div>
                              <label>
                                What earns the mark
                                <Textarea
                                  value={point.text}
                                  onChange={(event) =>
                                    updatePart({
                                      ...part,
                                      markingPoints: part.markingPoints.map(
                                        (row, i) =>
                                          i === index
                                            ? {
                                                ...row,
                                                text: event.target.value,
                                              }
                                            : row,
                                      ),
                                    })
                                  }
                                />
                              </label>
                              <label>
                                Depends on code (optional)
                                <Input
                                  maxLength={30}
                                  value={point.dependsOn || ''}
                                  onChange={(event) =>
                                    updatePart({
                                      ...part,
                                      markingPoints: part.markingPoints.map(
                                        (row, i) =>
                                          i === index
                                            ? {
                                                ...row,
                                                dependsOn:
                                                  event.target.value || null,
                                              }
                                            : row,
                                      ),
                                    })
                                  }
                                />
                              </label>
                              {(!point.code.trim() || !point.text.trim()) && (
                                <output className="small">
                                  Point {index + 1} is incomplete. You may save
                                  this draft, but cannot approve it yet.
                                </output>
                              )}
                              <Button
                                variant="outline"
                                onClick={() =>
                                  updatePart({
                                    ...part,
                                    markingPoints: part.markingPoints.filter(
                                      (_, i) => i !== index,
                                    ),
                                  })
                                }
                              >
                                Remove point {index + 1}
                              </Button>
                            </div>
                          ))}
                          <Button
                            variant="outline"
                            onClick={() =>
                              updatePart({
                                ...part,
                                markingPoints: [
                                  ...part.markingPoints,
                                  {
                                    code: '',
                                    kind: 'other',
                                    text: '',
                                    dependsOn: null,
                                    followThrough: false,
                                  },
                                ],
                              })
                            }
                          >
                            Add marking point
                          </Button>
                        </fieldset>
                        <label>
                          Accepted alternatives · one per line{' '}
                          <Textarea
                            value={part.alternatives.join('\n')}
                            onChange={(event) =>
                              updatePart({
                                ...part,
                                alternatives: event.target.value
                                  .split('\n')
                                  .filter(Boolean),
                              })
                            }
                          />
                        </label>
                        <label>
                          Examiner guidance{' '}
                          <Textarea
                            value={part.examinerAdvice}
                            onChange={(event) =>
                              updatePart({
                                ...part,
                                examinerAdvice: event.target.value,
                              })
                            }
                          />
                        </label>
                        <p className="small">
                          Paper pages: {sourceList(part.paperSources)} · Scheme
                          pages: {sourceList(part.schemeSources)} · Report
                          pages: {sourceList(part.reportSources)}
                        </p>
                        <div className="stack" aria-live="polite">
                          <strong>
                            Evidence linked to part{' '}
                            {part.label || activePart + 1}{' '}
                            {dirty ? '· unsaved changes' : ''}
                          </strong>
                          {(['paper', 'scheme', 'report'] as const).map(
                            (kind) => {
                              const sources = part[`${kind}Sources`];
                              return (
                                <div key={kind}>
                                  <span>
                                    {kind}:{' '}
                                    {
                                      sources.filter((source) => source.blockId)
                                        .length
                                    }{' '}
                                    exact block(s),{' '}
                                    {
                                      sources.filter(
                                        (source) => !source.blockId,
                                      ).length
                                    }{' '}
                                    page link(s)
                                  </span>
                                  <div className="button-row">
                                    {sources.map((source, index) => (
                                      <Button
                                        key={`${source.page}-${source.blockId || index}`}
                                        variant="outline"
                                        onClick={() => showLinked(kind, source)}
                                      >
                                        {source.blockId ? 'Block' : 'Page'} ·
                                        PDF page {source.page} ·{' '}
                                        {source.blockId
                                          ? (kind === 'paper'
                                              ? paperExtraction
                                              : kind === 'scheme'
                                                ? schemeExtraction
                                                : reportExtraction
                                            )?.pages
                                              .find(
                                                (page) =>
                                                  page.pageNumber ===
                                                  source.page,
                                              )
                                              ?.blocks.find(
                                                (block) =>
                                                  block.id === source.blockId,
                                              )
                                              ?.text.slice(0, 45) ||
                                            'Visual block'
                                          : 'Page evidence'}
                                      </Button>
                                    ))}
                                  </div>
                                </div>
                              );
                            },
                          )}
                        </div>
                        <h3 className="pr-section-title">
                          Curriculum coverage
                        </h3>
                        <label>
                          Coverage decision{' '}
                          <select
                            value={part.coverage}
                            onChange={(event) =>
                              updatePart({
                                ...part,
                                coverage: event.target.value as CoverageStatus,
                                topicRefs: [],
                              })
                            }
                          >
                            {coverageStatuses.map((value) => (
                              <option value={value} key={value}>
                                {label(value)}
                              </option>
                            ))}
                          </select>
                        </label>
                        {part.coverage === 'supported' && (
                          <fieldset>
                            <legend>Published {paper.subject} topics</legend>
                            {topics.map((topic) => (
                              <label
                                key={topic.topicRef}
                                style={{ display: 'block' }}
                              >
                                <input
                                  type="checkbox"
                                  checked={part.topicRefs.includes(
                                    topic.topicRef,
                                  )}
                                  onChange={(event) =>
                                    updatePart({
                                      ...part,
                                      topicRefs: event.target.checked
                                        ? [...part.topicRefs, topic.topicRef]
                                        : part.topicRefs.filter(
                                            (ref) => ref !== topic.topicRef,
                                          ),
                                    })
                                  }
                                />{' '}
                                {topic.code} · {topic.title}
                              </label>
                            ))}
                          </fieldset>
                        )}
                        <label>
                          Coverage reason{' '}
                          <Textarea
                            value={part.coverageReason}
                            onChange={(event) =>
                              updatePart({
                                ...part,
                                coverageReason: event.target.value,
                              })
                            }
                          />
                        </label>
                        <label>
                          Subpart review status{' '}
                          <select
                            value={part.status}
                            onChange={(event) =>
                              updatePart({
                                ...part,
                                status: event.target.value as ReviewStatus,
                              })
                            }
                          >
                            {reviewStatuses
                              .filter((item) => item !== 'excluded')
                              .map((value) => (
                                <option value={value} key={value}>
                                  {label(value)}
                                </option>
                              ))}
                          </select>
                        </label>
                      </div>
                    )}
                  </div>
                </DashboardCard>
                <DashboardCard
                  title="Question visuals"
                  description="Check the crop and assign each visual to the parts that need it."
                >
                  <div className="stack">
                    <strong>
                      Question visuals · {allVisualIds.length} candidates or
                      assigned {dirty ? '· unsaved' : ''}
                    </strong>
                    <p className="small">
                      Assign a visual to every subpart that needs it. Use Shared
                      only when it applies to the entire question. Unassigned
                      candidates cannot be approved.
                    </p>
                    {allVisualIds.map((assetId) => {
                      const crop = availableCrops.find(
                        (item) => item.assetId === assetId,
                      );
                      return (
                        <div key={assetId} className="panel stack">
                          <strong>
                            {crop?.approved
                              ? 'Reviewed visual'
                              : 'Candidate · needs review'}{' '}
                            · {crop?.kind || 'visual'} · PDF page{' '}
                            {crop?.page || '?'}
                          </strong>
                          <Image
                            src={`/api/v1/documents/${paperId}/assets/${assetId}/content`}
                            alt={crop?.altText || 'Unreviewed candidate visual'}
                            width={560}
                            height={400}
                            unoptimized
                            style={{
                              width: '100%',
                              height: 'auto',
                              maxWidth: 560,
                              objectFit: 'contain',
                            }}
                          />
                          <p className="small">
                            {crop?.altText ||
                              'Check the crop and enter an accessible description before approval.'}
                          </p>
                          <fieldset>
                            <legend>Where this visual belongs</legend>
                            <div className="button-row">
                              <label>
                                <input
                                  type="checkbox"
                                  checked={data.visualAssetIds.includes(
                                    assetId,
                                  )}
                                  onChange={(event) =>
                                    setVisualLocation(
                                      assetId,
                                      'shared',
                                      event.target.checked,
                                    )
                                  }
                                />{' '}
                                Shared question stem
                              </label>
                              {data.parts.map((item, index) => (
                                <label key={index}>
                                  <input
                                    type="checkbox"
                                    checked={item.visualAssetIds.includes(
                                      assetId,
                                    )}
                                    onChange={(event) =>
                                      setVisualLocation(
                                        assetId,
                                        index,
                                        event.target.checked,
                                      )
                                    }
                                  />{' '}
                                  Part {item.label || index + 1}
                                </label>
                              ))}
                            </div>
                          </fieldset>
                          {data.candidateVisualAssetIds.includes(assetId) && (
                            <output className="small">
                              Unassigned: select a part or the shared stem, or
                              remove this candidate.
                            </output>
                          )}
                          {crop && !crop.approved && (
                            <>
                              <label>
                                Describe this candidate for students (editable draft; at least 10 characters){' '}
                                <Textarea
                                  value={candidateDescriptions[assetId] ?? crop.altText ?? ''}
                                  onChange={(event) =>
                                    setCandidateDescriptions((current) => ({
                                      ...current,
                                      [assetId]: event.target.value,
                                    }))
                                  }
                                />
                              </label>
                              <div className="button-row">
                                <Button
                                  variant="outline"
                                  disabled={
                                    busy ||
                                    (
                                      candidateDescriptions[assetId] ?? crop.altText ?? ''
                                    ).trim().length < 10
                                  }
                                  onClick={() => void keepCandidate(crop)}
                                >
                                  Keep this crop and attach reviewed visual
                                </Button>
                                <Button
                                  variant="outline"
                                  onClick={() => {
                                    setPaperPage(crop.page);
                                    setCropBox(crop.bounds);
                                    setCropKind(crop.kind);
                                    setReplaceCandidateId(assetId);
                                    setCropOpen(true);
                                  }}
                                >
                                  Adjust crop
                                </Button>
                              </div>
                            </>
                          )}
                          <Button
                            variant="outline"
                            onClick={() =>
                              setData((current) => ({
                                ...current,
                                visualAssetIds: current.visualAssetIds.filter(
                                  (id) => id !== assetId,
                                ),
                                candidateVisualAssetIds:
                                  current.candidateVisualAssetIds.filter(
                                    (id) => id !== assetId,
                                  ),
                                parts: current.parts.map((item) => ({
                                  ...item,
                                  visualAssetIds: item.visualAssetIds.filter(
                                    (id) => id !== assetId,
                                  ),
                                })),
                              }))
                            }
                          >
                            Remove visual from question
                          </Button>
                        </div>
                      );
                    })}
                    {!!availableCrops.length && (
                      <label>
                        Attach an existing reviewed crop{' '}
                        <select
                          value=""
                          onChange={(event) => {
                            const id = event.target.value;
                            if (id)
                              setData((current) => ({
                                ...current,
                                candidateVisualAssetIds:
                                  current.candidateVisualAssetIds.includes(id)
                                    ? current.candidateVisualAssetIds
                                    : [...current.candidateVisualAssetIds, id],
                              }));
                          }}
                        >
                          <option value="">Choose a crop</option>
                          {availableCrops
                            .filter(
                              (crop) =>
                                crop.approved &&
                                !allVisualIds.includes(crop.assetId),
                            )
                            .map((crop) => (
                              <option key={crop.assetId} value={crop.assetId}>
                                {crop.kind} · PDF page {crop.page} ·{' '}
                                {crop.altText.slice(0, 70)}
                              </option>
                            ))}
                        </select>
                      </label>
                    )}
                    <label>
                      Fallback accessible description for older visuals{' '}
                      <Textarea
                        value={data.visualAltText}
                        onChange={(event) =>
                          setData({
                            ...data,
                            visualAltText: event.target.value,
                          })
                        }
                      />
                    </label>
                    <details
                      className="pr-crop-disclosure"
                      open={cropOpen}
                      onToggle={(event) =>
                        setCropOpen(event.currentTarget.open)
                      }
                    >
                      <summary>Create or adjust a visual crop</summary>
                      <VisualCropEditor
                        key={`${paperPage}-${replaceCandidateId || ''}-${JSON.stringify(cropBox)}`}
                        paperId={paperId}
                        extraction={paperExtraction}
                        pageNumber={paperPage}
                        initialBox={cropBox}
                        initialKind={cropKind}
                        onCreated={(assetId, altText, kind, bounds) => {
                          setAvailableCrops((current) => [
                            ...current,
                            {
                              assetId,
                              page: paperPage,
                              kind,
                              altText,
                              approved: true,
                              bounds,
                            },
                          ]);
                          setData((current) => ({
                            ...current,
                            visualAssetIds: current.visualAssetIds.filter(
                              (id) => id !== replaceCandidateId,
                            ),
                            candidateVisualAssetIds: [
                              ...current.candidateVisualAssetIds.filter(
                                (id) => id !== replaceCandidateId,
                              ),
                              assetId,
                            ],
                            parts: current.parts.map((item) => ({
                              ...item,
                              visualAssetIds: item.visualAssetIds.filter(
                                (id) => id !== replaceCandidateId,
                              ),
                            })),
                            visualAltText: current.visualAltText || altText,
                          }));
                          setReplaceCandidateId(null);
                          setNotice(
                            'Reviewed visual created. Assign it to the relevant part and save the question.',
                          );
                        }}
                      />
                    </details>
                    <details>
                      <summary>Preview this question as a student</summary>
                      <div className="panel stack" style={{ maxWidth: 700 }}>
                        <strong>
                          Question {number} · {data.marks} marks
                        </strong>
                        {data.sharedStem && <p>{data.sharedStem}</p>}
                        {data.visualAssetIds.map((assetId) => (
                          <figure key={assetId} style={{ margin: 0 }}>
                            <Image
                              src={`/api/v1/documents/${paperId}/assets/${assetId}/content`}
                              alt={
                                availableCrops.find(
                                  (crop) => crop.assetId === assetId,
                                )?.altText ||
                                data.visualAltText ||
                                'Question visual'
                              }
                              width={650}
                              height={450}
                              unoptimized
                              style={{
                                maxWidth: '100%',
                                width: 'auto',
                                height: 'auto',
                                maxHeight: 450,
                              }}
                            />
                          </figure>
                        ))}
                        {data.parts.map((row) => (
                          <section key={row.label} className="panel stack">
                            <strong>
                              Part ({row.label}) · {row.marks} marks
                            </strong>
                            <p style={{ whiteSpace: 'pre-wrap' }}>
                              {row.prompt}
                            </p>
                            {row.visualAssetIds.map((assetId) => (
                              <figure key={assetId} style={{ margin: 0 }}>
                                <Image
                                  src={`/api/v1/documents/${paperId}/assets/${assetId}/content`}
                                  alt={
                                    availableCrops.find(
                                      (crop) => crop.assetId === assetId,
                                    )?.altText ||
                                    data.visualAltText ||
                                    'Question visual'
                                  }
                                  width={650}
                                  height={450}
                                  unoptimized
                                  style={{
                                    maxWidth: '100%',
                                    width: 'auto',
                                    height: 'auto',
                                    maxHeight: 450,
                                  }}
                                />
                              </figure>
                            ))}
                          </section>
                        ))}
                      </div>
                    </details>
                  </div>
                </DashboardCard>
              </fieldset>
            </div>
            <aside
              className="pr-sources"
              aria-label="Source evidence"
              data-comparison={compareSources}
            >
              <DashboardCard
                title="Source evidence"
                description={`Reviewing question ${number || '—'} · part ${part?.label || '—'}`}
                action={
                  <Button
                    variant="outline"
                    size="sm"
                    aria-pressed={compareSources}
                    onClick={() => setCompareSources(!compareSources)}
                  >
                    {compareSources ? (
                      <Minimize2 size={14} />
                    ) : (
                      <Maximize2 size={14} />
                    )}{' '}
                    {compareSources ? 'Close comparison' : 'Compare sources'}
                  </Button>
                }
              >
                {compareSources ? (
                  <div className="pr-source-comparison">
                    <SourcePage
                      documentId={paperId}
                      extraction={paperExtraction}
                      title="Question paper"
                      selectedPage={paperPage}
                      onPage={setPaperPage}
                      linked={part?.paperSources || []}
                      partLabel={part?.label || String(activePart + 1)}
                      sourceKind="paper"
                      onToggle={
                        part && !busy
                          ? (id) => toggleLink('paper', id)
                          : undefined
                      }
                      onCropBox={(box) => {
                        setCropBox(box);
                        setCropOpen(true);
                      }}
                    />{' '}
                    <SourcePage
                      documentId={review.schemeDocumentId}
                      extraction={schemeExtraction}
                      title="Exact marking scheme"
                      selectedPage={schemePage}
                      onPage={setSchemePage}
                      linked={part?.schemeSources || []}
                      partLabel={part?.label || String(activePart + 1)}
                      sourceKind="scheme"
                      onToggle={
                        part && !busy
                          ? (id) => toggleLink('scheme', id)
                          : undefined
                      }
                    />
                  </div>
                ) : (
                  <Tabs
                    value={sourceTab}
                    onValueChange={(value) => setSourceTab(String(value))}
                  >
                    <TabsList
                      aria-label="Review source"
                      className="pr-source-tabs"
                    >
                      <TabsTrigger value="paper">Paper</TabsTrigger>
                      <TabsTrigger value="scheme">Marking scheme</TabsTrigger>
                      <TabsTrigger value="report">Report</TabsTrigger>
                    </TabsList>
                    <TabsContent
                      value="paper"
                      id="review-source-paper"
                      tabIndex={-1}
                    >
                      <SourcePage
                        documentId={paperId}
                        extraction={paperExtraction}
                        title="Question paper"
                        selectedPage={paperPage}
                        onPage={setPaperPage}
                        linked={part?.paperSources || []}
                        partLabel={part?.label || String(activePart + 1)}
                        sourceKind="paper"
                        onToggle={
                          part && !busy
                            ? (id) => toggleLink('paper', id)
                            : undefined
                        }
                        onCropBox={(box) => {
                          setCropBox(box);
                          setCropOpen(true);
                        }}
                      />
                    </TabsContent>
                    <TabsContent
                      value="scheme"
                      id="review-source-scheme"
                      tabIndex={-1}
                    >
                      <SourcePage
                        documentId={review.schemeDocumentId}
                        extraction={schemeExtraction}
                        title="Exact marking scheme"
                        selectedPage={schemePage}
                        onPage={setSchemePage}
                        linked={part?.schemeSources || []}
                        partLabel={part?.label || String(activePart + 1)}
                        sourceKind="scheme"
                        onToggle={
                          part && !busy
                            ? (id) => toggleLink('scheme', id)
                            : undefined
                        }
                      />
                    </TabsContent>
                    <TabsContent
                      value="report"
                      id="review-source-report"
                      tabIndex={-1}
                    >
                      <SourcePage
                        documentId={review.reportDocumentId}
                        extraction={reportExtraction}
                        title="Examiner report"
                        selectedPage={reportPage}
                        onPage={setReportPage}
                        linked={part?.reportSources || []}
                        partLabel={part?.label || String(activePart + 1)}
                        sourceKind="report"
                        onToggle={
                          part && !busy
                            ? (id) => toggleLink('report', id)
                            : undefined
                        }
                      />
                    </TabsContent>
                  </Tabs>
                )}
              </DashboardCard>
            </aside>
          </div>
        </>
      )}
    </div>
  );
}
