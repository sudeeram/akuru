'use client';
import { AvatarBuilderPreview } from '@/features/student-avatar-editor';
import { useState } from 'react';
import {
  FilterToolbar,
  EditorDrawer,
  AdvancedPanel,
  LoadingState,
  ErrorState,
} from '@/components/portal/workspace';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

/** Isolated examples: no account data, network requests or publication actions. */
export function WorkflowPatterns() {
  const [search, setSearch] = useState('');
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState('');
  return (
    <section className="panel stack">
      <AvatarBuilderPreview />
      <h2>Real workflow patterns</h2>
      <p>
        Compact queues keep search and row actions visible; editing opens in a
        focused drawer.
      </p>
      <FilterToolbar
        search={search}
        onSearch={setSearch}
        placeholder="Search the example queue…"
        count={
          'Topic review'.toLowerCase().includes(search.toLowerCase()) ? 1 : 0
        }
        onClear={() => setSearch('')}
      >
        <Button onClick={() => setOpen(true)}>Open example editor</Button>
      </FilterToolbar>
      {'Topic review'.toLowerCase().includes(search.toLowerCase()) ? (
        <div className="resource-row">
          <strong>Topic review</strong>
          <span className="pill">Draft</span>
          <Button variant="outline" onClick={() => setOpen(true)}>
            Review topic
          </Button>
        </div>
      ) : (
        <p>No examples match this search.</p>
      )}
      <EditorDrawer
        open={open}
        onOpenChange={setOpen}
        title="Example topic editor"
        dirty={Boolean(title)}
      >
        <form
          className="stack"
          onSubmit={(event) => {
            event.preventDefault();
            setTitle('');
            setOpen(false);
          }}
        >
          <label htmlFor="example-topic-title">Topic title</label>
          <Input
            id="example-topic-title"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            required
          />
          <Button type="submit">Save example</Button>
        </form>
      </EditorDrawer>
      <AdvancedPanel title="Loading, recovery and acceptance scenarios">
        <LoadingState message="Example loading state" />
        <ErrorState
          message="Example connection error"
          retry={() => setSearch('')}
        />
        <ul>
          <li>
            Phone, tablet and desktop: no clipped controls; tables scroll within
            their card.
          </li>
          <li>
            Keyboard: visible focus, labelled fields, drawer focus return and
            Escape protection for unsaved edits.
          </li>
          <li>
            Refresh and Back/Forward: restore filters, learner context and
            supported record links.
          </li>
          <li>
            Check empty, no-results, denied access, failed saves and long names.
          </li>
          <li>
            Active learning: focus view keeps timer, answer controls and an
            explicit exit available.
          </li>
        </ul>
      </AdvancedPanel>
    </section>
  );
}
