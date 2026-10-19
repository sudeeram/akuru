'use client';
import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Spinner } from '@/components/ui/spinner';
export function TimedDemo() {
  const [busy, setBusy] = useState(false),
    [done, setDone] = useState(false);
  useEffect(() => {
    if (!busy) return;
    const timer = setTimeout(() => {
      setBusy(false);
      setDone(true);
    }, 1200);
    return () => clearTimeout(timer);
  }, [busy]);
  return (
    <div className="catalogue-row">
      <Button
        disabled={busy}
        onClick={() => {
          setDone(false);
          setBusy(true);
        }}
      >
        {busy && <Spinner aria-hidden="true" />}
        {busy ? 'Processing sample…' : 'Run sample action'}
      </Button>
      <output aria-live="polite">
        {done ? 'Sample complete. No changes saved.' : ''}
      </output>
    </div>
  );
}
