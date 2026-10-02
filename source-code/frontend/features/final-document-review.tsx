'use client';

import { useEffect, useState } from 'react';
import Image from 'next/image';
import { Button } from '@/components/ui/button';
import { ScientificTextEditor, ScientificTextPreview, scientificPlainText } from '@/components/scientific-text-editor';
import {
  confirmFinalDocumentReview, errorMessage, getFinalDocumentReview,
  paragraphOperation, previewDocumentParagraphReconstruction, reconstructDocumentParagraphs, updateExtractionBlock,
  type DocumentExtraction, type FinalDocumentReview, type ScientificTextContent,
} from '@/api';

export function FinalDocumentReviewWorkspace({ documentId, notify, extractionChanged, readOnly = false }: {
  documentId: string;
  notify: (message: string) => void;
  extractionChanged: (value: DocumentExtraction) => void;
  readOnly?: boolean;
}) {
  const [review, setReview] = useState<FinalDocumentReview | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [dirty, setDirty] = useState(false);
  const [previewMode, setPreviewMode] = useState(readOnly);
  const displayPreview = readOnly || previewMode;
  const load = async () => setReview(await getFinalDocumentReview(documentId));
  useEffect(() => {
    let active = true;
    void getFinalDocumentReview(documentId)
      .then((value) => { if (active) setReview(value); })
      .catch((cause) => { if (active) setError(errorMessage(cause)); });
    return () => { active = false; };
  }, [documentId]);
  useEffect(() => {
    if (!dirty) return;
    const protect = (event: BeforeUnloadEvent) => { event.preventDefault(); };
    window.addEventListener('beforeunload', protect);
    return () => window.removeEventListener('beforeunload', protect);
  }, [dirty]);
  async function run(work: () => Promise<DocumentExtraction>, message: string) {
    setBusy(true); setError('');
    try { const result = await work(); extractionChanged(result); await load(); setDirty(false); notify(message); }
    catch (cause) { setError(errorMessage(cause)); }
    finally { setBusy(false); }
  }
  if (!review) return <section className="panel"><p>{error || 'Loading the final reviewed document…'}</p></section>;
  return <section className="panel stack final-document-workspace" aria-labelledby="final-document-title">
    <div className="spread"><div><h2 id="final-document-title">{readOnly ? 'Published document content' : 'Review complete document'}</h2>
      <p>{readOnly ? 'This reviewed source is published and read-only. Upload a revised source and publish a new Topic version to change what students use.' : 'Read and correct the exact continuous content AKURU will publish. Every edit updates the underlying review draft.'}</p></div>
      <span className={`review-status-badge ${review.confirmed ? 'review-status-complete' : 'review-status-required'}`}>{review.confirmed ? 'Final document confirmed' : 'Confirmation required'}</span>
    </div>
    {error && <p className="error" role="alert">{error}</p>}
    {dirty && <output className="source-note"><strong>Unsaved changes.</strong> Save the edited paragraph before leaving this page or confirming the document.</output>}
    <div className="button-row">
      <Button variant="outline" disabled={busy} onClick={() => window.print()}>Print or save private preview</Button>
      {!readOnly && <Button variant="outline" aria-pressed={previewMode} onClick={() => setPreviewMode((value) => !value)}>{previewMode ? 'Return to editing' : 'Preview Student version'}</Button>}
      {!readOnly && <Button variant="outline" disabled={busy} onClick={() => { setBusy(true); setError('');
        void previewDocumentParagraphReconstruction(documentId).then((preview) => {
          const summary = `${preview.version}\n${preview.pageCount} pages\n${preview.beforeBlockCount} current blocks → ${preview.afterBlockCount} reconstructed blocks\n${preview.reviewedBlockCount} manually reviewed blocks would be reopened.\n\nApply this reconstruction to the unpublished review draft?`;
          if (window.confirm(summary)) return run(() => reconstructDocumentParagraphs(documentId, preview.reviewedBlockCount > 0), 'Paragraph reconstruction applied to the review draft.');
        }).catch((cause) => setError(errorMessage(cause))).finally(() => setBusy(false));
      }}>Re-run paragraph reconstruction</Button>}
      {!readOnly && <Button className="primary" disabled={busy || dirty || review.blockers.length > 0 || review.confirmed} onClick={() => {
        if (!window.confirm('Confirm this complete document as the exact reviewed content AKURU may publish?')) return;
        setBusy(true); setError(''); void confirmFinalDocumentReview(documentId).then(setReview)
          .then(() => notify('Final reviewed document confirmed.'))
          .catch((cause) => setError(errorMessage(cause))).finally(() => setBusy(false));
      }}>Confirm final reviewed document</Button>}
    </div>
    <div className="source-note"><strong>Final review summary</strong><p>Reconstruction {review.reconstructionVersion} · content fingerprint {review.contentHash.slice(0, 12)}</p>
      {review.blockers.length ? <><p><strong>{review.blockers.length} items remain:</strong></p><ul>{review.blockers.slice(0, 20).map((blocker) => <li key={blocker}>{blocker}</li>)}</ul></> : <p>Every page label and review block is complete.</p>}
    </div>
    {review.pages.map((page) => <article className="final-document-page stack" key={page.id}>
      <div className="spread"><h3>Page {page.printedPageLabel || page.pageNumber}</h3><a href={`#extraction-page-${page.pageNumber}`}>Open page review</a></div>
      <div className="final-document-page-layout"><aside><Image src={`/api/v1/documents/${documentId}/assets/${page.renderAssetId}/content`} alt={`Original textbook page ${page.printedPageLabel || page.pageNumber}`} width={360} height={500} unoptimized loading="lazy" style={{ width: '100%', height: 'auto', objectFit: 'contain' }}/></aside>
      <div className="stack">{page.blocks.map((block, index) => {
        const content = (block.metadata.scientificContent as ScientificTextContent | undefined) || { version: 1 as const, text: block.text, plainText: scientificPlainText(block.text), marks: [] };
        return <section className="final-document-block stack" key={block.id}>
          <div className="spread"><span><strong>{block.kind}</strong> · {Math.round(block.confidence * 100)}% confidence</span><span>{block.needsReview ? 'Needs block review' : 'Reviewed'}</span></div>
          {displayPreview ? <div className="scientific-preview" aria-label="Student version"><ScientificTextPreview content={content}/></div> : <ScientificTextEditor id={`final-${block.id}`} content={content} onChange={(value) => { setDirty(true); setReview({ ...review, confirmed: false, pages: review.pages.map((row) => row.id === page.id ? { ...row, blocks: row.blocks.map((item) => item.id === block.id ? { ...item, text: value.text, metadata: { ...item.metadata, scientificContent: value } } : item) } : row) }); }}/>} 
          {!displayPreview && <><details><summary>Compare with extracted version</summary><pre className="source-note">{block.rawText}</pre></details>
          <div className="button-row">
            <Button disabled={busy} onClick={() => void run(() => updateExtractionBlock(documentId, block.id, { kind: block.kind, text: block.text, latex: block.latex, sequenceNumber: block.sequenceNumber, scientificContent: block.metadata.scientificContent as ScientificTextContent | undefined }), 'Reviewed paragraph saved.')}>Save paragraph</Button>
            <Button variant="outline" disabled={busy || index === 0} onClick={() => void run(() => paragraphOperation(documentId, block.id, 'join_previous'), 'Paragraphs joined for review.')}>Join with previous</Button>
            <Button variant="outline" disabled={busy} onClick={() => { const raw = window.prompt('Split after which character?', String(Math.floor(block.text.length / 2))); if (raw) void run(() => paragraphOperation(documentId, block.id, 'split', Number(raw)), 'Paragraph split for review.'); }}>Split paragraph</Button>
            <Button variant="outline" disabled={busy || block.rawText === block.text} onClick={() => void run(() => paragraphOperation(documentId, block.id, 'restore_extracted'), 'Original extracted text restored for review.')}>Restore extracted version</Button>
          </div></>}
        </section>;
      })}</div></div>
    </article>)}
  </section>;
}
