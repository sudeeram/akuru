'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, ShieldCheck } from 'lucide-react';
import { ApiError, getUiFeaturesAccess, type UiFeaturesAccess } from '@/api';
import { Button, buttonVariants } from '@/components/ui/button';
import { ComponentGallery } from '@/features/ui-reference/component-gallery';
import { UiFeaturesExperience } from '@/features/ui-reference/experience';

export default function UiFeaturesPage() {
  const [access, setAccess] = useState<UiFeaturesAccess | null>(null);
  const [status, setStatus] = useState<'loading' | 'denied' | 'error'>(
    'loading',
  );
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    getUiFeaturesAccess()
      .then((result) => {
        if (!active) return;
        if (result.allowed === true && result.user.role === 'admin')
          setAccess(result);
        else setStatus('denied');
      })
      .catch((error: unknown) => {
        if (active)
          setStatus(
            error instanceof ApiError &&
              (error.status === 401 || error.status === 403)
              ? 'denied'
              : 'error',
          );
      });
    return () => {
      active = false;
    };
  }, [retry]);
  if (!access)
    return (
      <div className="ui-reference-loading">
        <div className="ui-reference-denied">
          <ShieldCheck size={32} />
          <h1>
            {status === 'loading'
              ? 'Checking Admin access…'
              : status === 'denied'
                ? 'Admin access required'
                : 'Unable to check access'}
          </h1>
          <p>
            {status === 'denied'
              ? 'Sign in with an AKURU Admin account to view the component reference.'
              : status === 'error'
                ? 'The connection could not be completed. Please try again.'
                : 'Opening your design workspace.'}
          </p>
          {status === 'error' && (
            <Button
              onClick={() => {
                setStatus('loading');
                setRetry(retry + 1);
              }}
            >
              Try again
            </Button>
          )}
          {status !== 'loading' && (
            <Link className={buttonVariants({ variant: 'outline' })} href="/">
              <ArrowLeft /> Return to sign in
            </Link>
          )}
        </div>
      </div>
    );
  return (
    <UiFeaturesExperience userName={access.user.name}>
      <ComponentGallery />
    </UiFeaturesExperience>
  );
}
