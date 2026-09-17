'use client';
import { useEffect, useState } from 'react';
import { Eye } from 'lucide-react';
import { getTutorSignals, type TutorSignal } from '@/lib/api';

export function TutorSignals({ studentId, refreshKey }: { studentId?: string; refreshKey?: string }) {
  const [signals, setSignals] = useState<TutorSignal[]>([]);
  useEffect(() => { void getTutorSignals(studentId).then((result) => setSignals(result.signals)).catch(() => setSignals([])); }, [studentId, refreshKey]);
  if (!signals.length) return null;
  return <section className="tutor-observations stack" aria-label="Tutor observations"><div className="panel-heading"><div><span className="pill"><Eye size={13} /> NON-AUTHORITATIVE</span><h3>Tutor observations</h3></div></div>{signals.slice(0, 6).map((signal) => <div className="source-note" key={signal.signalRef}><strong>{signal.topicCode} · {signal.topicTitle} · {signal.category.replaceAll('_', ' ')}</strong><p>{signal.observation}</p><small>{Math.round(signal.confidence * 100)}% confidence · {signal.evidenceCount} supporting reference{signal.evidenceCount === 1 ? '' : 's'} · does not change mastery or study plans</small></div>)}</section>;
}
