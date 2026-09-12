'use client';

import { useEffect, useState } from 'react';
import {
  ArrowLeft,
  Bell,
  BookOpen,
  CheckCircle2,
  Clock3,
  FileText,
  GraduationCap,
  Info,
  Palette,
  Search,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
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
import { Button } from '@/components/ui/button';
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

const palette = [
  ['Primary', '#2E65D5'],
  ['Deep blue', '#163F9F'],
  ['Canvas', '#F1F4FB'],
  ['Success', '#22A77A'],
  ['Highlight', '#F2AE49'],
];

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
          <Button
            onClick={() => {
              window.location.href = '/';
            }}
          >
            <ArrowLeft /> Return to sign in
          </Button>
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
          <Button
            variant="outline"
            onClick={() => {
              window.location.href = '/#today';
            }}
          >
            <ArrowLeft /> Admin portal
          </Button>
        </div>
      </header>
      <main className="ui-reference-main">
        <section className="ui-reference-hero">
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

        <section className="ui-section">
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

        <section className="ui-section">
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

        <section className="ui-section">
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
