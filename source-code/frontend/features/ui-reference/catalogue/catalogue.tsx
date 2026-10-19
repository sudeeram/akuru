'use client';
import { lazy, Suspense, useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  catalogueEntries,
  catalogueFromHash,
  findEntries,
  type CatalogueId,
} from './registry';
import { ExampleCard } from './example-card';
import './catalogue.css';
const Foundations = lazy(() => import('./examples/foundations'));
const Interactions = lazy(() => import('./examples/interactions'));
const Workspace = lazy(() => import('./examples/workspace'));
const Attendance = lazy(() => import('./examples/attendance'));
const interactiveIds = [
  'alerts',
  'accordion',
  'collapse',
  'dropdowns',
  'modals',
  'offcanvas',
  'popovers',
  'tooltips',
  'nav-tabs',
  'carousel',
];
const usage: Partial<Record<CatalogueId, string>> = {
  alerts: `import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';\n<Alert><AlertTitle>Ready for review</AlertTitle><AlertDescription>Check the supporting material.</AlertDescription></Alert>`,
  accordion: `import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from '@/components/ui/accordion';\n<Accordion defaultValue={['help']}><AccordionItem value="help"><AccordionTrigger>Instructions</AccordionTrigger><AccordionContent>Read carefully.</AccordionContent></AccordionItem></Accordion>`,
  avatar: `import { StudentAvatar } from '@/components/portal/student-avatar';\nimport { avatarPresets } from '@/lib/student-avatar';\n<StudentAvatar avatar={avatarPresets[0]} fallback="MS" label="Maya Sample" />`,
  badges: `import { StatusBadge, MetadataBadge, CountBadge } from '@/components/portal/badges';\n<StatusBadge status="Ready" />\n<MetadataBadge>iGCSE Science</MetadataBadge>\n<CountBadge count={142} label="notifications" />`,
  buttons: `import { Button } from '@/components/ui/button';\n<Button variant="outline" size="sm" onClick={onPreview}>Preview</Button>`,
  'buttons-group': `import { ButtonGroup } from '@/components/ui/button-group';\nimport { Button } from '@/components/ui/button';\n<ButtonGroup aria-label="Period"><Button aria-pressed={period === 'week'} onClick={() => setPeriod('week')}>Week</Button></ButtonGroup>`,
  cards: `import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';\n<Card><CardHeader><CardTitle>Course overview</CardTitle></CardHeader><CardContent>Learning resources</CardContent></Card>`,
  collapse: `import { Collapsible, CollapsibleTrigger, CollapsibleContent } from '@/components/ui/collapsible';\n<Collapsible><CollapsibleTrigger>Guidance</CollapsibleTrigger><CollapsibleContent>Supporting information</CollapsibleContent></Collapsible>`,
  dropdowns: `import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from '@/components/ui/dropdown-menu';\n<DropdownMenu><DropdownMenuTrigger>Actions</DropdownMenuTrigger><DropdownMenuContent><DropdownMenuItem onClick={onPreview}>Preview</DropdownMenuItem></DropdownMenuContent></DropdownMenu>`,
  grid: `<div className="grid gap-4 md:grid-cols-2"><section>Primary content</section><aside>Supporting content</aside></div>`,
  images: `<figure><img src="/favicon.svg" width="112" height="112" alt="AKURU application icon" /><figcaption>AKURU</figcaption></figure>`,
  links: `<a href="#ui-catalog-workspace">Explore the workspace</a>`,
  'list-group': `<ul><li><a href="#ui-catalog-workspace">Science resources</a></li><li>Supporting information</li></ul>`,
  progress: `import { Progress, ProgressLabel, ProgressValue } from '@/components/ui/progress';\n<Progress value={40}><ProgressLabel>Study completion</ProgressLabel><ProgressValue /></Progress>`,
  placeholders: `import { Skeleton } from '@/components/ui/skeleton';\n<div aria-busy="true" aria-label="Loading resources"><Skeleton className="h-5 w-3/4" /></div>`,
  spinner: `import { Spinner } from '@/components/ui/spinner';\n<Spinner aria-label="Loading resources" />`,
  typography: `<section><h2>Learning overview</h2><p>Readable supporting information.</p><dl><dt>Course</dt><dd>iGCSE Science</dd></dl></section>`,
  breadcrumb: `import { Breadcrumb, BreadcrumbList, BreadcrumbItem, BreadcrumbLink, BreadcrumbSeparator, BreadcrumbPage } from '@/components/ui/breadcrumb';\n<Breadcrumb><BreadcrumbList><BreadcrumbItem><BreadcrumbLink href="#ui-catalog-workspace">Workspace</BreadcrumbLink></BreadcrumbItem><BreadcrumbSeparator/><BreadcrumbItem><BreadcrumbPage>Review</BreadcrumbPage></BreadcrumbItem></BreadcrumbList></Breadcrumb>`,
  'nav-tabs': `import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';\n<Tabs defaultValue="overview"><TabsList><TabsTrigger value="overview">Overview</TabsTrigger></TabsList><TabsContent value="overview">Sample overview</TabsContent></Tabs>`,
  modals: `import { Dialog, DialogTrigger, DialogContent, DialogTitle, DialogDescription } from '@/components/ui/dialog';\n<Dialog><DialogTrigger>Preview</DialogTrigger><DialogContent><DialogTitle>Sample preview</DialogTitle><DialogDescription>No changes are saved.</DialogDescription></DialogContent></Dialog>`,
  offcanvas: `import { Sheet, SheetTrigger, SheetContent, SheetTitle, SheetDescription } from '@/components/ui/sheet';\n<Sheet><SheetTrigger>Details</SheetTrigger><SheetContent side="right"><SheetTitle>Resource</SheetTitle><SheetDescription>Supporting information</SheetDescription></SheetContent></Sheet>`,
  popovers: `import { Popover, PopoverTrigger, PopoverContent, PopoverTitle, PopoverDescription } from '@/components/ui/popover';\n<Popover><PopoverTrigger>Help</PopoverTrigger><PopoverContent><PopoverTitle>Review evidence</PopoverTitle><PopoverDescription>Check the source.</PopoverDescription></PopoverContent></Popover>`,
  tooltips: `import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip';\n<Tooltip><TooltipTrigger>Review help</TooltipTrigger><TooltipContent>Check supporting evidence</TooltipContent></Tooltip>`,
  carousel: `import { Carousel, CarouselContent, CarouselItem, CarouselPrevious, CarouselNext } from '@/components/ui/carousel';\n<Carousel><CarouselContent><CarouselItem>First resource</CarouselItem><CarouselItem>Second resource</CarouselItem></CarouselContent><CarouselPrevious/><CarouselNext/></Carousel>`,
  pagination: `import { Pagination, PaginationContent, PaginationItem, PaginationLink } from '@/components/ui/pagination';\n<Pagination><PaginationContent><PaginationItem><PaginationLink href="?page=1" isActive>1</PaginationLink></PaginationItem></PaginationContent></Pagination>`,
  workspace: `import { FilterToolbar } from '@/components/portal/workspace';\n<FilterToolbar search={search} onSearch={setSearch} count={rows.length} onClear={clearFilters} />\n// Compose with Table, StatusBadge and EditorDrawer; data belongs to the caller.`,
  attendance: `// Sample-only composition; not a live attendance service.\nimport { attendanceSummary } from '@/features/ui-reference/catalogue/models';\nconst summary = attendanceSummary(['Present', 'Late', null, 'Absent']);\n// summary.rate = 67; present-or-late / marked learners.`,
};
export function ComponentCatalogue() {
  const [selected, setSelected] = useState<CatalogueId>('alerts'),
    [query, setQuery] = useState(''),
    [revision, setRevision] = useState(0);
  useEffect(() => {
    const restore = () => {
      const id = catalogueFromHash(window.location.hash);
      if (id) {
        setSelected(id);
        setQuery('');
        document
          .getElementById('ui-catalogue')
          ?.scrollIntoView({ block: 'start' });
      }
    };
    restore();
    window.addEventListener('hashchange', restore);
    return () => window.removeEventListener('hashchange', restore);
  }, []);
  const results = findEntries(query),
    entry = catalogueEntries.find((e) => e.id === selected)!;
  const select = (id: CatalogueId) => {
    setSelected(id);
    setRevision(0);
    window.history.pushState(window.history.state, '', `#ui-catalog-${id}`);
    window.dispatchEvent(new HashChangeEvent('hashchange'));
  };
  return (
    <section id="ui-catalogue" className="ak-section catalogue">
      <header className="catalogue-heading">
        <div>
          <p className="catalogue-eyebrow">AKURU design system</p>
          <h2>Component catalogue</h2>
          <p>
            27 reusable component families. Explore a pattern, try it, then
            reuse it.
          </p>
        </div>
        <span className="catalogue-label">Local sample data</span>
      </header>
      <div className="catalogue-layout">
        <aside className="catalogue-index" aria-label="Component index">
          <label htmlFor="catalogue-search">Find a component</label>
          <Input
            id="catalogue-search"
            type="search"
            placeholder="Try cards, loading, filters…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <div className="catalogue-row">
            <output aria-live="polite">{results.length} families</output>
            {query && (
              <Button variant="ghost" size="sm" onClick={() => setQuery('')}>
                Clear search
              </Button>
            )}
          </div>
          <label className="catalogue-mobile-picker" htmlFor="catalogue-family">
            Component family
            <select
              id="catalogue-family"
              value={selected}
              onChange={(e) => select(e.target.value as CatalogueId)}
            >
              {!results.some((e) => e.id === selected) && (
                <option value={selected}>{entry.title}</option>
              )}
              {results.map((e) => (
                <option value={e.id} key={e.id}>
                  {e.title}
                </option>
              ))}
            </select>
          </label>
          <nav aria-label="Component families">
            {Array.from(new Set(catalogueEntries.map((e) => e.group))).map(
              (group) => {
                const items = results.filter((e) => e.group === group);
                return items.length ? (
                  <div key={group}>
                    <h3>{group}</h3>
                    {items.map((e) => (
                      <a
                        href={`#ui-catalog-${e.id}`}
                        key={e.id}
                        aria-current={selected === e.id ? 'true' : undefined}
                        onClick={(event) => {
                          event.preventDefault();
                          select(e.id);
                        }}
                      >
                        {e.title}
                      </a>
                    ))}
                  </div>
                ) : null;
              },
            )}
          </nav>
        </aside>
        <div className="catalogue-content">
          {results.length === 0 ? (
            <div className="catalogue-empty">
              <h3>No matching components</h3>
              <p>Try a shorter term such as “loading” or “card”.</p>
              <Button onClick={() => setQuery('')}>Reset search</Button>
            </div>
          ) : (
            <>
              <div className="catalogue-row catalogue-family-heading">
                <h3>{entry.title}</h3>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setRevision(revision + 1)}
                >
                  Reset example
                </Button>
              </div>
              <p>
                <span className="catalogue-label">
                  {['workspace', 'attendance'].includes(entry.id)
                    ? 'Composed pattern'
                    : 'Reusable component'}
                </span>
              </p>
              <ExampleCard
                title={`${entry.title} · AKURU examples`}
                description={entry.description}
                code={usage[entry.id]}
                guidance="Enabled controls affect this sample only. Decorative finishes are visual specimens; use the standard AKURU variants for product status and primary actions."
              >
                <Suspense
                  fallback={<output>Loading component preview…</output>}
                >
                  <div key={`${selected}-${revision}`}>
                    {entry.id === 'workspace' ? (
                      <Workspace />
                    ) : entry.id === 'attendance' ? (
                      <Attendance />
                    ) : interactiveIds.includes(entry.id) ? (
                      <Interactions id={entry.id} />
                    ) : (
                      <Foundations id={entry.id} />
                    )}
                  </div>
                </Suspense>
              </ExampleCard>
              <p className="catalogue-reference">
                <a
                  href={`https://preskool.dreamstechnologies.com/html/ui-${entry.id}.html`}
                  target="_blank"
                  rel="noreferrer"
                >
                  View design reference (opens new tab)
                </a>{' '}
                · Adapted with AKURU components and original artwork
              </p>
            </>
          )}
        </div>
      </div>
    </section>
  );
}
