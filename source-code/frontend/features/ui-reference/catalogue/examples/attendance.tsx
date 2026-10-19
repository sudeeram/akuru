'use client';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Progress,
  ProgressLabel,
  ProgressValue,
} from '@/components/ui/progress';
import { StatusBadge } from '@/components/portal/badges';
import { attendanceSummary, type AttendanceMark } from '../models';
const names = ['Maya Sample', 'Noah Sample', 'Aria Sample', 'Leo Sample'];
export default function AttendanceDemo() {
  const [marks, setMarks] = useState<AttendanceMark[]>([
    'Present',
    'Late',
    null,
    'Absent',
  ]);
  const [emptyHistory, setEmptyHistory] = useState(false);
  const summary = attendanceSummary(marks);
  return (
    <div className="catalogue-stack">
      <p className="catalogue-note">
        Sample attendance patterns · fictional learners and dates · changes are
        not saved.
      </p>
      <div className="catalogue-row">
        <Button
          variant="outline"
          onClick={() => setMarks(['Present', 'Late', null, 'Absent'])}
        >
          Reset marks
        </Button>
        <Button
          variant="outline"
          onClick={() => setMarks([null, null, null, null])}
        >
          Show no data
        </Button>
      </div>
      <div className="catalogue-grid">
        <div className="catalogue-tile">
          <strong className="catalogue-stat">
            {summary.rate === null ? 'No data' : `${summary.rate}%`}
          </strong>
          <p>Present or late / marked learners</p>
        </div>
        <div className="catalogue-tile">
          <strong>
            {summary.marked} of {summary.total} marked
          </strong>
          <Progress value={(summary.marked / summary.total) * 100}>
            <ProgressLabel>Register completion</ProgressLabel>
            <ProgressValue />
          </Progress>
        </div>
      </div>
      <h4>Sample register</h4>
      {names.map((name, i) => (
        <div className="catalogue-mark-row" key={name}>
          <span>
            {name}
            {i === 3 && ' · Register locked'}
          </span>
          <fieldset aria-label={`Status for ${name}`} className="catalogue-row">
            {(['Present', 'Late', 'Absent'] as const).map((mark) => (
              <Button
                key={mark}
                size="sm"
                variant={marks[i] === mark ? 'default' : 'outline'}
                disabled={i === 3}
                aria-pressed={marks[i] === mark}
                onClick={() =>
                  setMarks((prev) =>
                    prev.map((old, n) => (n === i ? mark : old)),
                  )
                }
              >
                {mark}
              </Button>
            ))}
          </fieldset>
        </div>
      ))}
      <output aria-live="polite">
        Present {summary.present} · Late {summary.late} · Absent{' '}
        {summary.absent} · Unmarked {summary.total - summary.marked}
      </output>
      <h4>October activity grid</h4>
      <label>
        <input
          type="checkbox"
          checked={emptyHistory}
          onChange={(e) => setEmptyHistory(e.target.checked)}
        />{' '}
        Empty history specimen
      </label>
      <p>
        Sample school days. No session is distinct from an unmarked session.
      </p>
      <figure
        className={`catalogue-heatmap ${emptyHistory ? 'is-empty' : ''}`}

        aria-label={
          emptyHistory
            ? 'No attendance history recorded for October'
            : 'October sample attendance: 12 present days, 3 late, 3 absent, 3 unmarked and 9 days with no session'
        }
      >
        {Array.from({ length: 30 }, (_, i) => (
          <span
            key={i}
            data-level={
              i % 10 < 4
                ? 'present'
                : i % 10 === 4
                  ? 'late'
                  : i % 10 === 5
                    ? 'absent'
                    : i % 10 === 6
                      ? 'unmarked'
                      : 'none'
            }
            title={
              emptyHistory
                ? `October ${i + 1}: No history`
                : `October ${i + 1}: ${i % 10 < 4 ? 'Present' : i % 10 === 4 ? 'Late' : i % 10 === 5 ? 'Absent' : i % 10 === 6 ? 'Unmarked' : 'No session'}`
            }
          >
            {i + 1}
          </span>
        ))}
      </figure>
      <p>
        Legend: green Present · amber Late · red Absent · outlined Unmarked ·
        grey No session
      </p>
      <details>
        <summary>Text summary of daily records</summary>
        <ul>
          {Array.from({ length: 30 }, (_, i) => (
            <li key={i}>
              October {i + 1}:{' '}
              {i % 10 < 4
                ? 'Present'
                : i % 10 === 4
                  ? 'Late'
                  : i % 10 === 5
                    ? 'Absent'
                    : i % 10 === 6
                      ? 'Unmarked'
                      : 'No session'}
            </li>
          ))}
        </ul>
      </details>
      <h4>Sample sessions</h4>
      {['Morning review', 'Science practice', 'Afternoon reflection'].map(
        (name, i) => (
          <div className="catalogue-mark-row" key={name}>
            <span>
              {i + 1}. {name}
            </span>
            <StatusBadge
              status={['Completed', 'In progress', 'Pending'][i]}
              label={['Completed', 'In progress', 'Pending'][i]}
            />
          </div>
        ),
      )}
      <h4>Sample group comparison</h4>
      {[98, 84, 62].map((value, i) => (
        <Progress key={value} value={value}>
          <ProgressLabel>
            Group {i + 1}: {value}% attended
          </ProgressLabel>
          <ProgressValue />
        </Progress>
      ))}
      <p>
        Attendance policy and real tracking are outside this preview. Missed
        study activity must not be interpreted as absence.
      </p>
    </div>
  );
}
