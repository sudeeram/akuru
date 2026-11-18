/* eslint-disable jsx-a11y/label-has-associated-control */
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import type {
  ReviewPart,
  DeterministicMatcher,
} from '@/api/assessments/official-paper-review.api';
const lines = (s: string) =>
  s
    .split('\n')
    .map((v) => v.trim())
    .filter(Boolean);
function LinesInput({
  value,
  onChange,
}: {
  value: string[];
  onChange: (v: string[]) => void;
}) {
  const serialized = value.join('\n');
  const [draft, setDraft] = useState(serialized);
  return (
    <Textarea
      value={draft}
      onChange={(e) => setDraft(e.target.value)}
      onBlur={() => onChange(lines(draft))}
    />
  );
}
export function DeterministicRulesEditor({
  part,
  onChange,
}: {
  part: ReviewPart;
  onChange: (p: ReviewPart) => void;
}) {
  const config = part.scoringRules?.deterministic;
  const set = (matchers: DeterministicMatcher[]) =>
    onChange({
      ...part,
      assessmentReadiness: 'unreviewed',
      scoringRules: {
        ...part.scoringRules!,
        version: 3,
        deterministic: {
          engine: 'deterministic-v1',
          matchers,
          certificateId: null,
        },
      },
    });
  const update = (i: number, patch: Partial<DeterministicMatcher>) =>
    set(config!.matchers.map((m, j) => (i === j ? { ...m, ...patch } : m)));
  return (
    <fieldset className="stack">
      <legend>Answer recognition without model calls</legend>
      <p>
        Only bounded numeric, fixed-choice and reviewed member-set answers are
        supported. Unknown wording or conflicting final answers require review.
        These rules do not enable scoring until the server validates them.
      </p>
      {!config ? (
        <Button
          variant="outline"
          onClick={() =>
            set(
              part.markingPoints.map((p) => ({
                pointId: p.code,
                kind: 'choice',
                accepted: [],
                rejected: [],
              })),
            )
          }
        >
          Configure deterministic recognition
        </Button>
      ) : (
        <>
          <p>
            Engine: {config.engine} ·{' '}
            {config.certificateId
              ? 'Validation receipt recorded; see current history below.'
              : 'Validation required'}
          </p>
          {config.matchers.map((m, i) => (
            <fieldset key={i} className="stack">
              <legend>{m.pointId}</legend>
              <p>
                {part.markingPoints.find((p) => p.code === m.pointId)?.text}
              </p>
              <label>
                Answer field label (leave empty for a single final answer)
                <Input
                  value={m.answerKey ?? ''}
                  onChange={(e) => update(i, { answerKey: e.target.value })}
                />
              </label>
              <label>
                Recognition type
                <select
                  value={m.kind}
                  onChange={(e) =>
                    update(i, {
                      kind: e.target.value as DeterministicMatcher['kind'],
                      values: [],
                      accepted: [],
                      rejected: [],
                      methods: [],
                      units: [],
                      requiredMembers: [],
                      extraMembers: [],
                    })
                  }
                >
                  <option value="choice">Fixed choice or name</option>
                  <option value="numeric">Numeric result</option>
                  <option value="set">Required member set</option>
                </select>
              </label>
              {m.kind === 'set' ? (
                <>
                  <p>
                    All required members must appear; any known extra member
                    earns no credit. Unknown wording is referred for review.
                  </p>
                  {(m.requiredMembers ?? []).map((aliases, k) => (
                    <label key={k}>
                      Required member {k + 1} aliases
                      <LinesInput
                        key={aliases.join('\n')}
                        value={aliases}
                        onChange={(v) =>
                          update(i, {
                            requiredMembers: m.requiredMembers!.map((x, j) =>
                              j === k ? v : x,
                            ),
                          })
                        }
                      />
                    </label>
                  ))}
                  <Button
                    variant="outline"
                    onClick={() =>
                      update(i, {
                        requiredMembers: [...(m.requiredMembers ?? []), []],
                      })
                    }
                  >
                    Add required member
                  </Button>
                  <label>
                    Recognised extra members
                    <LinesInput
                      key={(m.extraMembers ?? []).join('\n')}
                      value={m.extraMembers ?? []}
                      onChange={(extraMembers) => update(i, { extraMembers })}
                    />
                  </label>
                </>
              ) : m.kind === 'choice' ? (
                <>
                  <label>
                    Accepted aliases — one per line
                    <LinesInput
                      key={(m.accepted ?? []).join('\n')}
                      value={m.accepted ?? []}
                      onChange={(accepted) => update(i, { accepted })}
                    />
                  </label>
                  <label>
                    Recognised incorrect choices — one per line
                    <LinesInput
                      key={(m.rejected ?? []).join('\n')}
                      value={m.rejected ?? []}
                      onChange={(rejected) => update(i, { rejected })}
                    />
                  </label>
                </>
              ) : (
                <>
                  {(m.values ?? []).map((v, k) => (
                    <fieldset key={k}>
                      <legend>Allowed numeric outcome {k + 1}</legend>
                      <label>
                        Exact value or reviewed fraction
                        <Input
                          value={v.value}
                          onChange={(e) =>
                            update(i, {
                              values: m.values!.map((x, j) =>
                                j === k ? { ...x, value: e.target.value } : x,
                              ),
                            })
                          }
                        />
                      </label>
                      <label>
                        Significant figures (optional)
                        <Input
                          type="number"
                          min={1}
                          max={15}
                          value={v.significantFigures ?? ''}
                          onChange={(e) =>
                            update(i, {
                              values: m.values!.map((x, j) =>
                                j === k
                                  ? {
                                      ...x,
                                      significantFigures: e.target.value
                                        ? Number(e.target.value)
                                        : null,
                                    }
                                  : x,
                              ),
                            })
                          }
                        />
                      </label>
                      <label>
                        Decimal places (optional)
                        <Input
                          type="number"
                          min={0}
                          max={20}
                          value={v.decimalPlaces ?? ''}
                          onChange={(e) =>
                            update(i, {
                              values: m.values!.map((x, j) =>
                                j === k
                                  ? {
                                      ...x,
                                      decimalPlaces: e.target.value
                                        ? Number(e.target.value)
                                        : null,
                                    }
                                  : x,
                              ),
                            })
                          }
                        />
                      </label>
                      <label>
                        <input
                          type="checkbox"
                          checked={v.roundedFrom ?? false}
                          onChange={(e) =>
                            update(i, {
                              values: m.values!.map((x, j) =>
                                j === k
                                  ? { ...x, roundedFrom: e.target.checked }
                                  : x,
                              ),
                            })
                          }
                        />
                        Source authorises rounded/truncated forms of this value
                      </label>
                      <label>
                        <input type="checkbox" checked={v.allowPowerOfTenScaling ?? false}
                          onChange={e => update(i, {values: m.values!.map((x,j) => j === k ? {...x, allowPowerOfTenScaling:e.target.checked} : x)})} />
                        Source permits the same significand at an incorrect power-of-ten scale
                      </label>
                      {v.roundedFrom && (
                        <label>
                          Minimum significant figures
                          <Input
                            type="number"
                            min={1}
                            max={15}
                            value={v.minimumSignificantFigures ?? 1}
                            onChange={(e) =>
                              update(i, {
                                values: m.values!.map((x, j) =>
                                  j === k
                                    ? {
                                        ...x,
                                        minimumSignificantFigures: Number(
                                          e.target.value,
                                        ),
                                      }
                                    : x,
                                ),
                              })
                            }
                          />
                        </label>
                      )}
                      <Button
                        variant="outline"
                        onClick={() =>
                          update(i, {
                            values: m.values!.filter((_, j) => j !== k),
                          })
                        }
                      >
                        Remove numeric outcome
                      </Button>
                    </fieldset>
                  ))}
                  <Button
                    variant="outline"
                    onClick={() =>
                      update(i, {
                        values: [...(m.values ?? []), { value: '' }],
                      })
                    }
                  >
                    Add numeric outcome
                  </Button>
                  <label>
                    Approved units — one per line
                    <LinesInput
                      key={(m.units ?? []).join('\n')}
                      value={m.units ?? []}
                      onChange={(units) => update(i, { units })}
                    />
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      checked={m.allowMissingUnit ?? true}
                      onChange={(e) =>
                        update(i, { allowMissingUnit: e.target.checked })
                      }
                    />
                    Scheme permits omission of a supplied unit
                  </label>
                  <label>Explicitly recognised zero-credit final values
                    <LinesInput key={(m.incorrectValues ?? []).join('\n')} value={m.incorrectValues ?? []} onChange={incorrectValues => update(i, {incorrectValues})} />
                  </label>
                  {!!m.methods?.length && (
                    <details>
                      <summary>
                        Source-authorised working stages (prepared through API)
                      </summary>
                      {m.methods.map((step, j) => (
                        <p key={j}>
                          {step.operator} by {step.right}; allowed left values:{' '}
                          {step.allowAnyLeft ? 'any bounded left operand (explicit source allowance)' : step.leftValues.join(', ')}
                        </p>
                      ))}
                    </details>
                  )}
                </>
              )}
            </fieldset>
          ))}
          <Button
            variant="outline"
            onClick={() =>
              set(
                part.markingPoints.map(
                  (p) =>
                    config.matchers.find((m) => m.pointId === p.code) ?? {
                      pointId: p.code,
                      kind: 'choice',
                      accepted: [],
                      rejected: [],
                    },
                ),
              )
            }
          >
            Synchronise criteria with marking point codes
          </Button>
          <Button
            variant="outline"
            onClick={() =>
              onChange({
                ...part,
                assessmentReadiness: 'unreviewed',
                scoringRules: { ...part.scoringRules!, deterministic: null },
              })
            }
          >
            Remove deterministic recognition
          </Button>
        </>
      )}
    </fieldset>
  );
}
