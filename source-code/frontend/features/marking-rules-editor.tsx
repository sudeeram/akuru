import { useState } from 'react';
import { DeterministicRulesEditor } from './deterministic-rules-editor';
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
        separate. Score bands award only the highest matched alternative. Dependencies,
        follow-through and conditional zero-score rules combined with bands
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
      <fieldset>
        <legend>Calculation score bands</legend>
        <p>
          Create a separate marking point for each score outcome (for example,
          FULL for the correct result and PARTIAL for scheme-approved working or
          rounding errors). Reference those codes below. No matching band earns
          zero; matching both awards only the higher score. Equivalent notation
          belongs in the same criterion, not a separate additive point.
        </p>
        {(rules.scoreBands ?? []).map((group, i) => (
          <fieldset key={i}>
            <legend>Score-band group {i + 1}</legend>
            <label>
              Score-band group name
              <Input value={group.id} onChange={(e) => update({ ...rules,
                scoreBands: rules.scoreBands?.map((g, j) => j === i ? { ...g, id: e.target.value } : g),
              })} />
            </label>
            {group.bands.map((band, k) => (
              <div key={k}>
                <label>
                  Criterion point code
                  <select value={band.pointId} onChange={(e) => update({ ...rules,
                    scoreBands: rules.scoreBands?.map((g, j) => j === i ? { ...g,
                      bands: g.bands.map((b, n) => n === k ? { ...b, pointId: e.target.value } : b),
                    } : g),
                  })}>
                    <option value="">Choose a marking point</option>
                    {part.markingPoints.map((point) => <option key={point.code} value={point.code}>{point.code} — {point.text}</option>)}
                  </select>
                </label>
                <label>
                  Marks for this band
                  <Input type="number" min={1} max={part.marks} value={band.marks}
                    onChange={(e) => update({ ...rules,
                      scoreBands: rules.scoreBands?.map((g, j) => j === i ? { ...g,
                        bands: g.bands.map((b, n) => n === k ? { ...b, marks: Number(e.target.value) } : b),
                      } : g),
                    })} />
                </label>
                <Button variant="outline" onClick={() => update({ ...rules,
                  scoreBands: rules.scoreBands?.map((g, j) => j === i ? { ...g,
                    bands: g.bands.filter((_, n) => n !== k),
                  } : g),
                })}>Remove band</Button>
              </div>
            ))}
            <Button variant="outline" onClick={() => update({ ...rules,
              scoreBands: rules.scoreBands?.map((g, j) => j === i ? { ...g,
                bands: [...g.bands, { pointId: '', marks: 1 }],
              } : g),
            })}>Add band</Button>
            <Button variant="outline" onClick={() => update({ ...rules,
              scoreBands: rules.scoreBands?.filter((_, j) => j !== i),
            })}>Remove score-band group</Button>
          </fieldset>
        ))}
        <Button variant="outline" disabled={part.marks < 2} onClick={() => update({ ...rules, version: 2,
          scoreBands: [...(rules.scoreBands ?? []), {
            id: `calculation-${(rules.scoreBands?.length ?? 0) + 1}`,
            bands: [{ pointId: '', marks: part.marks }, { pointId: '', marks: 1 }],
          }],
        })}>Add calculation score bands</Button>
      </fieldset>
      <details>
        <summary>Optional validated scoring configuration</summary>
        <p>Not required for Tutor practice. Approved content can receive indicative AI feedback without certification.</p>
      <DeterministicRulesEditor part={part} onChange={onChange} />
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
          <option value="automatic" disabled={!!rules.deterministic && !rules.deterministic.certificateId}>
            All scoring rules represented and checked
          </option>
          <option value="manual_only">Indicative AI feedback (no scoring certificate)</option>
        </select>
      </label>
      <label>
        Scoring implementation notes
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
      </details>
    </fieldset>
  );
}
