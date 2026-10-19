'use client';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { StatusBadge } from '@/components/portal/badges';
import {
  FilterToolbar,
  EditorDrawer,
  ErrorState,
  AdvancedPanel,
} from '@/components/portal/workspace';
import { Skeleton } from '@/components/ui/skeleton';
import { pageWindow, workspaceRows, type SampleRecord } from '../models';
export default function WorkspaceDemo() {
  const [query, setQuery] = useState(''),
    [status, setStatus] = useState(''),
    [subject, setSubject] = useState(''),
    [descending, setDescending] = useState(false),
    [page, setPage] = useState(1),
    [size, setSize] = useState(5),
    [compact, setCompact] = useState(true),
    [cards, setCards] = useState(false),
    [selected, setSelected] = useState<number[]>([]),
    [detail, setDetail] = useState<SampleRecord | null>(null),
    [scenario, setScenario] = useState('populated'),
    [file, setFile] = useState(''),
    [notice, setNotice] = useState('');
  const rows =
      scenario === 'empty'
        ? []
        : workspaceRows(query, status, descending, subject),
    window = pageWindow(rows, page, size);
  const changeFilter = () => {
    setPage(1);
    setSelected([]);
  };
  const toggle = (id: number) =>
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  const clear = () => {
    setQuery('');
    setStatus('');
    setSubject('');
    changeFilter();
  };
  const selection = selected.filter((id) => rows.some((r) => r.id === id));
  const filePreview = (f: File | undefined) => {
    setFile(
      f
        ? f.size > 5 * 1024 * 1024
          ? 'File exceeds 5 MB.'
          : !f.name.toLowerCase().endsWith('.csv')
            ? 'Choose a CSV file.'
            : `${f.name} · ${f.size} bytes · Preview only; nothing uploaded.`
        : '',
    );
  };
  return (
    <div className="catalogue-stack">
      <div className="catalogue-row">
        <label>
          Scenario{' '}
          <select
            value={scenario}
            onChange={(e) => {
              setScenario(e.target.value);
              setSelected([]);
              setPage(1);
            }}
          >
            {['populated', 'loading', 'error', 'empty'].map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </label>
        <Button
          variant="outline"
          onClick={() => setCompact(!compact)}
          aria-pressed={compact}
        >
          Compact rows
        </Button>
        <Button
          variant="outline"
          onClick={() => setCards(!cards)}
          aria-pressed={cards}
        >
          Card view
        </Button>
      </div>
      <div className="catalogue-summary">
        <div>
          <strong>{scenario === 'empty' ? 0 : 23}</strong>
          <span>Sample documents</span>
        </div>
        <div>
          <strong>{rows.length}</strong>
          <span>Matching filters</span>
        </div>
        <div>
          <strong>{selection.length}</strong>
          <span>Selected</span>
        </div>
      </div>
      <FilterToolbar
        search={query}
        onSearch={(q) => {
          setQuery(q);
          changeFilter();
        }}
        count={rows.length}
        onClear={clear}
      >
        <label>
          Status{' '}
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              changeFilter();
            }}
          >
            <option value="">All statuses</option>
            {['Ready', 'Needs review', 'Draft'].map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </label>
      </FilterToolbar>
      <AdvancedPanel title="Advanced filters">
        <label>
          Subject{' '}
          <select
            value={subject}
            onChange={(e) => {
              setSubject(e.target.value);
              changeFilter();
            }}
          >
            <option value="">All subjects</option>
            {['Chemistry', 'Mathematics', 'Physics'].map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </label>
      </AdvancedPanel>
      {subject && (
        <Button
          variant="ghost"
          onClick={() => {
            setSubject('');
            changeFilter();
          }}
        >
          Remove {subject} filter ×
        </Button>
      )}
      <div className="catalogue-row">
        {['', 'Ready', 'Needs review', 'Draft'].map((s) => (
          <Button
            key={s}
            variant={status === s ? 'default' : 'outline'}
            size="sm"
            aria-pressed={status === s}
            onClick={() => {
              setStatus(s);
              changeFilter();
            }}
          >
            {s || 'All'} (
            {scenario === 'empty'
              ? 0
              : workspaceRows(query, s, false, subject).length}
            )
          </Button>
        ))}
        {status && (
          <Button
            variant="ghost"
            onClick={() => {
              setStatus('');
              changeFilter();
            }}
          >
            Remove {status} filter ×
          </Button>
        )}
      </div>
      <p className="catalogue-note">
        Fictional exam documents. Selection spans visible filtered pages and
        clears when filters change.
      </p>
      {scenario === 'loading' ? (
        <div aria-busy="true" aria-label="Loading sample records">
          {[1, 2, 3].map((n) => (
            <Skeleton key={n} className="h-12 mb-2" />
          ))}
        </div>
      ) : scenario === 'error' ? (
        <ErrorState
          message="Sample connection error"
          retry={() => setScenario('populated')}
        />
      ) : !rows.length ? (
        <div className="catalogue-empty">
          <h4>
            {scenario === 'empty'
              ? 'No sample records yet'
              : 'No records match these filters'}
          </h4>
          <Button
            onClick={() => {
              clear();
              setScenario('populated');
            }}
          >
            Reset sample
          </Button>
        </div>
      ) : (
        <>
          <div className="catalogue-row">
            <output aria-live="polite">{selection.length} selected</output>
            <Button
              variant="outline"
              disabled={!selection.length}
              onClick={() =>
                setNotice(
                  `${selection.length} sample records previewed. No records changed.`,
                )
              }
            >
              Preview selected
            </Button>
            <Button variant="ghost" onClick={() => setSelected([])}>
              Clear selection
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setDescending(!descending);
                setPage(1);
              }}
            >
              Sort: {descending ? 'Newest' : 'Oldest'}
            </Button>
          </div>
          {cards ? (
            <div className="catalogue-grid">
              {window.rows.map((r) => (
                <article className="catalogue-tile" key={r.id}>
                  <h4>{r.title}</h4>
                  <p>{r.subject}</p>
                  <StatusBadge status={r.status} />
                  <div className="catalogue-row">
                    <label>
                      <input
                        type="checkbox"
                        checked={selection.includes(r.id)}
                        onChange={() => toggle(r.id)}
                      />{' '}
                      Select {r.id}
                    </label>
                    <Button variant="outline" onClick={() => setDetail(r)}>
                      Details
                    </Button>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="catalogue-table-wrap">
              <table
                className={
                  compact ? 'catalogue-table compact' : 'catalogue-table'
                }
              >
                <caption>Sample exam documents</caption>
                <thead>
                  <tr>
                    <th>
                      <input
                        type="checkbox"
                        aria-label="Select current page"
                        checked={
                          window.rows.length > 0 &&
                          window.rows.every((r) => selection.includes(r.id))
                        }
                        onChange={(e) =>
                          setSelected(
                            e.target.checked
                              ? Array.from(
                                  new Set([
                                    ...selected,
                                    ...window.rows.map((r) => r.id),
                                  ]),
                                )
                              : selected.filter(
                                  (id) => !window.rows.some((r) => r.id === id),
                                ),
                          )
                        }
                      />
                    </th>
                    <th aria-sort={descending ? 'descending' : 'ascending'}>
                      Document
                    </th>
                    <th>Subject</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {window.rows.map((r) => (
                    <tr key={r.id} data-selected={selection.includes(r.id)}>
                      <td>
                        <input
                          type="checkbox"
                          aria-label={`Select ${r.title}`}
                          checked={selection.includes(r.id)}
                          onChange={() => toggle(r.id)}
                        />
                      </td>
                      <th scope="row">{r.title}</th>
                      <td>{r.subject}</td>
                      <td>
                        <StatusBadge status={r.status} />
                      </td>
                      <td>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setDetail(r)}
                        >
                          Details
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <footer className="catalogue-row">
            <span>
              Showing {window.start}–{window.end} of {rows.length}
            </span>
            <label>
              Rows{' '}
              <select
                value={size}
                onChange={(e) => {
                  setSize(Number(e.target.value));
                  setPage(1);
                }}
              >
                {[5, 10, 25].map((n) => (
                  <option key={n}>{n}</option>
                ))}
              </select>
            </label>
            <nav aria-label="Sample document pages" className="catalogue-row">
              <Button
                variant="outline"
                disabled={window.current === 1}
                onClick={() => setPage(1)}
              >
                First
              </Button>
              <Button
                variant="outline"
                disabled={window.current === 1}
                onClick={() => setPage(window.current - 1)}
              >
                Previous
              </Button>
              <span aria-current="page">
                {window.current} / {window.pages}
              </span>
              <Button
                variant="outline"
                disabled={window.current === window.pages}
                onClick={() => setPage(window.current + 1)}
              >
                Next
              </Button>
              <Button
                variant="outline"
                disabled={window.current === window.pages}
                onClick={() => setPage(window.pages)}
              >
                Last
              </Button>
            </nav>
          </footer>
        </>
      )}
      <output aria-live="polite">{notice}</output>
      {/* Keyboard users can use the native file input; dragging is an additional input method. */}
      {/* oxlint-disable-next-line jsx-a11y/no-noninteractive-element-interactions */}
      <label
        className="catalogue-dropzone"
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          filePreview(e.dataTransfer.files[0]);
        }}
      >
        Sample CSV preview · maximum 5 MB
        <Input
          type="file"
          accept=".csv"
          onChange={(e) => filePreview(e.target.files?.[0])}
        />
        <span>{file}</span>
      </label>
      <EditorDrawer
        open={!!detail}
        onOpenChange={(open) => {
          if (!open) setDetail(null);
        }}
        title={detail?.title || 'Sample details'}
        description="Local demonstration only"
      >
        <p>{detail?.subject}</p>
        <StatusBadge status={detail?.status || 'Draft'} />
        <p>No production record is opened or edited.</p>
      </EditorDrawer>
    </div>
  );
}
