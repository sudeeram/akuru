'use client';
import { createElement, useState, type ReactNode } from 'react';
import Image from 'next/image';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';

// Native MathML for common textbook notation. Unsupported commands stay visible as source.
const symbols: Record<string,string> = { times:'×', cdot:'·', div:'÷', pm:'±', leq:'≤', geq:'≥', neq:'≠', pi:'π', theta:'θ', alpha:'α', beta:'β', delta:'δ', Delta:'Δ', sigma:'σ', mu:'μ', infty:'∞', degree:'°' };
export function Equation({ value }: { value: string }) {
  let cursor = 0;
  const source = value.replace(/^\$+|\$+$/g,'');
  const node = (tag: string, children: ReactNode[]) => createElement(tag, {}, ...children);
  function group(): ReactNode {
    if (source[cursor] === '{') { cursor++; const result = sequence('}'); if (source[cursor] !== '}') throw Error('Unclosed group'); cursor++; return result; }
    return atom();
  }
  function atom(): ReactNode {
    const char = source[cursor++];
    if (!char) throw Error('Incomplete expression');
    if (char === '\\') {
      const command = source.slice(cursor).match(/^[a-zA-Z]+/)?.[0];
      if (!command) throw Error('Unsupported escape');
      cursor += command.length;
      if (command === 'frac') return node('mfrac',[group(),group()]);
      if (command === 'sqrt') return node('msqrt',[group()]);
      if (command === 'text' || command === 'mathrm') {
        if (source[cursor++] !== '{') throw Error('Missing text');
        const end=source.indexOf('}',cursor); if(end<0) throw Error('Unclosed text');
        const text=source.slice(cursor,end);cursor=end+1;return node('mtext',[text]);
      }
      if (symbols[command]) return node('mo',[symbols[command]]);
      throw Error('Unsupported notation');
    }
    return node(/[0-9.]/.test(char) ? 'mn' : /[a-zA-Z]/.test(char) ? 'mi' : 'mo',[char]);
  }
  function sequence(stop=''): ReactNode {
    const children: ReactNode[]=[];
    while(cursor<source.length && (!stop || source[cursor]!==stop)) {
      if (/\s/.test(source[cursor])) {cursor++;continue;}
      let current=source[cursor]==='{' ? group() : atom();
      while(source[cursor]==='^' || source[cursor]==='_') {const op=source[cursor++];current=node(op==='^'?'msup':'msub',[current,group()]);}
      children.push(current);
    }
    return node('mrow',children);
  }
  let rendered: ReactNode;
  try { rendered=createElement('math', {display:'block'}, sequence()); }
  catch { rendered=<><p className="small">This notation is shown in its original form; consult the source diagram if needed.</p><code>{value}</code></>; }
  return <figure className="equation">{rendered}<figcaption className="small">Equation source: {value}</figcaption></figure>;
}

export function LearningImage({ src, description, title = 'Learning diagram' }: { src: string; description: string; title?: string }) {
  const [open,setOpen]=useState(false);
  const [failed,setFailed]=useState(false);
  const [retry,setRetry]=useState(0);
  return <figure className="learning-image">
    <Image key={retry} src={src} unoptimized width={800} height={600} className="assessment-asset" alt={description} onError={() => setFailed(true)} />
    <figcaption className="small">{description}</figcaption>
    {failed ? <div role="alert">Diagram could not load. <Button variant="outline" onClick={() => {setFailed(false);setRetry(retry+1);}}>Retry image</Button></div> : <Button variant="outline" onClick={() => setOpen(true)}>Enlarge diagram</Button>}
    <Dialog open={open} onOpenChange={setOpen}><DialogContent className="wide-dialog"><DialogHeader><DialogTitle>{title}</DialogTitle><DialogDescription>{description}</DialogDescription></DialogHeader><section className="learning-image-zoom" aria-label="Scrollable enlarged diagram"><Image src={src} unoptimized width={1600} height={1200} style={{maxWidth:'none',width:'100%',height:'auto'}} alt={description} /></section><a href={src} target="_blank" rel="noreferrer">Open original size in a new tab</a></DialogContent></Dialog>
  </figure>;
}
