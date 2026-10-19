'use client';
// These fixed-size local SVG specimens do not need image optimization.
/* oxlint-disable next/no-img-element */
import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Info, CheckCircle2, TriangleAlert, XCircle } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from '@/components/ui/accordion';
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from '@/components/ui/collapsible';
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from '@/components/ui/dialog';
import {
  Sheet,
  SheetTrigger,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetClose,
} from '@/components/ui/sheet';
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuCheckboxItem,
} from '@/components/ui/dropdown-menu';
import {
  Popover,
  PopoverTrigger,
  PopoverContent,
  PopoverTitle,
  PopoverDescription,
} from '@/components/ui/popover';
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
  TooltipProvider,
} from '@/components/ui/tooltip';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselPrevious,
  CarouselNext,
  type CarouselApi,
} from '@/components/ui/carousel';
import { CountBadge } from '@/components/portal/badges';
import type { CatalogueId } from '../registry';
export default function Interactions({ id }: { id: CatalogueId }) {
  const [notice, setNotice] = useState(''),
    [show, setShow] = useState(true),
    [second, setSecond] = useState(false),
    [side, setSide] = useState<'left' | 'right' | 'top' | 'bottom'>('right'),
    [size, setSize] = useState('default'),
    [label, setLabel] = useState(''),
    [error, setError] = useState(''),
    [open, setOpen] = useState(false),
    [step, setStep] = useState(1);
  switch (id) {
    case 'alerts':
      return (
        <div className="catalogue-stack">
          <div className="catalogue-row">
            <Button
              onClick={() => setNotice('Sample document is ready to review.')}
            >
              Show live alert
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setShow(true);
                setNotice('');
              }}
            >
              Restore alerts
            </Button>
          </div>
          {notice && (
            <output aria-live="polite">
              <Alert role="none">
                <AlertTitle>Sample update</AlertTitle>
                <AlertDescription>{notice}</AlertDescription>
                <Button
                  variant="ghost"
                  size="sm"
                  aria-label="Dismiss sample update"
                  onClick={() => setNotice('')}
                >
                  Close
                </Button>
              </Alert>
            </output>
          )}
          {show && (
            <Alert role="none">
              <AlertTitle>Review required</AlertTitle>
              <AlertDescription>
                Some sample questions need a second look.{' '}
                <a href="#ui-catalog-workspace">Explore the workspace</a>
              </AlertDescription>
              <Button variant="ghost" size="sm" onClick={() => setShow(false)}>
                Dismiss review notice
              </Button>
            </Alert>
          )}
          {['Information', 'Success', 'Warning', 'Error'].map((tone, i) => (
            <div className={`catalogue-alert tone-${i}`} key={tone}>
              <strong className="catalogue-row">
                {[Info, CheckCircle2, TriangleAlert, XCircle].map((Icon, n) =>
                  n === i ? (
                    <Icon key={n} size={18} aria-hidden="true" />
                  ) : null,
                )}
                {tone}
              </strong>
              <p>
                {
                  [
                    'Your sample resources are available.',
                    'Sample document ready.',
                    'Check the supporting evidence.',
                    'Sample request could not finish.',
                  ][i]
                }
              </p>
              {i === 3 && (
                <Button
                  variant="outline"
                  onClick={() => setNotice('Sample retry completed.')}
                >
                  Retry sample
                </Button>
              )}
            </div>
          ))}
        </div>
      );
    case 'accordion':
      return (
        <div className="catalogue-stack">
          {[
            'Bordered FAQ',
            'Flush sections',
            'Multiple open',
            'Arrowless specimen',
          ].map((style, n) => (
            <section key={style}>
              <h4>{style}</h4>
              <Accordion
                multiple={n === 2}
                defaultValue={['instructions']}
                className={
                  n === 0
                    ? 'catalogue-tile'
                    : n === 3
                      ? 'catalogue-arrowless'
                      : ''
                }
              >
                <AccordionItem value="instructions">
                  <AccordionTrigger>
                    How do I start a practice exam?
                  </AccordionTrigger>
                  <AccordionContent>
                    Read the instructions, check the time available and begin
                    when ready.
                  </AccordionContent>
                </AccordionItem>
                <AccordionItem value="review">
                  <AccordionTrigger>
                    What happens after submission?
                  </AccordionTrigger>
                  <AccordionContent>
                    Review the sample feedback and revisit your learning
                    resources.
                  </AccordionContent>
                </AccordionItem>
                <AccordionItem value="locked" disabled>
                  <AccordionTrigger>Unavailable example</AccordionTrigger>
                  <AccordionContent>This section is locked.</AccordionContent>
                </AccordionItem>
              </Accordion>
            </section>
          ))}
        </div>
      );
    case 'collapse':
      return (
        <div className="catalogue-stack">
          <Collapsible open={show} onOpenChange={setShow}>
            <CollapsibleTrigger render={<Button variant="outline" />}>
              Toggle guidance
            </CollapsibleTrigger>
            <CollapsibleContent>
              <div className="catalogue-tile">
                Supporting guidance stays out of the way until needed.
              </div>
            </CollapsibleContent>
          </Collapsible>
          <Collapsible open={second} onOpenChange={setSecond}>
            <CollapsibleTrigger render={<Button variant="outline" />}>
              Toggle secondary tools
            </CollapsibleTrigger>
            <CollapsibleContent>
              <div className="catalogue-tile">
                Additional local tools · horizontal layout on wide screens.
              </div>
            </CollapsibleContent>
          </Collapsible>
          <Button
            onClick={() => {
              const next = !(show && second);
              setShow(next);
              setSecond(next);
            }}
            aria-expanded={show && second}
          >
            Toggle both regions
          </Button>
        </div>
      );
    case 'dropdowns':
      return (
        <div className="catalogue-stack">
          <div className="catalogue-row">
            {(['bottom', 'top', 'left', 'right'] as const).map((position) => (
              <DropdownMenu key={position}>
                <DropdownMenuTrigger render={<Button variant="outline" />}>
                  {position} actions ▾
                </DropdownMenuTrigger>
                <DropdownMenuContent side={position}>
                  <DropdownMenuItem
                    onClick={() => setNotice('Sample details selected')}
                  >
                    Preview details
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => setNotice('Sample link selected')}
                  >
                    Preview link
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuCheckboxItem
                    checked={show}
                    onCheckedChange={setShow}
                  >
                    Show metadata
                  </DropdownMenuCheckboxItem>
                  <DropdownMenuItem disabled>
                    Unavailable action
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ))}
          </div>
          <div className="catalogue-row">
            <Button
              onClick={() => setNotice('Primary sample action completed')}
            >
              Primary action
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger
                render={
                  <Button variant="outline" aria-label="More sample actions" />
                }
              >
                ▾
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem
                  onClick={() => setNotice('Alternative action selected')}
                >
                  Alternative action
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
          <output aria-live="polite">
            {notice} {show ? 'Metadata shown.' : 'Metadata hidden.'}
          </output>
          <p>
            Use a popover for forms. Menus provide actions and choices with
            predictable dismissal.
          </p>
        </div>
      );
    case 'modals':
      return (
        <div className="catalogue-stack">
          <label>
            Dialog size{' '}
            <select value={size} onChange={(e) => setSize(e.target.value)}>
              {['small', 'default', 'large', 'fullscreen'].map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </label>
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger render={<Button />}>
              Open sample editor
            </DialogTrigger>
            <DialogContent className={`catalogue-dialog ${size}`}>
              <DialogHeader>
                <DialogTitle>
                  {step === 1 ? 'Edit sample title' : 'Confirm sample preview'}
                </DialogTitle>
                <DialogDescription>
                  Demo only. No account or document is changed.
                </DialogDescription>
              </DialogHeader>
              {step === 1 ? (
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    if (!label.trim()) {
                      setError('Enter a sample title.');
                      return;
                    }
                    setError('');
                    setStep(2);
                  }}
                  className="catalogue-stack"
                >
                  <label htmlFor="catalogue-title">
                    Sample title
                    <Input
                      id="catalogue-title"
                      value={label}
                      onChange={(e) => setLabel(e.target.value)}
                      aria-invalid={!!error}
                      aria-describedby={
                        error ? 'catalogue-title-error' : undefined
                      }
                    />
                  </label>
                  {error && (
                    <p id="catalogue-title-error" role="alert">
                      {error}
                    </p>
                  )}
                  <details>
                    <summary>Review guidance</summary>
                    <p>Keep titles short and descriptive.</p>
                  </details>
                  <Button type="submit">Continue</Button>
                </form>
              ) : (
                <>
                  <p>Preview title: {label}</p>
                  <Button
                    onClick={() => {
                      setNotice(`Sample title previewed: ${label}`);
                      setOpen(false);
                      setStep(1);
                    }}
                  >
                    Confirm preview
                  </Button>
                  <Button variant="outline" onClick={() => setStep(1)}>
                    Back
                  </Button>
                </>
              )}
              <DialogFooter>
                <DialogClose render={<Button variant="outline" />}>
                  Close
                </DialogClose>
              </DialogFooter>
            </DialogContent>
          </Dialog>
          <Dialog>
            <DialogTrigger render={<Button variant="outline" />}>
              Long content modal
            </DialogTrigger>
            <DialogContent className="catalogue-dialog">
              <DialogHeader>
                <DialogTitle>Sample exam guidance</DialogTitle>
                <DialogDescription>
                  Scrollable content within the dialog.
                </DialogDescription>
              </DialogHeader>
              <div className="catalogue-dialog-scroll">
                {Array.from({ length: 12 }, (_, i) => (
                  <p key={i}>
                    Section {i + 1}. Read each question carefully and support
                    your answer with evidence. This is sample guidance for a
                    long-content preview.
                  </p>
                ))}
              </div>
              <DialogClose render={<Button variant="outline" />}>
                Close guidance
              </DialogClose>
            </DialogContent>
          </Dialog>
          <output aria-live="polite">{notice}</output>
        </div>
      );
    case 'offcanvas':
      return (
        <div className="catalogue-stack">
          <label>
            Placement{' '}
            <select
              value={side}
              onChange={(e) => setSide(e.target.value as typeof side)}
            >
              {['left', 'right', 'top', 'bottom'].map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </label>
          <Sheet>
            <SheetTrigger render={<Button />}>Open sample drawer</SheetTrigger>
            <SheetContent side={side} className="catalogue-sheet">
              <SheetHeader>
                <SheetTitle>Sample resource details</SheetTitle>
                <SheetDescription>
                  Local demonstration · modal backdrop and scroll lock.
                </SheetDescription>
              </SheetHeader>
              <div className="catalogue-stack">
                <p>Atomic structure · iGCSE Chemistry</p>
                <label htmlFor="catalogue-note">
                  Sample note
                  <Input
                    id="catalogue-note"
                    placeholder="Try editing this local field"
                  />
                </label>
                <details>
                  <summary>Additional information</summary>
                  <p>Use a drawer to preserve workspace context.</p>
                </details>
              </div>
              <SheetClose render={<Button variant="outline" />}>
                Close drawer
              </SheetClose>
            </SheetContent>
          </Sheet>
          <p>
            Editing uses a modal drawer. Nonmodal and dark surfaces are
            documented alternatives; no product default is changed.
          </p>
        </div>
      );
    case 'popovers':
      return (
        <div className="catalogue-stack">
          <div className="catalogue-row">
            {(['top', 'bottom', 'left', 'right'] as const).map((position) => (
              <Popover key={position}>
                <PopoverTrigger render={<Button variant="outline" />}>
                  Help: {position}
                </PopoverTrigger>
                <PopoverContent side={position}>
                  <PopoverTitle>Review evidence</PopoverTitle>
                  <PopoverDescription>
                    Check the sample answer against the supporting material
                    before deciding.
                  </PopoverDescription>
                </PopoverContent>
              </Popover>
            ))}
          </div>
          <Popover>
            <PopoverTrigger render={<Button />}>Sample filter</PopoverTrigger>
            <PopoverContent>
              <PopoverTitle>Filter preview</PopoverTitle>
              <PopoverDescription>
                Changes affect this demonstration only.
              </PopoverDescription>
              <label>
                <input
                  type="checkbox"
                  checked={show}
                  onChange={(e) => setShow(e.target.checked)}
                />{' '}
                Ready resources only
              </label>
            </PopoverContent>
          </Popover>
          <output aria-live="polite">
            {show ? 'Ready resources' : 'All resources'}
          </output>
        </div>
      );
    case 'tooltips':
      return (
        <TooltipProvider>
          <div className="catalogue-stack">
            <div className="catalogue-row">
              {(['top', 'bottom', 'left', 'right'] as const).map((position) => (
                <Tooltip key={position}>
                  <TooltipTrigger render={<Button variant="outline" />}>
                    Help on {position}
                  </TooltipTrigger>
                  <TooltipContent side={position}>
                    Preview supporting evidence
                  </TooltipContent>
                </Tooltip>
              ))}
            </div>
            <Tooltip>
              <TooltipTrigger
                render={
                  <Button
                    aria-disabled="true"
                    variant="outline"
                    aria-label="Submission unavailable: complete the review first"
                  />
                }
              >
                Submit unavailable
              </TooltipTrigger>
              <TooltipContent>Complete the review first.</TooltipContent>
            </Tooltip>
            <p>
              Essential help: complete the review before submitting. This text
              remains available on touch devices.
            </p>
          </div>
        </TooltipProvider>
      );
    case 'nav-tabs':
      return (
        <div className="catalogue-stack">
          {['line', 'default', 'vertical'].map((variant) => (
            <Tabs
              key={variant}
              defaultValue="overview"
              orientation={variant === 'vertical' ? 'vertical' : 'horizontal'}
            >
              <TabsList
                variant={variant === 'line' ? 'line' : 'default'}
                aria-label={`${variant} sample panels`}
              >
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="activity">
                  Activity <CountBadge count={3} label="sample activities" />
                </TabsTrigger>
                <TabsTrigger value="resources">Resources</TabsTrigger>
                <TabsTrigger value="locked" disabled>
                  Locked
                </TabsTrigger>
              </TabsList>
              <TabsContent value="overview">
                A compact overview of sample learning progress.
              </TabsContent>
              <TabsContent value="activity">
                Three sample activities completed this week.
              </TabsContent>
              <TabsContent value="resources">
                Sample Chemistry and Mathematics resources.
              </TabsContent>
            </Tabs>
          ))}
        </div>
      );
    case 'carousel':
      return <CarouselDemo />;
    default:
      return null;
  }
}
function CarouselDemo() {
  const [api, setApi] = useState<CarouselApi>(),
    [index, setIndex] = useState(0),
    [timed, setTimed] = useState(false),
    [paused, setPaused] = useState(false);
  useEffect(() => {
    if (!api) return;
    const update = () => setIndex(api.selectedScrollSnap());
    api.on('select', update);
    return () => {
      api.off('select', update);
    };
  }, [api]);
  useEffect(() => {
    if (!api || !timed || paused) return;
    const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (motion.matches) return;
    const timer = setInterval(() => {
      if (!document.hidden) api.scrollNext();
    }, 4500);
    return () => clearInterval(timer);
  }, [api, timed, paused]);
  return (
    <div className="catalogue-stack">
      <label>
        <input
          type="checkbox"
          checked={timed}
          onChange={(e) => setTimed(e.target.checked)}
        />{' '}
        Opt in to timed sample
      </label>
      <Button
        variant="outline"
        aria-pressed={paused}
        onClick={() => setPaused(!paused)}
      >
        {paused ? 'Resume' : 'Pause'}
      </Button>
      <div
        onMouseEnter={() => setPaused(true)}
        onFocusCapture={() => setPaused(true)}
      >
        <Carousel
          setApi={setApi}
          opts={{ loop: true }}
          className="catalogue-carousel"
        >
          <CarouselContent>
            {['Atomic structure', 'Algebra practice', 'Forces and motion'].map(
              (s, i) => (
                <CarouselItem key={s}>
                  <article className="catalogue-slide">
                    <img src="/favicon.svg" width="80" height="80" alt="" />
                    <h4>{s}</h4>
                    <p>Sample learning resource {i + 1} of 3</p>
                  </article>
                </CarouselItem>
              ),
            )}
          </CarouselContent>
          <CarouselPrevious />
          <CarouselNext />
        </Carousel>
      </div>
      <div className="catalogue-row">
        {[0, 1, 2].map((i) => (
          <Button
            key={i}
            size="sm"
            variant={index === i ? 'default' : 'outline'}
            aria-label={`Show slide ${i + 1}`}
            aria-pressed={index === i}
            onClick={() => api?.scrollTo(i)}
          >
            {i + 1}
          </Button>
        ))}
      </div>
      <output aria-live={timed ? 'off' : 'polite'}>
        Slide {index + 1} of 3
      </output>
      <p>
        Manual advancement is the default. Focus/hover pauses the timed
        specimen; use Resume to restart. Reduced motion disables automatic
        movement.
      </p>
    </div>
  );
}
