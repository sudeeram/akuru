'use client';
import { useEffect, useId, useState, type ReactNode } from 'react';
import { ListFilter, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';

export function FilterToolbar({
  search,
  onSearch,
  placeholder = 'Search…',
  count,
  children,
  onClear,
}: {
  search: string;
  onSearch: (value: string) => void;
  placeholder?: string;
  count?: number;
  children?: ReactNode;
  onClear?: () => void;
}) {
  const id = useId();
  return (
    <div className="workspace-filters">
      <label htmlFor={id} className="workspace-search">
        <Search size={16} />
        <span className="sr-only">Search</span>
        <Input
          id={id}
          type="search"
          value={search}
          onChange={(e) => onSearch(e.target.value)}
          placeholder={placeholder}
        />
      </label>
      {children}
      {onClear && (
        <Button variant="ghost" onClick={onClear}>
          Clear filters
        </Button>
      )}
      {count !== undefined && (
        <output className="workspace-count" aria-live="polite">
          {count} result{count === 1 ? '' : 's'}
        </output>
      )}
    </div>
  );
}
export function EditorDrawer({
  open,
  onOpenChange,
  title,
  description,
  children,
  dirty = false,
  busy = false,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  children: ReactNode;
  dirty?: boolean;
  busy?: boolean;
}) {
  const change = (next: boolean) => {
    if (!next && busy) return;
    if (next || !dirty || window.confirm('Discard unsaved changes?'))
      onOpenChange(next);
  };
  useWorkspaceGuard(open && dirty, open && busy);
  return (
    <Sheet open={open} onOpenChange={change}>
      <SheetContent side="right" className="workspace-drawer">
        <SheetHeader>
          <SheetTitle>{title}</SheetTitle>
          <SheetDescription>
            {description || 'Make changes, then save when ready.'}
          </SheetDescription>
        </SheetHeader>
        <div className="workspace-drawer-body">{children}</div>
      </SheetContent>
    </Sheet>
  );
}
export function AdvancedPanel({
  title,
  children,
  open = false,
}: {
  title: string;
  children: ReactNode;
  open?: boolean;
}) {
  return (
    <details className="workspace-disclosure" open={open || undefined}>
      <summary>
        <ListFilter size={15} />
        {title}
      </summary>
      <div className="workspace-disclosure-body">{children}</div>
    </details>
  );
}
export function LoadingState({
  message = 'Loading your workspace…',
}: {
  message?: string;
}) {
  return (
    <output className="panel workspace-loading" aria-live="polite">
      <span className="workspace-spinner" aria-hidden="true" />
      {message}
    </output>
  );
}
export function ErrorState({
  message,
  retry,
}: {
  message: string;
  retry?: () => void;
}) {
  return (
    <section className="panel stack">
      <p role="alert" className="error">
        {message}
      </p>
      {retry && (
        <Button variant="outline" onClick={retry}>
          Try again
        </Button>
      )}
    </section>
  );
}
export function useWorkspaceGuard(dirty: boolean, busy = false) {
  useEffect(() => {
    if (!dirty && !busy) return;
    const unload = (event: BeforeUnloadEvent) => event.preventDefault();
    const navigate = (event: Event) => {
      if (busy || !window.confirm('Discard unsaved changes?'))
        event.preventDefault();
    };
    window.addEventListener('beforeunload', unload);
    window.addEventListener('akuru:before-navigation', navigate);
    return () => {
      window.removeEventListener('beforeunload', unload);
      window.removeEventListener('akuru:before-navigation', navigate);
    };
  }, [dirty, busy]);
}
export function useFocusMode(active: boolean) {
  useEffect(() => {
    const timer = window.setTimeout(
      () =>
        window.dispatchEvent(
          new CustomEvent('akuru:learning-focus', { detail: active }),
        ),
      0,
    );
    return () => {
      window.clearTimeout(timer);
      window.dispatchEvent(
        new CustomEvent('akuru:learning-focus', { detail: false }),
      );
    };
  }, [active]);
}
export function WorkspaceToggle({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(false);
  return (
    <section className="workspace-tool">
      <Button
        variant="outline"
        aria-expanded={open}
        onClick={() => setOpen(!open)}
      >
        {title}
      </Button>
      {open && <div className="spaced">{children}</div>}
    </section>
  );
}
