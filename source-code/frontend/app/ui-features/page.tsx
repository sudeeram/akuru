'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  ArrowLeft,
  ArrowRight,
  Bell,
  BookOpen,
  CheckCircle2,
  Clock3,
  FileText,
  FolderKanban,
  GraduationCap,
  Info,
  LayoutDashboard,
  LockKeyhole,
  Mail,
  MoreHorizontal,
  Palette,
  Search,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
  UserRound,
  Users,
} from 'lucide-react';
import { api, ApiError, type UiFeaturesAccess } from '@/lib/api';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  Avatar,
  AvatarBadge,
  AvatarFallback,
  AvatarGroup,
} from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Button, buttonVariants } from '@/components/ui/button';
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import {
  Progress,
  ProgressLabel,
  ProgressValue,
} from '@/components/ui/progress';
import { Switch } from '@/components/ui/switch';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';

const palette = [
  ['Primary', '#2E65D5'],
  ['Deep blue', '#163F9F'],
  ['Canvas', '#F1F4FB'],
  ['Success', '#22A77A'],
  ['Highlight', '#F2AE49'],
];

const featureNavigation = [
  ['ui-overview', 'Overview', LayoutDashboard],
  ['ui-apps', 'Apps', FolderKanban],
  ['ui-widgets', 'Widgets', Sparkles],
  ['ui-components', 'UI', Palette],
  ['ui-forms', 'Forms & tables', FileText],
  ['ui-charts', 'Charts', TrendingUpIcon],
  ['ui-pages', 'Pages', BookOpen],
  ['ui-access', 'Access', LockKeyhole],
] as const;

function TrendingUpIcon({ size = 17 }: { size?: number }) {
  return <span style={{ fontSize: size, lineHeight: 1 }}>↗</span>;
}

const taskColumns = [
  {
    title: 'Upcoming',
    tone: 'info',
    tasks: ['Review Chemistry textbook units', 'Map Physics paper questions'],
  },
  {
    title: 'In progress',
    tone: 'warning',
    tasks: ['Configure Grade 10 Term 2 coverage', 'Prepare Maths mock paper'],
  },
  {
    title: 'Completed',
    tone: 'success',
    tasks: ['Create parent accounts', 'Upload Biology textbook'],
  },
] as const;

export default function UiFeaturesPage() {
  const [access, setAccess] = useState<UiFeaturesAccess | null>(null);
  const [denied, setDenied] = useState(false);
  useEffect(() => {
    api('admin/ui-features')
      .then(setAccess)
      .catch((error: unknown) => {
        if (
          error instanceof ApiError &&
          (error.status === 401 || error.status === 403)
        )
          setDenied(true);
        else setDenied(true);
      });
  }, []);

  if (!access && !denied)
    return (
      <div className="ui-reference-loading">
        <div>
          <span className="brand-mark">A</span>
          <p>Checking Admin access…</p>
        </div>
      </div>
    );
  if (denied)
    return (
      <div className="ui-reference-loading">
        <div className="ui-reference-denied">
          <ShieldCheck size={32} />
          <h2>Admin access required</h2>
          <p>
            Sign in with an AKURU Admin account to view the component reference.
          </p>
          <Link className={buttonVariants()} href="/">
            <ArrowLeft /> Return to sign in
          </Link>
        </div>
      </div>
    );

  return (
    <div className="ui-reference-page">
      <header className="ui-reference-header">
        <div className="ui-reference-brand">
          <span className="brand-mark">A</span>
          <div>
            AKURU<small>Admin UI reference</small>
          </div>
        </div>
        <div className="ui-reference-actions">
          <span className="muted">Signed in as {access?.user.name}</span>
          <Link
            className={cn(buttonVariants({ variant: 'outline' }))}
            href="/#today"
          >
            <ArrowLeft /> Admin portal
          </Link>
        </div>
      </header>
      <nav className="ui-top-navigation" aria-label="UI feature categories">
        <div className="ui-top-navigation-inner">
          {featureNavigation.map(([id, label, Icon]) => (
            <a href={`#${id}`} key={id}>
              <Icon size={17} />
              {label}
            </a>
          ))}
        </div>
      </nav>
      <main className="ui-reference-main">
        <section className="ui-reference-hero" id="ui-overview">
          <div className="ui-reference-hero-copy">
            <span className="ui-kicker">AKURU DESIGN SYSTEM · PHASE 1</span>
            <h1>One consistent language for every learning journey.</h1>
            <p>
              This page documents components currently available to AKURU.
              Admins can review patterns before new portal features are built.
            </p>
          </div>
          <div
            className="bot-sticker bot-checklist"
            aria-label="AKURU BOT presenting a checklist"
          />
        </section>

        <section className="ui-section" id="ui-components">
          <div className="ui-section-heading">
            <div>
              <h2>Foundation</h2>
              <p>
                Education dashboard cues adapted to AKURU’s identity,
                accessibility needs and family learning context.
              </p>
            </div>
            <Badge className="ui-status-info">
              <Palette /> Approved palette
            </Badge>
          </div>
          <div className="ui-feature-grid">
            <Card className="ui-feature-card wide">
              <CardHeader>
                <CardTitle>Colour palette</CardTitle>
                <CardDescription>
                  Primary blue anchors actions; green and amber communicate
                  progress and attention.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="ui-palette">
                  {palette.map(([name, color]) => (
                    <div className="ui-swatch" key={name}>
                      <div
                        className="ui-swatch-color"
                        style={{ background: color }}
                      />
                      <span>
                        {name}
                        <br />
                        {color}
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
            <Card className="ui-feature-card">
              <CardHeader>
                <CardTitle>Typography</CardTitle>
                <CardDescription>
                  Clear hierarchy for scanning and younger readers.
                </CardDescription>
              </CardHeader>
              <CardContent className="ui-demo-stack">
                <h1>Page title</h1>
                <h2>Section heading</h2>
                <h3>Card heading</h3>
                <p>Supporting copy explains the next useful action.</p>
                <small className="muted">Metadata · Grade 10 · Term 2</small>
              </CardContent>
            </Card>
          </div>
        </section>

        <section className="ui-section">
          <div className="ui-section-heading">
            <div>
              <h2>Actions and status</h2>
              <p>
                Reusable controls and feedback states already available in the
                portal.
              </p>
            </div>
          </div>
          <div className="ui-feature-grid">
            <Card className="ui-feature-card">
              <CardHeader>
                <CardTitle>Buttons</CardTitle>
              </CardHeader>
              <CardContent className="ui-demo-row">
                <Button>Primary action</Button>
                <Button variant="secondary">Secondary</Button>
                <Button variant="outline">Outline</Button>
                <Button variant="ghost">Ghost</Button>
                <Button disabled>Unavailable</Button>
              </CardContent>
            </Card>
            <Card className="ui-feature-card">
              <CardHeader>
                <CardTitle>Badges</CardTitle>
              </CardHeader>
              <CardContent className="ui-demo-row">
                <Badge className="ui-status-success">Ready</Badge>
                <Badge className="ui-status-warning">Needs review</Badge>
                <Badge className="ui-status-info">In progress</Badge>
                <Badge variant="outline">Draft</Badge>
              </CardContent>
            </Card>
            <Card className="ui-feature-card">
              <CardHeader>
                <CardTitle>People and alerts</CardTitle>
              </CardHeader>
              <CardContent className="ui-demo-stack">
                <AvatarGroup>
                  <Avatar>
                    <AvatarFallback>AS</AvatarFallback>
                    <AvatarBadge />
                  </Avatar>
                  <Avatar>
                    <AvatarFallback>KM</AvatarFallback>
                  </Avatar>
                  <Avatar>
                    <AvatarFallback>RJ</AvatarFallback>
                  </Avatar>
                </AvatarGroup>
                <div className="ui-demo-row">
                  <Bell size={18} />
                  <span>3 items need attention</span>
                </div>
              </CardContent>
            </Card>
            <Card className="ui-feature-card wide">
              <CardHeader>
                <CardTitle>Messages</CardTitle>
              </CardHeader>
              <CardContent className="ui-demo-stack">
                <Alert>
                  <Info />
                  <AlertTitle>Textbook ready</AlertTitle>
                  <AlertDescription>
                    Units can now be mapped to Grade 10 Term 2.
                  </AlertDescription>
                </Alert>
                <Alert variant="destructive">
                  <TriangleAlert />
                  <AlertTitle>Mapping incomplete</AlertTitle>
                  <AlertDescription>
                    Every past paper question must link to at least one unit in
                    the same subject.
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
            <Card className="ui-feature-card">
              <CardHeader>
                <CardTitle>Selection controls</CardTitle>
              </CardHeader>
              <CardContent className="ui-demo-stack">
                <div className="ui-demo-row">
                  <Checkbox id="include-term-one" defaultChecked />
                  <label htmlFor="include-term-one">Include Term 1 units</label>
                </div>
                <div className="ui-demo-row">
                  <Switch id="notify-parent" defaultChecked />
                  <label htmlFor="notify-parent">Notify parent</label>
                </div>
              </CardContent>
            </Card>
          </div>
        </section>

        <section className="ui-section" id="ui-apps">
          <div className="ui-section-heading">
            <div>
              <h2>Workflow board</h2>
              <p>
                A task board pattern for document ingestion, curriculum setup
                and content review.
              </p>
            </div>
            <Button variant="outline">
              <FolderKanban /> Add task
            </Button>
          </div>
          <div className="ui-task-board">
            {taskColumns.map((column) => (
              <div className="ui-task-column" key={column.title}>
                <div className="ui-task-column-heading">
                  <Badge className={`ui-status-${column.tone}`}>
                    {column.title}
                  </Badge>
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    aria-label={`${column.title} actions`}
                  >
                    <MoreHorizontal />
                  </Button>
                </div>
                {column.tasks.map((task, index) => (
                  <article className="ui-task-card" key={task}>
                    <div className="ui-demo-row">
                      <Checkbox
                        id={`${column.tone}-${index}`}
                        defaultChecked={column.tone === 'success'}
                      />
                      <label htmlFor={`${column.tone}-${index}`}>{task}</label>
                    </div>
                    <div className="ui-task-meta">
                      <span>
                        <Clock3 size={14} /> {index ? 'Friday' : 'Today'}
                      </span>
                      <AvatarGroup>
                        <Avatar size="sm">
                          <AvatarFallback>AD</AvatarFallback>
                        </Avatar>
                        <Avatar size="sm">
                          <AvatarFallback>RV</AvatarFallback>
                        </Avatar>
                      </AvatarGroup>
                    </div>
                  </article>
                ))}
                <Button variant="ghost" className="ui-task-add">
                  + Add another task
                </Button>
              </div>
            ))}
          </div>
        </section>

        <section className="ui-section" id="ui-forms">
          <div className="ui-section-heading">
            <div>
              <h2>Forms and progress</h2>
              <p>
                Input patterns for accounts, curriculum configuration, documents
                and assessments.
              </p>
            </div>
          </div>
          <div className="ui-feature-grid">
            <Card className="ui-feature-card wide">
              <CardHeader>
                <CardTitle>Form fields</CardTitle>
                <CardDescription>
                  Labels stay visible and validation belongs next to the
                  affected field.
                </CardDescription>
              </CardHeader>
              <CardContent className="ui-demo-stack">
                <div className="ui-demo-field">
                  <label htmlFor="feature-search">Search documents</label>
                  <div className="ui-demo-row">
                    <Search size={18} />
                    <Input
                      id="feature-search"
                      placeholder="Paper, textbook or report"
                    />
                  </div>
                </div>
                <div className="ui-demo-field">
                  <label htmlFor="feature-notes">Admin notes</label>
                  <Textarea
                    id="feature-notes"
                    placeholder="Add context for future reviewers…"
                  />
                </div>
              </CardContent>
              <CardFooter>
                <Button>
                  <CheckCircle2 /> Save configuration
                </Button>
              </CardFooter>
            </Card>
            <Card className="ui-feature-card">
              <CardHeader>
                <CardTitle>Coverage progress</CardTitle>
                <CardAction>
                  <Badge className="ui-status-success">On track</Badge>
                </CardAction>
              </CardHeader>
              <CardContent className="ui-demo-stack">
                <Progress value={76}>
                  <ProgressLabel>Maths</ProgressLabel>
                  <ProgressValue>{() => '76%'}</ProgressValue>
                </Progress>
                <Progress value={58}>
                  <ProgressLabel>Physics</ProgressLabel>
                  <ProgressValue>{() => '58%'}</ProgressValue>
                </Progress>
                <Progress value={91}>
                  <ProgressLabel>English</ProgressLabel>
                  <ProgressValue>{() => '91%'}</ProgressValue>
                </Progress>
              </CardContent>
            </Card>
          </div>
        </section>

        <section className="ui-section" id="ui-widgets">
          <div className="ui-section-heading">
            <div>
              <h2>Dashboard and data</h2>
              <p>Cards, tabs and tables for concise operational views.</p>
            </div>
          </div>
          <div className="ui-feature-grid">
            <Card className="ui-feature-card full">
              <CardHeader>
                <CardTitle>Admin overview</CardTitle>
                <CardDescription>
                  Use a few meaningful measures before detailed tables.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="ui-metric-grid">
                  <div className="ui-metric">
                    <Users size={20} />
                    <strong>3</strong>
                    <span className="muted">Active learners</span>
                  </div>
                  <div className="ui-metric">
                    <BookOpen size={20} />
                    <strong>42</strong>
                    <span className="muted">Mapped units</span>
                  </div>
                  <div className="ui-metric">
                    <FileText size={20} />
                    <strong>8</strong>
                    <span className="muted">Documents ready</span>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="ui-feature-card full">
              <CardHeader>
                <CardTitle>Tabs and table</CardTitle>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="learners">
                  <TabsList>
                    <TabsTrigger value="learners">
                      <GraduationCap /> Learners
                    </TabsTrigger>
                    <TabsTrigger value="content">
                      <FileText /> Content
                    </TabsTrigger>
                  </TabsList>
                  <TabsContent value="learners">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Learner</TableHead>
                          <TableHead>Current stage</TableHead>
                          <TableHead>Subjects</TableHead>
                          <TableHead>Status</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        <TableRow>
                          <TableCell>Alex Silva</TableCell>
                          <TableCell>Grade 10 · Term 2</TableCell>
                          <TableCell>Maths, Physics, ICT</TableCell>
                          <TableCell>
                            <Badge className="ui-status-success">Active</Badge>
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Maya Silva</TableCell>
                          <TableCell>Grade 11 · Term 1</TableCell>
                          <TableCell>English, Biology, Chemistry</TableCell>
                          <TableCell>
                            <Badge className="ui-status-warning">Review</Badge>
                          </TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TabsContent>
                  <TabsContent value="content">
                    <div className="ui-demo-stack">
                      <p>
                        Content views use the same table structure for
                        textbooks, units, papers and reports.
                      </p>
                      <div className="ui-demo-row">
                        <Clock3 size={18} />
                        <span>Last reviewed today</span>
                      </div>
                    </div>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          </div>
        </section>

        <section className="ui-section" id="ui-charts">
          <div className="ui-section-heading">
            <div>
              <h2>Charts and trends</h2>
              <p>
                Accessible summaries pair every visual with a title, value and
                readable data labels.
              </p>
            </div>
            <Badge className="ui-status-info">Last 6 weeks</Badge>
          </div>
          <div className="ui-feature-grid">
            <Card className="ui-feature-card wide">
              <CardHeader>
                <CardTitle>Practice completion</CardTitle>
                <CardDescription>
                  Completed questions by subject
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div
                  className="ui-bar-chart"
                  aria-label="Maths 82 percent, Physics 64 percent, English 91 percent, ICT 73 percent"
                >
                  <div>
                    <span>Maths</span>
                    <i style={{ '--bar': '82%' } as React.CSSProperties} />
                    <strong>82%</strong>
                  </div>
                  <div>
                    <span>Physics</span>
                    <i style={{ '--bar': '64%' } as React.CSSProperties} />
                    <strong>64%</strong>
                  </div>
                  <div>
                    <span>English</span>
                    <i style={{ '--bar': '91%' } as React.CSSProperties} />
                    <strong>91%</strong>
                  </div>
                  <div>
                    <span>ICT</span>
                    <i style={{ '--bar': '73%' } as React.CSSProperties} />
                    <strong>73%</strong>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="ui-feature-card">
              <CardHeader>
                <CardTitle>Weekly activity</CardTitle>
                <CardDescription>Questions attempted</CardDescription>
              </CardHeader>
              <CardContent>
                <div
                  className="ui-mini-chart"
                  aria-label="Weekly activity rose from 8 to 21 questions"
                >
                  <span style={{ height: '34%' }} />
                  <span style={{ height: '48%' }} />
                  <span style={{ height: '42%' }} />
                  <span style={{ height: '70%' }} />
                  <span style={{ height: '62%' }} />
                  <span style={{ height: '88%' }} />
                </div>
                <div className="ui-chart-axis">
                  <span>W1</span>
                  <span>W2</span>
                  <span>W3</span>
                  <span>W4</span>
                  <span>W5</span>
                  <span>W6</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </section>

        <section className="ui-section" id="ui-pages">
          <div className="ui-section-heading">
            <div>
              <h2>Page patterns</h2>
              <p>Composed views for common AKURU administration tasks.</p>
            </div>
          </div>
          <div className="ui-feature-grid">
            <Card className="ui-feature-card">
              <CardHeader>
                <CardTitle>Multi-step setup</CardTitle>
                <CardDescription>
                  Keep long setup flows clear and resumable.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ol className="ui-stepper">
                  <li className="complete">
                    <span>1</span>
                    <div>
                      <strong>Textbook</strong>
                      <small>Uploaded</small>
                    </div>
                  </li>
                  <li className="active">
                    <span>2</span>
                    <div>
                      <strong>Units</strong>
                      <small>In progress</small>
                    </div>
                  </li>
                  <li>
                    <span>3</span>
                    <div>
                      <strong>Term coverage</strong>
                      <small>Next</small>
                    </div>
                  </li>
                  <li>
                    <span>4</span>
                    <div>
                      <strong>Question mapping</strong>
                      <small>Pending</small>
                    </div>
                  </li>
                </ol>
              </CardContent>
              <CardFooter>
                <Button>
                  Continue setup <ArrowRight />
                </Button>
              </CardFooter>
            </Card>
            <Card className="ui-feature-card wide">
              <CardHeader>
                <CardTitle>User directory</CardTitle>
                <CardDescription>
                  Human-readable account records; internal UUIDs remain hidden.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>User</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>Scope</TableHead>
                      <TableHead>Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow>
                      <TableCell>
                        <div className="ui-person">
                          <Avatar>
                            <AvatarFallback>NS</AvatarFallback>
                          </Avatar>
                          <div>
                            <strong>Nimal Silva</strong>
                            <small>@nimal.silva</small>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">Parent</Badge>
                      </TableCell>
                      <TableCell>2 children</TableCell>
                      <TableCell>
                        <Button variant="ghost" size="sm">
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>
                        <div className="ui-person">
                          <Avatar>
                            <AvatarFallback>AS</AvatarFallback>
                          </Avatar>
                          <div>
                            <strong>Alex Silva</strong>
                            <small>@alex.silva</small>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge className="ui-status-info">Student</Badge>
                      </TableCell>
                      <TableCell>Grade 10 · Term 2</TableCell>
                      <TableCell>
                        <Button variant="ghost" size="sm">
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>
        </section>

        <section className="ui-section" id="ui-access">
          <div className="ui-section-heading">
            <div>
              <h2>Access and communication</h2>
              <p>
                Authentication, permission and notification patterns aligned
                with AKURU security.
              </p>
            </div>
          </div>
          <div className="ui-feature-grid">
            <Card className="ui-feature-card">
              <CardHeader>
                <CardTitle>Secure sign-in</CardTitle>
                <CardDescription>
                  Use visible labels, clear requirements and specific errors.
                </CardDescription>
              </CardHeader>
              <CardContent className="ui-demo-stack">
                <div className="ui-demo-field">
                  <label htmlFor="reference-username">Username</label>
                  <Input id="reference-username" placeholder="your.username" />
                </div>
                <div className="ui-demo-field">
                  <label htmlFor="reference-password">Password</label>
                  <Input
                    id="reference-password"
                    type="password"
                    value="example-password"
                    readOnly
                  />
                </div>
                <Button>
                  <LockKeyhole /> Sign in securely
                </Button>
              </CardContent>
            </Card>
            <Card className="ui-feature-card">
              <CardHeader>
                <CardTitle>Permission states</CardTitle>
              </CardHeader>
              <CardContent className="ui-demo-stack">
                <Alert>
                  <ShieldCheck />
                  <AlertTitle>Admin access</AlertTitle>
                  <AlertDescription>
                    You may manage accounts and curriculum content.
                  </AlertDescription>
                </Alert>
                <Alert variant="destructive">
                  <LockKeyhole />
                  <AlertTitle>Access restricted</AlertTitle>
                  <AlertDescription>
                    This area is available only to AKURU administrators.
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
            <Card className="ui-feature-card">
              <CardHeader>
                <CardTitle>Notifications</CardTitle>
              </CardHeader>
              <CardContent className="ui-notification-list">
                <div>
                  <Bell />
                  <span>
                    <strong>Question mapping ready</strong>
                    <small>Physics · moments and forces</small>
                  </span>
                </div>
                <div>
                  <Mail />
                  <span>
                    <strong>Parent review due</strong>
                    <small>Two assessments need feedback</small>
                  </span>
                </div>
                <div>
                  <UserRound />
                  <span>
                    <strong>New learner configured</strong>
                    <small>Grade 10 · Term 1</small>
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>
        </section>
        <section className="ui-section">
          <Alert>
            <Sparkles />
            <AlertTitle>Reference scope</AlertTitle>
            <AlertDescription>
              This catalog contains AKURU-owned components and example data
              only. The external EduAdmin demo informed layout rhythm and colour
              direction; no vendor code or assets are included.
            </AlertDescription>
          </Alert>
        </section>
      </main>
    </div>
  );
}
