"use client";
import { BookOpen, Calculator, FlaskConical, Monitor, Feather } from "lucide-react";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";
import type { Subject, State, Student, Attempt } from "@/lib/api";
export const subjectIcons: Record<string, typeof BookOpen> = {
  maths: Calculator,
  science: FlaskConical,
  english: Feather,
  ict: Monitor,
};
export function SubjectIcon({ subject }: { subject: Subject }) {
  const Icon = subjectIcons[subject.id] || BookOpen;
  return (
    <span className={`subject-icon ${subject.color}`}>
      <Icon size={23} />
    </span>
  );
}
export function Heading({
  eyebrow,
  title,
  children,
  action,
}: {
  eyebrow?: string;
  title: string;
  children?: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        {eyebrow && <div className="eyebrow">{eyebrow}</div>}
        <h1>{title}</h1>
        {children && <p>{children}</p>}
      </div>
      {action}
    </div>
  );
}
export function Empty({ title, children }: { title: string; children?: React.ReactNode }) {
  return (
    <div className="empty">
      <BookOpen size={30} />
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  );
}
export function Picker({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <div className="picker">
      <label>{label}</label>
      <Select
        value={value}
        onValueChange={(v) => v !== null && onChange(String(v))}
        items={Object.fromEntries(options.map((o) => [o.value, o.label]))}
      >
        <SelectTrigger aria-label={label}>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {options.map((o) => (
            <SelectItem key={o.value} value={o.value}>
              {o.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
export type FeatureProps = {
  data: State;
  child: Student;
  subject: string;
  setSubject: (id: string) => void;
  refresh: () => Promise<void>;
  notify: (s: string) => void;
  go: (view: string, subject?: string) => void;
  selected: string;
  setSelected: (id: string) => void;
};
export function Status({ status }: { status: string }) {
  const labels: Record<string, string> = {
    "needs-review": "Awaiting review", checked: "Answer checked", reviewed: "Parent reviewed",
    approved: "Approved", pending: "Awaiting review", active: "In progress", submitted: "Submitted",
    draft: "Draft", published: "Published", archived: "Archived", processing: "Processing", failed: "Needs attention",
  };
  const label = labels[status] || status.replaceAll('_', ' ');
  const symbol = status === 'approved' || status === 'published' || status === 'checked' ? '✓' :
    status === 'failed' ? '!' : status === 'processing' ? '…' : '•';
  return (
    <span className={`status ${status}`} aria-label={`Status: ${label}`}>
      <span aria-hidden="true">{symbol}</span> {label}
    </span>
  );
}
export function Evidence({ attempts }: { attempts: Attempt[] }) {
  const checked = attempts.filter((a) => a.mark !== null);
  const possible = checked.reduce((n, a) => n + a.maxMarks, 0);
  const earned = checked.reduce((n, a) => n + (a.mark || 0), 0);
  return (
    <>
      <div className="spread small">
        <span>Marks on assessed attempts</span>
        <strong>{possible ? `${earned} / ${possible}` : "No assessed attempts"}</strong>
      </div>
      <Progress value={possible ? (100 * earned) / possible : 0} className="evidence-progress" />
    </>
  );
}
