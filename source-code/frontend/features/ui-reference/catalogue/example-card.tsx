'use client';
import { useState, type ReactNode } from 'react';
import { Button } from '@/components/ui/button';
export function ExampleCard({
  title,
  description,
  children,
  code,
  guidance,
}: {
  title: string;
  description: string;
  children: ReactNode;
  code?: string;
  guidance?: string;
}) {
  const [copied, setCopied] = useState('');
  return (
    <section className="catalogue-example">
      <header>
        <h3>{title}</h3>
        <p>{description}</p>
      </header>
      <div className="catalogue-example-body">{children}</div>
      {guidance && <p className="catalogue-guidance">{guidance}</p>}
      {code && (
        <details className="catalogue-source">
          <summary>Usage example</summary>
          <pre>
            <code>{code}</code>
          </pre>
          <Button
            variant="outline"
            size="sm"
            onClick={async () => {
              try {
                await navigator.clipboard.writeText(code);
                setCopied('Copied');
              } catch {
                setCopied('Select the code above to copy.');
              }
            }}
          >
            Copy example
          </Button>
          <output aria-live="polite">{copied}</output>
        </details>
      )}
    </section>
  );
}
