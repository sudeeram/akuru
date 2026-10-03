'use client';

import { useEffect, useRef, useState } from 'react';
import Image from 'next/image';
import { ChevronLeft, ChevronRight, Expand, Minimize, ZoomIn, ZoomOut } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { StudentTextbookReference } from '@/api';
import { flipbookSpread, nextFlipPage, previousFlipPage } from '@/lib/flipbook.mjs';

type Props = {
  reference: StudentTextbookReference;
  pageNumber: number;
  onTurn: (page: number) => void;
};

export function VisualReferenceFlipbook({ reference, pageNumber, onTurn }: Props) {
  const [wide, setWide] = useState(false);
  const [singlePage, setSinglePage] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [showPages, setShowPages] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [turnDirection, setTurnDirection] = useState<'forward' | 'backward'>('forward');
  const stageRef = useRef<HTMLElement>(null);
  const touchStart = useRef<number | null>(null);
  useEffect(() => {
    const media = window.matchMedia('(min-width: 850px)');
    const sync = () => setWide(media.matches);
    sync(); media.addEventListener('change', sync);
    return () => media.removeEventListener('change', sync);
  }, []);
  useEffect(() => {
    const sync = () => setFullscreen(document.fullscreenElement === stageRef.current);
    document.addEventListener('fullscreenchange', sync);
    return () => document.removeEventListener('fullscreenchange', sync);
  }, []);
  useEffect(() => {
    if (!expanded) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const onEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setExpanded(false);
    };
    window.addEventListener('keydown', onEscape);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener('keydown', onEscape);
    };
  }, [expanded]);
  const fullScreenActive = fullscreen || expanded;
  const toggleFullScreen = async () => {
    if (expanded) { setExpanded(false); return; }
    if (fullscreen) { await document.exitFullscreen(); return; }
    if (document.fullscreenEnabled && stageRef.current?.requestFullscreen) {
      try { await stageRef.current.requestFullscreen(); return; } catch { /* Use the in-page mobile view. */ }
    }
    setExpanded(true);
  };
  const spreadMode = wide && !singlePage;
  const shown = flipbookSpread(pageNumber, reference.pages.length, spreadMode);
  const previous = previousFlipPage(pageNumber, reference.pages.length, spreadMode);
  const next = nextFlipPage(pageNumber, reference.pages.length, spreadMode);
  const turn = (target: number) => {
    setTurnDirection(target < shown.start ? 'backward' : 'forward');
    onTurn(target);
  };
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.altKey || event.ctrlKey || event.metaKey || /INPUT|SELECT|TEXTAREA/.test((event.target as HTMLElement)?.tagName || '')) return;
      const target = event.key === 'ArrowRight' ? next : event.key === 'ArrowLeft' ? previous
        : event.key === 'Home' ? 1 : event.key === 'End' ? reference.pages.length : null;
      if (target !== null) { event.preventDefault(); turn(target); }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  });
  const sheet = (ordinal: number | null, side: string) => {
    const page = ordinal ? reference.pages[ordinal - 1] : null;
    return <div className={`flipbook-sheet flipbook-sheet-${side}${page ? '' : ' flipbook-sheet-blank'}`}>
      {page && <><Image src={page.imageUrl} alt={`Page ${page.printedPage} of ${reference.filename}`}
        width={1000} height={1400} unoptimized priority={page.ordinal === shown.start}
        style={{ width: '100%', height: 'auto', maxHeight: '100%', objectFit: 'contain' }}/>
        <span className="flipbook-sheet-label">Page {page.printedPage}</span></>}
    </div>;
  };
  const shownPages = [shown.left, shown.right].filter((value): value is number => value !== null);
  return <section className={`flipbook stack${expanded ? ' flipbook-expanded' : ''}`} ref={stageRef} aria-label={`Visual reference flipbook: ${reference.filename}`}>
    <div className="flipbook-toolbar" role="toolbar" aria-label="Flipbook controls">
      <Button variant="outline" disabled={previous === null} onClick={() => previous !== null && turn(previous)}><ChevronLeft size={17}/> Previous</Button>
      <span className="flipbook-position" aria-live="polite">{shownPages.map((ordinal) => reference.pages[ordinal - 1]?.printedPage).join('–')} · {shown.start} of {reference.pages.length}</span>
      <Button variant="outline" disabled={next === null} onClick={() => next !== null && turn(next)}>Next <ChevronRight size={17}/></Button>
      <label className="flipbook-jump">Page <select aria-label="Go to visual reference page" value={pageNumber}
        onChange={(event) => turn(Number(event.target.value))}>
        {reference.pages.map((page) => <option key={page.ordinal} value={page.ordinal}>{page.printedPage}</option>)}
      </select></label>
      {wide && <Button variant="outline" aria-pressed={singlePage} onClick={() => setSinglePage((value) => !value)}>{singlePage ? 'Two pages' : 'One page'}</Button>}
      <Button variant="outline" aria-label="Zoom out" disabled={zoom <= 1} onClick={() => setZoom((value) => Math.max(1, value - 0.25))}><ZoomOut size={17}/></Button>
      <span className="small" aria-live="polite">{Math.round(zoom * 100)}%</span>
      <Button variant="outline" aria-label="Zoom in" disabled={zoom >= 2} onClick={() => setZoom((value) => Math.min(2, value + 0.25))}><ZoomIn size={17}/></Button>
      <Button variant="outline" aria-pressed={fullScreenActive} onClick={() => { void toggleFullScreen(); }}>
        {fullScreenActive ? <Minimize size={17}/> : <Expand size={17}/>} {fullScreenActive ? 'Exit full screen' : 'Full screen'}
      </Button>
      <Button variant="outline" aria-pressed={showPages} onClick={() => setShowPages((value) => !value)}>{showPages ? 'Hide pages' : 'Browse pages'}</Button>
    </div>
    <div className="flipbook-stage" onPointerDown={(event) => {
      if (event.pointerType === 'touch' && zoom === 1) touchStart.current = event.clientX;
    }} onPointerUp={(event) => {
      if (touchStart.current === null || event.pointerType !== 'touch') return;
      const distance = event.clientX - touchStart.current; touchStart.current = null;
      if (distance < -60 && next !== null) turn(next);
      if (distance > 60 && previous !== null) turn(previous);
    }}>
      <div className="flipbook-scroll">
        <div className={`flipbook-spread${spreadMode ? ' flipbook-spread-double' : ''} flipbook-turn-${turnDirection}`}
          key={`${reference.ordinal}-${shown.start}-${spreadMode}`} style={{ width: `${zoom * 100}%`, maxWidth: zoom === 1 && spreadMode ? '1400px' : 'none' }}>
          {sheet(shown.left, 'left')}
          {spreadMode && sheet(shown.right, 'right')}
        </div>
      </div>
    </div>
    {showPages && <div className="flipbook-pages" aria-label="Browse visual reference pages">
      {reference.pages.map((page) => <button type="button" key={page.ordinal}
        className={`flipbook-page-tile${shownPages.includes(page.ordinal) ? ' active' : ''}`}
        aria-label={`Go to page ${page.printedPage}`} aria-current={shownPages.includes(page.ordinal) ? 'page' : undefined}
        onClick={() => turn(page.ordinal)}>
        <Image src={page.thumbnailUrl} alt="" width={100} height={136} unoptimized loading="lazy"/>
        <span>{page.printedPage}</span>
      </button>)}
    </div>}
    <p className="small">Use the arrows or swipe to turn pages. On a larger screen, the first page opens like a book cover.</p>
  </section>;
}
