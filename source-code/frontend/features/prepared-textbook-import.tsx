import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { errorMessage, getTopicSources } from '@/api';
import { confirmPreparedReview, getPreparedReview, uploadPreparedTextbook, type PreparedReview, type PreparedSummary } from '@/api/textbooks/prepared-textbooks.api';

/** A deliberate draft workflow; imports cannot replace a released primary source. */
export function PreparedTextbookImport({ bookRef, topicRef, refreshBook, notify, navigate }: {
  bookRef: string; topicRef: string; refreshBook: () => Promise<void>; notify: (message: string) => void; navigate: (to: string) => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<PreparedSummary | null>(null);
  const [drafts, setDrafts] = useState<{ documentId: string; filename: string; sequence: number; reviewStatus: string; role: string }[]>([]);
  const [review, setReview] = useState<PreparedReview | null>(null);
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const load = async () => {
    const sources = await getTopicSources(bookRef, topicRef);
    setDrafts(sources.filter(source => source.filename === 'prepared-textbook.zip'));
  };
  useEffect(() => {
    let active = true;
    void getTopicSources(bookRef, topicRef).then(sources => {
      if (active) setDrafts(sources.filter(source => source.filename === 'prepared-textbook.zip'));
    }).catch(e => { if (active) setError(errorMessage(e)); });
    return () => { active = false; };
  }, [bookRef, topicRef]);
  const perform = async (work: () => Promise<void>) => {
    setBusy(true); setError('');
    try { await work(); } catch (e) { setError(errorMessage(e)); } finally { setBusy(false); }
  };
  return <details className="topic-upload-panel">
    <summary><strong>Import prepared screenshot textbook</strong></summary>
    <p>Import a validated AKURU package as a separate supporting draft. Existing published content stays available. No OCR or paid AI request is made.</p>
    <label>Prepared package (.zip)
      <input type="file" accept=".zip,application/zip" disabled={busy} onChange={e => { setFile(e.target.files?.[0] ?? null); setPreview(null); }} />
    </label>
    <Button disabled={!file || busy} onClick={() => void perform(async () => {
      const result = await uploadPreparedTextbook(bookRef, topicRef, file!, 'preview'); setPreview(result);
    })}>Validate and preview package</Button>
    {busy && <output>Processing package… Please keep this page open.</output>}
    {error && <p role="alert">{error}</p>}
    {preview && <section aria-label="Prepared package preview">
      <h4>{preview.title}</h4>
      <p>{preview.pageCount} pages · {preview.blockCount} teaching blocks · {preview.figureCount} figures · {preview.exerciseCount} exercises · {preview.issues.length} review decisions</p>
      <p>Destination: this topic · Source role: Supporting text · Not approved or published</p>
      <Button disabled={busy || !file} onClick={() => void perform(async () => {
        const result = await uploadPreparedTextbook(bookRef, topicRef, file!, 'import');
        await load(); await refreshBook();
        notify(result.alreadyImported ? 'This prepared package is already imported.' : 'Prepared package imported as a separate draft.');
        setPreview(null);
      })}>Import supporting draft</Button>
    </section>}
    {drafts.map(draft => <div key={draft.documentId}>
      <p>{draft.filename} · Source {draft.sequence} · {draft.role} · {draft.reviewStatus.replaceAll('_', ' ')}</p>
      <Button disabled={busy} onClick={() => void perform(async () => {
        const result = await getPreparedReview(bookRef, topicRef, draft.documentId);
        setReview(result); setNotes(result.decisions); setConfirmed(false);
      })}>Review prepared draft</Button>
    </div>)}
    {review && <section aria-label="Prepared draft review">
      <h4>Whole-document review and exception decisions</h4>
      <Button onClick={() => navigate(review.reviewUrl)}>Open editable document and source pages</Button>
      <p>Inspect the assembled document, tables, exercises and original pages. Make wording corrections in the normal review editor, then reload this review before confirming. Figures require separate visual approval under Manage topic sources.</p>
      {review.issues.map(issue => <div key={issue.id}>
        <h5>{issue.id}: {issue.title} · Page {issue.page}</h5>
        <p>{issue.reason}</p><p>{issue.action}</p>
        <label htmlFor={`${topicRef}-${issue.id}`}>Reviewed teaching clarification or decision</label>
          <Textarea id={`${topicRef}-${issue.id}`} disabled={busy || review.immutable} value={notes[issue.id] ?? ''} maxLength={5000}
            onChange={e => { setNotes(previous => ({ ...previous, [issue.id]: e.target.value })); setConfirmed(false); }} />
      </div>)}
      <label><input type="checkbox" checked={confirmed} disabled={busy || review.immutable} onChange={e => setConfirmed(e.target.checked)} /> I reviewed the complete document, printed page labels, source evidence and every exception. My notes will be included as teaching clarifications.</label>
      <Button disabled={busy || review.immutable || !confirmed || review.issues.some(issue => !notes[issue.id]?.trim())} onClick={() => void perform(async () => {
        const result = await confirmPreparedReview(bookRef, topicRef, review.documentId, { contentHash: review.contentHash, confirmWholeDocument: confirmed, decisions: notes });
        setReview(result); setConfirmed(false); await refreshBook(); notify('Prepared document review confirmed. Visual approval and topic publication are still separate.');
      })}>Confirm whole-document review</Button>
      <output>{review.confirmed ? 'Whole-document review confirmed.' : 'Whole-document review not yet confirmed.'}{review.immutable ? ' Published evidence is read-only.' : ''}</output>
    </section>}
  </details>;
}
