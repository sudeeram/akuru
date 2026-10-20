'use client';
// Native SVG specimens deliberately demonstrate image sizing without an optimizer.
/* oxlint-disable next/no-img-element */
import { useState } from 'react';
import { BookOpen, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ButtonGroup } from '@/components/ui/button-group';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '@/components/ui/card';
import {
  Avatar,
  AvatarFallback,
  AvatarImage,
  AvatarBadge,
  AvatarGroup,
  AvatarGroupCount,
} from '@/components/ui/avatar';
import { SubjectProgressCard } from '@/components/portal/dashboard-widgets';
import { StudentAvatar } from '@/components/portal/student-avatar';
import {
  StatusBadge,
  MetadataBadge,
  CountBadge,
  ReviewBadge,
} from '@/components/portal/badges';
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';
import {
  Progress,
  ProgressLabel,
  ProgressValue,
} from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { Spinner } from '@/components/ui/spinner';
import { avatarPresets, avatarCatalogue } from '@/lib/student-avatar';
import type { CatalogueId } from '../registry';
import { pageWindow, sampleRecords } from '../models';
import { TimedDemo } from './timed';
const image = '/favicon.svg';
export default function Foundations({ id }: { id: CatalogueId }) {
  const [choice, setChoice] = useState('Week'),
    [count, setCount] = useState(1),
    [value, setValue] = useState(40),
    [shape, setShape] = useState('rounded'),
    [loaded, setLoaded] = useState(false),
    [width, setWidth] = useState('wide');
  const page = pageWindow(sampleRecords, count, 5);
  switch (id) {
    case 'typography':
      return (
        <div className="catalogue-stack">
          <div className="catalogue-eyebrow">Learning overview</div>
          <h4 className="catalogue-display">Make space for progress</h4>
          <p>
            Readable body text supports a calm, focused learning experience.{' '}
            <strong>Important information</strong> and <em>gentle emphasis</em>{' '}
            keep their meaning.
          </p>
          <p>
            <mark>Highlighted concept</mark> · <small>Secondary caption</small>{' '}
            ·{' '}
            <abbr title="International General Certificate of Secondary Education">
              iGCSE
            </abbr>
          </p>
          <p>
            <del>Previous version</del> <ins>Reviewed version</ins>
          </p>
          <ol>
            <li>
              Read the question
              <ul>
                <li>Identify the key evidence</li>
              </ul>
            </li>
            <li>Explain your answer</li>
          </ol>
          <figure>
            <blockquote>Practice makes progress.</blockquote>
            <figcaption>— AKURU sample learning note</figcaption>
          </figure>
          <dl>
            <dt>Course</dt>
            <dd>iGCSE Science</dd>
            <dt>Review</dt>
            <dd>A considered second look at your work.</dd>
          </dl>
          <p className="catalogue-note">
            Use semantic heading levels in order; display size is independent of
            heading rank. Body 14–16px; captions 12–13px; comfortable line
            height 1.5. Metadata stays readable.
          </p>
        </div>
      );
    case 'grid':
      return (
        <div className="catalogue-stack">
          <label>
            Preview width{' '}
            <select value={width} onChange={(e) => setWidth(e.target.value)}>
              <option>wide</option>
              <option>tablet</option>
              <option>mobile</option>
            </select>
          </label>
          <div className={`catalogue-grid-preview ${width}`}>
            <div className="catalogue-grid">
              {[
                'Equal columns',
                'Responsive columns',
                'Automatic wrapping',
              ].map((s) => (
                <div className="catalogue-tile" key={s}>
                  {s}
                </div>
              ))}
            </div>
            <div className="catalogue-split">
              <div className="catalogue-tile">
                Two thirds
                <div className="catalogue-grid">
                  <span className="catalogue-tile">Nested</span>
                  <span className="catalogue-tile">Nested</span>
                </div>
              </div>
              <div className="catalogue-tile">One third</div>
            </div>
          </div>
          <p>
            CSS grid uses minmax and automatic wrapping; compact gaps 12px,
            standard gaps 16px. Portal navigation changes at 850px. Layouts
            follow available space rather than Bootstrap column classes.
          </p>
        </div>
      );
    case 'images':
      return (
        <div className="catalogue-stack">
          <label>
            Image shape{' '}
            <select value={shape} onChange={(e) => setShape(e.target.value)}>
              {['rounded', 'circle', 'thumbnail', 'pill'].map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </label>
          <div className="catalogue-grid">
            {['left', 'center', 'right'].map((align) => (
              <figure
                key={align}
                style={{ textAlign: align as 'left' | 'center' | 'right' }}
              >
                <img
                  src={image}
                  alt="AKURU application icon"
                  width="112"
                  height="112"
                  className={`catalogue-image ${shape}`}
                  onError={(e) => {
                    e.currentTarget.hidden = true;
                  }}
                />
                <figcaption>{align} aligned · contain crop</figcaption>
              </figure>
            ))}
          </div>
          <figure className="catalogue-media-fallback">
            <BookOpen aria-hidden="true" />
            <figcaption>Image unavailable · text remains readable</figcaption>
          </figure>
          <p>
            Reserve dimensions; use cover for photos and contain for diagrams.
            Original AKURU icons/artwork only.
          </p>
        </div>
      );
    case 'cards':
      return (
        <div className="catalogue-grid">
          <section className="catalogue-colour-guide">
            <h3>AKURU subject accents</h3>
            <p>
              These production cards use stable subject colours. Progress keeps
              its existing meaning; the accent identifies the subject.
            </p>
            <div className="catalogue-grid">
              {['maths', 'biology', 'chemistry', 'physics', 'english'].map(
                (subject) => (
                  <SubjectProgressCard
                    key={subject}
                    subjectId={subject}
                    title={subject.charAt(0).toUpperCase() + subject.slice(1)}
                    description="Illustrative subject card"
                    value={null}
                    label="No assessed attempts"
                  />
                ),
              )}
            </div>
          </section>
          {[
            'Course overview',
            'Profile directory',
            'Document review',
            'Media card',
          ].map((title, i) => (
            <Card
              key={title}
              className={`catalogue-divided ${i === 0 ? 'catalogue-accent-card' : i === 1 ? 'catalogue-flush-card' : ''}`}
            >
              <CardHeader>
                <CardTitle>{title}</CardTitle>
                <CardDescription>Compact divided header</CardDescription>
              </CardHeader>
              <CardContent>
                {i === 1 ? (
                  <StudentAvatar fallback="MS" label="Maya Sample" />
                ) : i === 3 ? (
                  <img src={image} alt="AKURU icon" width="64" height="64" />
                ) : (
                  <BookOpen aria-hidden="true" />
                )}
                <p>
                  {i === 0
                    ? 'Atomic structure · 4 of 8 activities'
                    : i === 1
                      ? 'Maya Sample · iGCSE learner'
                      : 'Supporting information remains separate from actions.'}
                </p>
                <StatusBadge status={i === 2 ? 'Needs review' : 'Ready'} />
              </CardContent>
              <CardFooter>
                <Button size="sm" onClick={() => setChoice(title)}>
                  Preview
                </Button>
              </CardFooter>
            </Card>
          ))}
          <output aria-live="polite">
            {choice === 'Week'
              ? 'Choose a sample card.'
              : `${choice} preview selected.`}
          </output>
        </div>
      );
    case 'avatar':
      return (
        <div className="catalogue-stack">
          <div className="catalogue-row">
            {avatarPresets.map((base) => (
              <div key={base.base}>
                <StudentAvatar
                  avatar={base}
                  fallback="MS"
                  label={avatarCatalogue.options.base[base.base].label}
                />
                <p>{avatarCatalogue.options.base[base.base].label}</p>
              </div>
            ))}
          </div>
          <div className="catalogue-row">
            {['sm', 'default', 'lg'].map((size) => (
              <Avatar key={size} size={size as 'sm' | 'default' | 'lg'}>
                <AvatarFallback>MS</AvatarFallback>
              </Avatar>
            ))}
            <Avatar className="catalogue-avatar-ring">
              <AvatarImage src="/favicon.svg" alt="AKURU application icon" />
              <AvatarFallback>AK</AvatarFallback>
              <AvatarBadge aria-label="Sample unread count">3</AvatarBadge>
            </Avatar>
            <Avatar className="catalogue-avatar-square">
              <AvatarFallback>AS</AvatarFallback>
            </Avatar>
            <AvatarGroup>
              <Avatar>
                <AvatarFallback>MS</AvatarFallback>
              </Avatar>
              <Avatar>
                <AvatarFallback>NS</AvatarFallback>
              </Avatar>
              <AvatarGroupCount>+8</AvatarGroupCount>
            </AvatarGroup>
            <Button
              variant="outline"
              onClick={() => setLoaded(!loaded)}
              aria-expanded={loaded}
            >
              Sample group members
            </Button>
          </div>
          {loaded && (
            <p>
              Maya Sample, Noah Sample, Aria Sample and eight fictional
              learners.
            </p>
          )}
          <div className="catalogue-row">
            <MetadataBadge>Sample presence: away</MetadataBadge>
            <CountBadge count={3} label="sample notifications" />
            <span className="catalogue-icon-tile">
              <BookOpen aria-hidden="true" />
              Science
            </span>
            <span className="catalogue-specimen gradient">
              AI · visual specimen
            </span>
            <span className="catalogue-specimen medal">★ Sample award</span>
          </div>
          <p>
            Initials are the fallback. Presence and awards here are fictional;
            no online tracking or achievements are enabled.
          </p>
        </div>
      );
    case 'badges':
      return (
        <div className="catalogue-stack">
          <div className="catalogue-row">
            {[
              'Ready',
              'Needs review',
              'In progress',
              'Draft',
              'Failed',
              'Unknown state',
              'Following each other',
            ].map((status) => (
              <StatusBadge key={status} status={status} />
            ))}
          </div>
          <div className="catalogue-row">
            <MetadataBadge>iGCSE Science</MetadataBadge>
            <ReviewBadge state="partial">Partially checked</ReviewBadge>
            <CountBadge count={142} label="sample notifications" />
            <Button variant="outline" onClick={() => setCount(count + 1)}>
              Notifications{' '}
              <CountBadge count={count} label="sample notifications" />
            </Button>
          </div>
          <div dir="rtl" className="catalogue-tile">
            <StatusBadge status="Ready" />{' '}
            <MetadataBadge>RTL specimen</MetadataBadge>
          </div>
          <div className="catalogue-dark">
            <span className="catalogue-specimen">High priority · specimen</span>
            <span className="catalogue-specimen gradient">
              Decorative gradient
            </span>
          </div>
          <MetadataBadge>
            Long metadata labels wrap to remain readable within a narrow panel
          </MetadataBadge>
          <p>
            Use semantic statuses, quiet metadata and actual accessible counts.
            Decorative specimens do not replace the shared badge system.
          </p>
        </div>
      );
    case 'buttons':
      return (
        <div className="catalogue-stack">
          <div className="catalogue-row">
            {(
              [
                'default',
                'secondary',
                'outline',
                'ghost',
                'destructive',
              ] as const
            ).map((variant) => (
              <Button
                key={variant}
                variant={variant}
                onClick={() => setChoice(variant)}
              >
                {variant}
              </Button>
            ))}
          </div>
          <div className="catalogue-row">
            <Button size="sm" onClick={() => setCount(count + 1)}>
              Small {count}
            </Button>
            <Button size="lg" onClick={() => setChoice('Large')}>
              Large
            </Button>
            <Button
              variant="outline"
              aria-label="Refresh sample"
              onClick={() => setChoice('Refreshed')}
            >
              <RefreshCw />
            </Button>
            <Button disabled>Unavailable</Button>
            <Button aria-pressed={loaded} onClick={() => setLoaded(!loaded)}>
              Toggle {loaded ? 'on' : 'off'}
            </Button>
          </div>
          <div className="catalogue-row">
            <Button
              className="catalogue-rounded"
              onClick={() => setChoice('Rounded')}
            >
              Rounded
            </Button>
            <Button
              className="catalogue-soft"
              onClick={() => setChoice('Soft')}
            >
              Soft
            </Button>
            <Button
              className="catalogue-ledge"
              onClick={() => setChoice('3D specimen')}
            >
              3D specimen
            </Button>
            <Button
              className="catalogue-gradient"
              onClick={() => setChoice('Gradient specimen')}
            >
              Gradient specimen
            </Button>
          </div>
          <Button className="w-full" onClick={() => setChoice('Full width')}>
            Full width action
          </Button>
          <output aria-live="polite">
            {choice === 'Week'
              ? 'Choose an action.'
              : `${choice} action selected.`}
          </output>
          <TimedDemo />
        </div>
      );
    case 'buttons-group':
      return (
        <div className="catalogue-stack">
          <ButtonGroup aria-label="Sample period">
            {['Day', 'Week', 'Month'].map((s) => (
              <Button
                key={s}
                variant={choice === s ? 'default' : 'outline'}
                aria-pressed={choice === s}
                onClick={() => setChoice(s)}
              >
                {s}
              </Button>
            ))}
          </ButtonGroup>
          <ButtonGroup orientation="vertical" aria-label="Sample zoom">
            <Button
              variant="outline"
              onClick={() => setValue(Math.min(100, value + 10))}
            >
              Zoom in
            </Button>
            <Button
              variant="outline"
              onClick={() => setValue(Math.max(10, value - 10))}
            >
              Zoom out
            </Button>
          </ButtonGroup>
          <fieldset>
            <legend>Multiple subjects</legend>
            {['Science', 'Maths'].map((s) => (
              <label key={s}>
                <input type="checkbox" /> {s}{' '}
              </label>
            ))}
          </fieldset>
          <fieldset>
            <legend>Exclusive view</legend>
            {['Grid', 'List', 'Board'].map((s, i) => (
              <label key={s}>
                <input
                  type="radio"
                  name="catalogue-view"
                  defaultChecked={i === 0}
                />{' '}
                {s}{' '}
              </label>
            ))}
          </fieldset>
          <output aria-live="polite">
            Period: {choice} · Zoom: {value}%
          </output>
        </div>
      );
    case 'breadcrumb':
      return (
        <div className="catalogue-stack">
          {['/', '›', '→'].map((separator) => (
            <Breadcrumb key={separator}>
              <BreadcrumbList>
                <BreadcrumbItem>
                  <BreadcrumbLink href="#ui-catalog-workspace">
                    Admin workspace
                  </BreadcrumbLink>
                </BreadcrumbItem>
                <BreadcrumbSeparator>{separator}</BreadcrumbSeparator>
                <BreadcrumbItem>
                  <BreadcrumbLink href="#ui-catalog-cards">
                    Exam documents
                  </BreadcrumbLink>
                </BreadcrumbItem>
                <BreadcrumbSeparator>{separator}</BreadcrumbSeparator>
                <BreadcrumbItem>
                  <BreadcrumbPage>Review preview</BreadcrumbPage>
                </BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>
          ))}
        </div>
      );
    case 'links':
      return (
        <div className="catalogue-stack">
          <a href="#ui-catalog-typography">Inline learning guidance</a>
          <a className="catalogue-quiet-link" href="#ui-catalog-workspace">
            Secondary workspace reference →
          </a>
          <a className="catalogue-offset-link" href="#ui-catalog-cards">
            Underline offset specimen
          </a>
          <p>
            Low-opacity links are not offered: they can fail contrast. Use a
            button for an action and a meaningful link for navigation.
          </p>
        </div>
      );
    case 'list-group':
      return (
        <div className="catalogue-stack">
          <ol className="catalogue-list">
            {[
              'Read the instructions',
              'Answer practice questions',
              'Review your feedback',
            ].map((s, i) => (
              <li key={s}>
                <BookOpen aria-hidden="true" />
                <span>
                  {s}
                  <small>Sample learning step {i + 1}</small>
                </span>
                <CountBadge count={i + 1} label="sample resources" />
              </li>
            ))}
          </ol>
          <ul className="catalogue-list">
            {['Science resources', 'Mathematics resources'].map((s) => (
              <li key={s}>
                <a href="#ui-catalog-workspace">{s}</a>
              </li>
            ))}
            <li>
              <Button
                variant="ghost"
                onClick={() => setChoice('Notification preview opened')}
              >
                Preview notification
              </Button>
            </li>
            <li>
              <Button disabled>Locked resource</Button>
            </li>
          </ul>
          <label>
            <input type="checkbox" /> Include optional resources
          </label>
          <output aria-live="polite">{choice === 'Week' ? '' : choice}</output>
        </div>
      );
    case 'pagination':
      return (
        <div className="catalogue-stack">
          <ul>
            {page.rows.map((r) => (
              <li key={r.id}>{r.title}</li>
            ))}
          </ul>
          <p>
            Showing {page.start}–{page.end} of {sampleRecords.length}
          </p>
          <nav
            aria-label="Sample resource pagination"
            className="catalogue-row"
          >
            <Button
              variant="outline"
              disabled={page.current === 1}
              onClick={() => setCount(1)}
            >
              First
            </Button>
            <Button
              variant="outline"
              disabled={page.current === 1}
              onClick={() => setCount(page.current - 1)}
            >
              Previous
            </Button>
            {Array.from({ length: page.pages }, (_, i) => (
              <Button
                key={i}
                variant={page.current === i + 1 ? 'default' : 'outline'}
                aria-current={page.current === i + 1 ? 'page' : undefined}
                onClick={() => setCount(i + 1)}
              >
                {i + 1}
              </Button>
            ))}
            <Button
              variant="outline"
              disabled={page.current === page.pages}
              onClick={() => setCount(page.current + 1)}
            >
              Next
            </Button>
            <Button
              variant="outline"
              disabled={page.current === page.pages}
              onClick={() => setCount(page.pages)}
            >
              Last
            </Button>
          </nav>
        </div>
      );
    case 'progress':
      return (
        <div className="catalogue-stack">
          <label>
            Sample completion{' '}
            <input
              type="range"
              min="0"
              max="100"
              value={value}
              onChange={(e) => setValue(Number(e.target.value))}
            />
          </label>
          <Progress value={value}>
            <ProgressLabel>Study activities</ProgressLabel>
            <ProgressValue />
          </Progress>
          <figure
            className="catalogue-meter"

            aria-label="40% complete, 30% in progress, 30% remaining"
          >
            <span style={{ width: '40%' }} />
            <span style={{ width: '30%' }} />
            <span style={{ width: '30%' }} />
          </figure>
          <p>40% complete · 30% in progress · 30% remaining</p>
          <div
            className="catalogue-striped-meter"
            aria-label="Striped specimen: 60 percent"
          >
            <span style={{ width: '60%' }} />
          </div>
          <div
            className="catalogue-gradient-meter"
            aria-label="Gradient specimen: 80 percent"
          >
            <span style={{ width: '80%' }} />
          </div>
          <p>
            Striped and gradient finishes are visual specimens; the labelled
            completion control above is the recommended accessible pattern.
          </p>
          <div className="catalogue-row">
            <div
              className="catalogue-gauge"
              style={{
                background: `conic-gradient(#2e65d5 ${value}%, #e4e9f2 0)`,
              }}
            >
              <span>{value}%</span>
            </div>
            <figure
              className="catalogue-sparkline"

              aria-label="Sample activity trend: 2, 4, 3, 6, 5, 7, 8"
            >
              {[2, 4, 3, 6, 5, 7, 8].map((n, i) => (
                <span key={i} style={{ height: `${n * 10}%` }} />
              ))}
            </figure>
          </div>
          <p>
            Gauge shows completion; trend is fictional. Unknown-duration work
            uses a spinner instead of fabricated percentages.
          </p>
        </div>
      );
    case 'placeholders':
      return (
        <div className="catalogue-stack">
          <Button
            variant="outline"
            aria-pressed={loaded}
            onClick={() => setLoaded(!loaded)}
          >
            {loaded ? 'Show skeleton' : 'Show loaded content'}
          </Button>
          <div
            className="catalogue-tile catalogue-loading-card"
            aria-busy={!loaded}
          >
            {loaded ? (
              <>
                <h4>Atomic structure</h4>
                <p>Your sample learning resources are ready.</p>
                <StatusBadge status="Ready" />
              </>
            ) : (
              <>
                <span className="sr-only">Loading sample card</span>
                <Skeleton className="h-10 w-10 rounded-full" />
                <Skeleton className="h-5 w-3/4" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-8 w-24" />
              </>
            )}
          </div>
          <div className="catalogue-list" aria-hidden="true">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-10 w-full mb-2" />
            ))}
          </div>
          <p>
            Matched dimensions reduce layout movement. Decorative skeletons do
            not receive focus.
          </p>
        </div>
      );
    case 'spinner':
      return (
        <div className="catalogue-stack">
          <div className="catalogue-row">
            <Spinner aria-label="Loading sample" />
            <Spinner className="size-8" aria-label="Loading larger sample" />
            <output className="catalogue-grow">
              <span className="sr-only">Loading specimen</span>
            </output>
          </div>
          <TimedDemo />
          <p>
            Use a spinner for unknown-duration actions and skeletons for content
            structure. Keep one announcement per active operation.
          </p>
        </div>
      );
    default:
      return null;
  }
}
