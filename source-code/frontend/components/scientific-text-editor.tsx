'use client';

import { useRef } from 'react';
import type { ReactNode } from 'react';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import type { ScientificTextContent, ScientificTextMark } from '@/api';

const SUB = '₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎';
const SUPER = '⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾';
const ASCII = '0123456789+-=()';
export function scientificPlainText(value: string) {
  return [...value].map((character) => {
    const sub = SUB.indexOf(character), sup = SUPER.indexOf(character);
    return sub >= 0 ? ASCII[sub] : sup >= 0 ? ASCII[sup] : character;
  }).join('');
}

function formattedRuns(content: ScientificTextContent) {
  const boundaries = new Set([0, content.text.length]);
  content.marks.forEach((mark) => { boundaries.add(mark.start); boundaries.add(mark.end); });
  const points = [...boundaries].sort((a, b) => a - b);
  return points.slice(0, -1).map((start, index) => {
    const end = points[index + 1];
    return { start, text: content.text.slice(start, end), marks: content.marks.filter((mark) => mark.start <= start && mark.end >= end).map((mark) => mark.type) };
  });
}

export function ScientificTextEditor({ id, content, proposal, onChange }: {
  id: string;
  content: ScientificTextContent;
  proposal?: { marks?: Array<{ type: string; start: number; end: number; confidence: number }>; ambiguousTokens?: string[] };
  onChange: (value: ScientificTextContent) => void;
}) {
  const input = useRef<HTMLTextAreaElement>(null);
  const undoHistory = useRef<ScientificTextContent[]>([]);
  const redoHistory = useRef<ScientificTextContent[]>([]);
  const commit = (value: ScientificTextContent) => {
    undoHistory.current.push(content);
    redoHistory.current = [];
    onChange(value);
  };
  const updateText = (text: string) => commit({ version: 1, text, plainText: scientificPlainText(text), marks: [] });
  const undo = () => {
    const prior = undoHistory.current.pop();
    if (!prior) return;
    redoHistory.current.push(content);
    onChange(prior);
  };
  const redo = () => {
    const next = redoHistory.current.pop();
    if (!next) return;
    undoHistory.current.push(content);
    onChange(next);
  };
  const apply = (type: ScientificTextMark['type']) => {
    const start = input.current?.selectionStart ?? 0, end = input.current?.selectionEnd ?? 0;
    if (start === end) return;
    const retained = content.marks.filter((mark) => mark.end <= start || mark.start >= end || mark.type !== type);
    const already = retained.length !== content.marks.length;
    let text = content.text;
    if (!already && (type === 'subscript' || type === 'superscript')) {
      const target = type === 'subscript' ? SUB : SUPER;
      const selection = [...text.slice(start, end)].map((character) => {
        const index = ASCII.indexOf(character); return index >= 0 ? target[index] : character;
      }).join('');
      text = text.slice(0, start) + selection + text.slice(end);
    }
    commit({ ...content, text, plainText: scientificPlainText(text), marks: already ? retained : [...content.marks, { type, start, end }] });
    queueMicrotask(() => { input.current?.focus(); input.current?.setSelectionRange(start, end); });
  };
  const insert = (symbol: string) => {
    const start = input.current?.selectionStart ?? content.text.length, end = input.current?.selectionEnd ?? start;
    const next = content.text.slice(0, start) + symbol + content.text.slice(end);
    updateText(next); queueMicrotask(() => { input.current?.focus(); input.current?.setSelectionRange(start + symbol.length, start + symbol.length); });
  };
  return <div className="scientific-editor stack">
    <label className="stack" htmlFor={id}>Extracted text</label>
    {proposal && <p className="source-note" role="status"><strong>Scientific notation needs confirmation.</strong>{' '}
      AKURU found {proposal.marks?.length || 0} possible formatting mark{proposal.marks?.length === 1 ? '' : 's'}.
      {!!proposal.ambiguousTokens?.length && <> Check ambiguous text: {proposal.ambiguousTokens.join(', ')}.</>}
    </p>}
    <div className="scientific-toolbar" role="toolbar" aria-label="Scientific text formatting">
      <Button type="button" variant="outline" aria-label="Apply subscript" onClick={() => apply('subscript')}>X<sub>2</sub></Button>
      <Button type="button" variant="outline" aria-label="Apply superscript" onClick={() => apply('superscript')}>X<sup>2</sup></Button>
      <Button type="button" variant="outline" onClick={() => apply('bold')}>Bold</Button>
      <Button type="button" variant="outline" onClick={() => apply('italic')}>Italic</Button>
      <Button type="button" variant="outline" aria-label="Undo scientific text edit" onClick={undo}>Undo</Button>
      <Button type="button" variant="outline" aria-label="Redo scientific text edit" onClick={redo}>Redo</Button>
      {['→', '⇌', '°', '±', 'Δ', 'α', 'β'].map((symbol) => <Button type="button" variant="outline" aria-label={`Insert ${symbol}`} key={symbol} onClick={() => insert(symbol)}>{symbol}</Button>)}
      <Button type="button" variant="outline" onClick={() => commit({ ...content, marks: [] })}>Clear formatting</Button>
    </div>
    <Textarea ref={input} id={id} value={content.text} onChange={(event) => updateText(event.target.value)} onKeyDown={(event) => {
      if (!(event.ctrlKey || event.metaKey)) return;
      if (event.key === ',') { event.preventDefault(); apply('subscript'); }
      if (event.key === '.') { event.preventDefault(); apply('superscript'); }
    }}/>
    <div className="scientific-preview" aria-label="Student display preview"><strong>Student display preview</strong><p>{formattedRuns(content).map((run) => {
      let node: ReactNode = run.text;
      if (run.marks.includes('subscript')) node = <sub>{node}</sub>;
      if (run.marks.includes('superscript')) node = <sup>{node}</sup>;
      if (run.marks.includes('bold')) node = <strong>{node}</strong>;
      if (run.marks.includes('italic')) node = <em>{node}</em>;
      return <span key={`${run.start}-${run.text}`}>{node}</span>;
    })}</p><small>Search alias: {content.plainText}</small></div>
  </div>;
}
