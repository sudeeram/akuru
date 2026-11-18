import { useId } from 'react';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
export type AnswerFormat = {
  engine: string;
  fields: string[];
  allowWorking: boolean;
};
export function DeterministicAnswerInput({
  format,
  value,
  onChange,
  disabled,
}: {
  format: AnswerFormat;
  value: string;
  onChange: (s: string) => void;
  disabled?: boolean;
}) {
  const controlId = useId();
  let decoded: Record<string, unknown> = {};
  try {
    const parsed = JSON.parse(value);
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed))
      decoded = parsed;
  } catch {
    /* Bare single final answer is a supported format. */
  }
  const single = format.fields.length === 1 && format.fields[0] === '';
  const read = (key: string) => {
    const v = single
      ? Object.hasOwn(decoded, 'final')
        ? decoded
        : value
      : decoded[key];
    return typeof v === 'string'
      ? { final: v, working: [] as string[] }
      : v && typeof v === 'object'
        ? (v as { final: string; working?: string[] })
        : { final: '', working: [] as string[] };
  };
  const write = (
    key: string,
    patch: { final?: string; working?: string[] },
  ) => {
    const updated = { ...read(key), ...patch };
    if (single)
      onChange(
        updated.working?.length ? JSON.stringify(updated) : updated.final,
      );
    else
      onChange(
        JSON.stringify({
          ...decoded,
          [key]: format.allowWorking ? updated : updated.final,
        }),
      );
  };
  return (
    <fieldset className="stack">
      <legend>Final answer{format.fields.length > 1 ? 's' : ''}</legend>
      <p>
        Use the labelled fields below. If an answer cannot be recognised
        reliably, it will be referred for review rather than guessed.
      </p>
      {format.fields.map((key) => (
        <div key={key} className="stack">
          <label htmlFor={`${controlId}-${key}`} className="stack">
            {key || 'Final answer'}
            <Input
              id={`${controlId}-${key}`}
              disabled={disabled}
              value={read(key).final}
              onChange={(e) => write(key, { final: e.target.value })}
            />
          </label>
          {format.allowWorking && (
            <label htmlFor={`${controlId}-${key}-working`} className="stack">
              Arithmetic working (one expression per line)
              <Textarea
                id={`${controlId}-${key}-working`}
                disabled={disabled}
                value={read(key).working?.join('\n') ?? ''}
                onChange={(e) =>
                  write(key, { working: e.target.value.split('\n') })
                }
              />
            </label>
          )}
        </div>
      ))}
    </fieldset>
  );
}
