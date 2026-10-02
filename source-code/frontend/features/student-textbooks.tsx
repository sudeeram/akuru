'use client';

import Image from 'next/image';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, BookOpen, ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  errorMessage, getStudentTextbooks, getStudentTextbookTopic,
  type StudentTextbook, type StudentTextbookVisual,
} from '@/api';
import { queryKeys } from '@/lib/query-keys';
import { studentTextbookPaths } from '@/lib/routes';
import { readableTextbookBlocks } from '@/lib/textbook-display.mjs';
import { Empty, Heading } from './shared';

type Route = { bookRef?: string; topicRef?: string; view: 'text' | 'visual'; source: number; page: number };
type Props = {
  actorRef: string;
  subjects: { id: string; name: string }[];
  route: Route;
  navigate: (to: string) => void;
};

const publishedDate = (value: string) => new Date(value).toLocaleDateString(undefined, {
  year: 'numeric', month: 'long', day: 'numeric',
});

function Visual({ visual }: { visual: StudentTextbookVisual }) {
  return <figure className="student-textbook-visual">
    <Image src={visual.contentUrl} alt={visual.altText || visual.caption || 'Approved textbook diagram'}
      width={620} height={440} unoptimized loading="lazy" style={{ width: 'auto', height: 'auto', maxWidth: '100%', maxHeight: '24rem' }} />
    {visual.caption && <figcaption>{visual.caption}</figcaption>}
  </figure>;
}

function BookTopics({ book, navigate }: { book: StudentTextbook; navigate: (to: string) => void }) {
  return <div className="student-textbook-groups">
    {book.groups.map((group) => <section className="panel stack" key={group.code}>
      <h3>{book.groupLabel === 'module' ? 'Module' : 'Unit'} {group.code} · {group.title}</h3>
      <div className="student-textbook-topic-list">
        {group.topics.map((topic) => <button className="student-textbook-topic" type="button" key={topic.topicRef}
          onClick={() => navigate(studentTextbookPaths.topic(book.textbookRef, topic.topicRef))}>
          <span><strong>{topic.code} · {topic.title}</strong><small>Topic content v{topic.contentVersion} · published {publishedDate(topic.publishedAt)}</small></span>
          <span className="small">{topic.pageCount} {topic.pageCount === 1 ? 'page' : 'pages'} →</span>
        </button>)}
      </div>
    </section>)}
  </div>;
}

export function StudentTextbooks({ actorRef, subjects, route, navigate }: Props) {
  const booksQuery = useQuery({ queryKey: queryKeys.textbooks.studentLibrary(actorRef), queryFn: getStudentTextbooks });
  const topicQuery = useQuery({
    queryKey: queryKeys.textbooks.studentTopic(actorRef, route.bookRef || '', route.topicRef || ''),
    queryFn: () => getStudentTextbookTopic(route.bookRef!, route.topicRef!),
    enabled: Boolean(route.bookRef && route.topicRef),
  });
  const books = booksQuery.data?.textbooks || [];
  const book = books.find((item) => item.textbookRef === route.bookRef);
  const topic = topicQuery.data;
  const page = topic?.pages[Math.min(Math.max(route.page, 1), topic.pages.length) - 1];
  const reference = topic?.visualReferences.find((item) => item.ordinal === route.source);
  const referencePage = reference?.pages[Math.min(Math.max(route.page, 1), reference.pages.length) - 1];
  const subjectName = (id: string) => subjects.find((item) => item.id === id)?.name || id;

  if (booksQuery.isPending) return <section className="panel" aria-live="polite">Loading your published textbooks…</section>;
  if (booksQuery.error) return <section className="panel error" role="alert">{errorMessage(booksQuery.error)}</section>;

  return <>
    <Heading eyebrow="YOUR LEARNING LIBRARY" title="Published textbooks">
      Read the published Topics in your enrolled subjects. Your Grade and Term still determine which Topics appear in practice and exams.
    </Heading>
    {!books.length && <Empty title="No published textbook Topics yet">Your Admin can publish a reviewed Topic in one of your subjects to make it available here.</Empty>}
    {route.bookRef && <div className="button-row"><Button variant="outline" onClick={() => navigate(studentTextbookPaths.library)}><ArrowLeft size={16}/> All textbooks</Button>
      {route.topicRef && <Button variant="outline" onClick={() => navigate(studentTextbookPaths.book(route.bookRef!))}>All Topics in this textbook</Button>}</div>}
    {!route.bookRef && <div className="student-textbook-library">
      {books.map((item) => <article className="panel stack" key={item.textbookRef}>
        <span className="eyebrow">{subjectName(item.subjectId)}</span>
        <h2>{item.title}</h2>
        <p>{item.edition}{item.publisher ? ` · ${item.publisher}` : ''}</p>
        <p className="small">Published structure v{item.structureVersion} · {publishedDate(item.structurePublishedAt)} · {item.groups.reduce((sum, group) => sum + group.topics.length, 0)} available Topics</p>
        <Button className="primary" onClick={() => navigate(studentTextbookPaths.book(item.textbookRef))}><BookOpen size={17}/> Browse Topics</Button>
      </article>)}
    </div>}
    {route.bookRef && !book && <section className="panel" role="alert">This textbook is unavailable in your enrolled subjects.</section>}
    {book && !route.topicRef && <>
      <section className="panel stack"><span className="eyebrow">{subjectName(book.subjectId)}</span><h2>{book.title}</h2>
        <p>{book.edition}{book.publisher ? ` · ${book.publisher}` : ''}</p>
        <p className="small">Published structure v{book.structureVersion} · {publishedDate(book.structurePublishedAt)}</p></section>
      <BookTopics book={book} navigate={navigate}/>
    </>}
    {book && route.topicRef && <>
      {topicQuery.isPending && <section className="panel" aria-live="polite">Opening the published Topic…</section>}
      {topicQuery.error && <section className="panel error" role="alert">{errorMessage(topicQuery.error)}</section>}
      {topic && <section className="student-textbook-reader stack">
        <div className="panel stack"><span className="eyebrow">{subjectName(topic.subjectId)} · {topic.groupCode} · {topic.groupTitle}</span>
          <h2>{topic.topicCode} · {topic.topicTitle}</h2>
          <p className="small">Topic content v{topic.contentVersion} · published {publishedDate(topic.publishedAt)} · {topic.pages.length} pages</p>
        </div>
        <nav className="button-row" aria-label="Choose textbook reading view">
          <Button variant={route.view === 'text' ? 'default' : 'outline'} aria-pressed={route.view === 'text'}
            onClick={() => navigate(studentTextbookPaths.topic(topic.textbookRef, topic.topicRef))}>Reviewed text</Button>
          {!!topic.visualReferences.length && <Button variant={route.view === 'visual' ? 'default' : 'outline'} aria-pressed={route.view === 'visual'}
            onClick={() => navigate(studentTextbookPaths.visual(topic.textbookRef, topic.topicRef))}>Visual reference · original pages</Button>}
        </nav>
        {route.view === 'visual' ? reference && referencePage ? <>
          {topic.visualReferences.length > 1 && <label className="student-textbook-reference-source">Visual reference <select aria-label="Choose visual reference source" value={reference.ordinal}
            onChange={(event) => navigate(studentTextbookPaths.visual(topic.textbookRef, topic.topicRef, Number(event.target.value)))}>
            {topic.visualReferences.map((item) => <option key={item.ordinal} value={item.ordinal}>{item.filename}</option>)}
          </select></label>}
          <section className="panel stack"><h3>{reference.filename}</h3><p className="small">Reviewed Visual Reference · {reference.pages.length} labelled pages</p></section>
          <nav className="student-textbook-page-nav" aria-label="Visual reference pages">
            <Button variant="outline" disabled={referencePage.ordinal === 1} onClick={() => navigate(studentTextbookPaths.visual(topic.textbookRef, topic.topicRef, reference.ordinal, referencePage.ordinal - 1))}><ChevronLeft size={17}/> Previous</Button>
            <label>Page <select aria-label="Choose visual reference page" value={referencePage.ordinal} onChange={(event) => navigate(studentTextbookPaths.visual(topic.textbookRef, topic.topicRef, reference.ordinal, Number(event.target.value)))}>
              {reference.pages.map((item) => <option key={item.ordinal} value={item.ordinal}>{item.printedPage} ({item.ordinal} of {reference.pages.length})</option>)}
            </select></label>
            <Button variant="outline" disabled={referencePage.ordinal === reference.pages.length} onClick={() => navigate(studentTextbookPaths.visual(topic.textbookRef, topic.topicRef, reference.ordinal, referencePage.ordinal + 1))}>Next <ChevronRight size={17}/></Button>
          </nav>
          <figure className="panel student-textbook-reference-page"><Image src={referencePage.imageUrl}
            alt={`Original textbook page ${referencePage.printedPage} from ${reference.filename}`}
            width={1100} height={1500} unoptimized loading="lazy" style={{ width: '100%', height: 'auto', objectFit: 'contain' }}/>
            <figcaption>Page {referencePage.printedPage}</figcaption></figure>
        </> : <Empty title="Visual reference unavailable">Choose a reviewed Visual Reference for this published Topic.</Empty> : page ? <>
          <nav className="student-textbook-page-nav" aria-label="Textbook pages">
            <Button variant="outline" disabled={page.ordinal === 1} onClick={() => navigate(studentTextbookPaths.topic(topic.textbookRef, topic.topicRef, page.ordinal - 1))}><ChevronLeft size={17}/> Previous</Button>
            <label>Page <select aria-label="Choose textbook page" value={page.ordinal} onChange={(event) => navigate(studentTextbookPaths.topic(topic.textbookRef, topic.topicRef, Number(event.target.value)))}>
              {topic.pages.map((item) => <option key={item.ordinal} value={item.ordinal}>{item.printedPage || item.pageNumber} ({item.ordinal} of {topic.pages.length})</option>)}
            </select></label>
            <Button variant="outline" disabled={page.ordinal === topic.pages.length} onClick={() => navigate(studentTextbookPaths.topic(topic.textbookRef, topic.topicRef, page.ordinal + 1))}>Next <ChevronRight size={17}/></Button>
          </nav>
          <div className="student-textbook-page-grid">
            <article className="panel stack" aria-label={`Reviewed content for page ${page.printedPage || page.pageNumber}`}>
              <h3>Page {page.printedPage || page.pageNumber}</h3>
              {page.sections.length ? page.sections.flatMap((section) => section.kind === 'heading'
                ? [{ kind: 'heading' as const, text: section.text }]
                : readableTextbookBlocks(section.text)).map((block, index) => block.kind === 'heading'
                  ? <h4 key={index}>{block.text}</h4>
                  : block.kind === 'list'
                    ? <ul className="student-textbook-list" key={index}>{block.items.map((item: string, itemIndex: number) => <li key={itemIndex}>{item}</li>)}</ul>
                    : <p className="student-textbook-paragraph" key={index}>{block.text}</p>)
                : <p>The reviewed text for this page is unavailable. You can still see the published page image.</p>}
              {page.visuals.map((visual) => <Visual key={visual.assetRef} visual={visual}/>)}
            </article>
            <aside className="panel stack"><h3>Textbook page image</h3><p className="small">Page {page.printedPage || page.pageNumber} from the published primary source</p>
              <Image src={page.imageUrl} alt={`Textbook page ${page.printedPage || page.pageNumber}`} width={680} height={900} unoptimized
                style={{ width: '100%', height: 'auto', objectFit: 'contain' }}/></aside>
          </div>
          {!!topic.additionalVisuals.length && <section className="panel stack"><h3>Other approved diagrams in this Topic</h3>
            <div className="student-textbook-visual-gallery">{topic.additionalVisuals.map((visual) => <Visual key={visual.assetRef} visual={visual}/>)}</div></section>}
        </> : <Empty title="No published pages">This Topic has no readable primary pages yet.</Empty>}
      </section>}
    </>}
  </>;
}
