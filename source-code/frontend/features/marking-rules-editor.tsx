import { useState } from 'react';
/* eslint-disable jsx-a11y/label-has-associated-control */
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import type {
  ReviewPart,
  MarkingRules,
} from '@/api/assessments/official-paper-review.api';

const codes = (text: string) =>
  text
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);
function CodeListInput({
  value,
  onChange,
}: {
  value: string[];
  onChange: (value: string[]) => void;
}) {
  const [draft, setDraft] = useState(value.join(', '));
  return (
    <Input
      value={draft}
      onChange={(e) => setDraft(e.target.value)}
      onBlur={() => onChange(codes(draft))}
    />
  );
}
export function MarkingRulesEditor({
  part,
  onChange,
}: {
  part: ReviewPart;
  onChange: (part: ReviewPart) => void;
}) {
  const rules: MarkingRules = part.scoringRules ?? {
    version: 1,
    groups: [],
    combinedResponses: [],
  };
  const update = (next: MarkingRules) =>
    onChange({
      ...part,
      scoringRules: next,
      assessmentReadiness: 'unreviewed',
    });
  return (
    <fieldset className="pr-marking-rules">
      <legend>Automatic marking rules</legend>
      <p>
        Content approval and automatic marking are separate. This subpart can
        award at most <strong>{part.marks} marks</strong> across{' '}
        {part.markingPoints.length} distinct points. Equivalent answers for the
        same point earn credit once.
      </p>
      <p>
        Use point codes from above, separated by commas. Groups may be nested or
        separate. Conditional zero-score rules and alternative scoring paths
        still require manual marking.
      </p>
      {rules.groups.map((group, i) => (
        <fieldset key={i}>
          <legend>Additional scoring group {i + 1}</legend>
          <label>
            Group name
            <Input
              value={group.id}
              onChange={(e) =>
                update({
                  ...rules,
                  groups: rules.groups.map((g, j) =>
                    j === i ? { ...g, id: e.target.value } : g,
                  ),
                })
              }
            />
          </label>
          <label>
            Point codes
            <CodeListInput
              key={group.pointIds.join('|')}
              value={group.pointIds}
              onChange={(pointIds) =>
                update({
                  ...rules,
                  groups: rules.groups.map((g, j) =>
                    j === i ? { ...g, pointIds } : g,
                  ),
                })
              }
            />
          </label>
          <label>
            Maximum marks
            <Input
              type="number"
              min={0}
              max={part.marks}
              value={group.maxMarks}
              onChange={(e) =>
                update({
                  ...rules,
                  groups: rules.groups.map((g, j) =>
                    j === i ? { ...g, maxMarks: Number(e.target.value) } : g,
                  ),
                })
              }
            />
          </label>
          <label>
            Points required for full group credit (optional)
            <CodeListInput
              key={group.requiredForFullCredit.join('|')}
              value={group.requiredForFullCredit}
              onChange={(requiredForFullCredit) =>
                update({
                  ...rules,
                  groups: rules.groups.map((g, j) =>
                    j === i ? { ...g, requiredForFullCredit } : g,
                  ),
                })
              }
            />
          </label>
          <Button
            variant="outline"
            onClick={() =>
              update({
                ...rules,
                groups: rules.groups.filter((_, j) => j !== i),
              })
            }
          >
            Remove group
          </Button>
        </fieldset>
      ))}
      <Button
        variant="outline"
        onClick={() =>
          update({
            ...rules,
            groups: [
              ...rules.groups,
              {
                id: `group-${rules.groups.length + 1}`,
                pointIds: [],
                maxMarks: part.marks,
                requiredForFullCredit: [],
              },
            ],
          })
        }
      >
        Add group limit
      </Button>
      {rules.combinedResponses.map((rule, i) => (
        <fieldset key={i}>
          <legend>Combined response {i + 1}</legend>
          <label>
            Approved standalone response
            <Input
              value={rule.phrase}
              onChange={(e) =>
                update({
                  ...rules,
                  combinedResponses: rules.combinedResponses.map((c, j) =>
                    j === i ? { ...c, phrase: e.target.value } : c,
                  ),
                })
              }
            />
          </label>
          <label>
            Points this response satisfies
            <CodeListInput
              key={rule.pointIds.join('|')}
              value={rule.pointIds}
              onChange={(pointIds) =>
                update({
                  ...rules,
                  combinedResponses: rules.combinedResponses.map((c, j) =>
                    j === i ? { ...c, pointIds } : c,
                  ),
                })
              }
            />
          </label>
          <Button
            variant="outline"
            onClick={() =>
              update({
                ...rules,
                combinedResponses: rules.combinedResponses.filter(
                  (_, j) => j !== i,
                ),
              })
            }
          >
            Remove combined response
          </Button>
        </fieldset>
      ))}
      <Button
        variant="outline"
        onClick={() =>
          update({
            ...rules,
            combinedResponses: [
              ...rules.combinedResponses,
              { phrase: '', pointIds: [] },
            ],
          })
        }
      >
        Add combined response
      </Button>
      <label>
        Automatic-marking readiness
        <select
          value={part.assessmentReadiness ?? 'unreviewed'}
          onChange={(e) =>
            onChange({
              ...part,
              assessmentReadiness: e.target
                .value as ReviewPart['assessmentReadiness'],
            })
          }
        >
          <option value="unreviewed">Rules not checked</option>
          <option value="automatic">
            All scoring rules represented and checked
          </option>
          <option value="manual_only">Manual marking required</option>
        </select>
      </label>
      <label>
        Readiness notes (required for manual marking)
        <Textarea
          value={part.assessmentReadinessReason ?? ''}
          onChange={(e) =>
            onChange({ ...part, assessmentReadinessReason: e.target.value })
          }
        />
      </label>
      <p>
        Only confirm automatic marking when every scheme restriction is
        represented. Content can be approved while marking rules remain
        unchecked.
      </p>
    </fieldset>
  );
}
