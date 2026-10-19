'use client';
import { useState } from 'react';
import { RotateCcw, Shuffle, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { EditorDrawer } from '@/components/portal/workspace';
import { StudentAvatar } from '@/components/portal/student-avatar';
import {
  errorMessage,
  saveStudentAvatar,
  resetStudentAvatar,
  type AvatarConfig,
  type AvatarField,
} from '@/api';
import {
  avatarCatalogue,
  avatarPresets,
  surpriseAvatar,
} from '@/lib/student-avatar';

const groups = [
  { id: 'face', label: 'Face & skin', fields: ['face', 'skin'] },
  { id: 'hair', label: 'Hair', fields: ['hair', 'hairColor'] },
  { id: 'eyes', label: 'Eyes & brows', fields: ['eyes', 'eyeColor', 'brows'] },
  { id: 'expression', label: 'Expression', fields: ['mouth'] },
  {
    id: 'style',
    label: 'Clothes & glasses',
    fields: ['outfit', 'clothesColor', 'glasses'],
  },
  { id: 'background', label: 'Background', fields: ['background'] },
] as const;
const fieldLabels: Record<string, string> = {
  face: 'Face shape',
  skin: 'Skin tone',
  hair: 'Hairstyle',
  hairColor: 'Hair colour',
  eyes: 'Eye shape',
  eyeColor: 'Eye colour',
  brows: 'Eyebrows',
  mouth: 'Expression',
  outfit: 'Outfit',
  clothesColor: 'Clothing colour',
  glasses: 'Glasses',
  background: 'Background colour',
};
export function StudentAvatarEditor({
  current,
  onClose,
  onSaved,
  savePreview,
}: {
  current: AvatarConfig | null;
  onClose: () => void;
  onSaved: (value: AvatarConfig | null) => void;
  /** Used only by the labelled Admin design preview; real profiles use the authenticated API. */
  savePreview?: (value: AvatarConfig | null) => Promise<void>;
}) {
  const [draft, setDraft] = useState<AvatarConfig>(() => ({
    ...(current || avatarPresets[0]),
  }));
  const [category, setCategory] =
    useState<(typeof groups)[number]['id']>('face');
  const [busy, setBusy] = useState(false),
    [error, setError] = useState('');
  const dirty =
    JSON.stringify(draft) !== JSON.stringify(current || avatarPresets[0]);
  const choose = (field: AvatarField, value: string) => {
    setDraft((previous) => ({ ...previous, [field]: value }));
    setError('');
  };
  async function save(remove = false) {
    setBusy(true);
    setError('');
    try {
      if (savePreview) await savePreview(remove ? null : draft);
      else if (remove) await resetStudentAvatar();
      else await saveStudentAvatar(draft);
      onSaved(remove ? null : draft);
      onClose();
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  }
  return (
    <EditorDrawer
      open
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
      title={current ? 'Edit your avatar' : 'Create your avatar'}
      description={
        savePreview
          ? 'Design preview only — no account changes are saved.'
          : 'Start with a character, then make it your own.'
      }
      dirty={dirty}
      busy={busy}
    >
      <div className="avatar-editor" aria-busy={busy}>
        <section className="avatar-preview" aria-label="Avatar preview">
          <StudentAvatar avatar={draft} label="Your avatar preview" />
          <p>Made for your AKURU learning journey</p>
          <div className="button-row">
            <Button
              variant="outline"
              disabled={busy}
              onClick={() => {
                setDraft(surpriseAvatar());
                setError('');
              }}
            >
              <Shuffle size={16} />
              Surprise me
            </Button>
            <Button
              variant="ghost"
              disabled={busy}
              onClick={() => {
                setDraft({ ...(current || avatarPresets[0]) });
                setError('');
              }}
            >
              <RotateCcw size={15} />
              Reset draft
            </Button>
          </div>
        </section>
        <fieldset className="avatar-bases" disabled={busy}>
          <legend>Choose a starting character</legend>
          <div>
            {avatarPresets.map((preset, index) => (
              <button
                type="button"
                key={preset.base}
                aria-pressed={draft.base === preset.base}
                aria-label={`Start with character ${index + 1}`}
                onClick={() => {
                  setDraft({ ...preset });
                  setError('');
                }}
              >
                <StudentAvatar avatar={preset} />
                <span>Base 0{index + 1}</span>
              </button>
            ))}
          </div>
          <p>Every feature is available for every character.</p>
        </fieldset>
        <fieldset className="avatar-categories">
          <legend className="sr-only">Customisation categories</legend>
          {groups.map((group) => (
            <Button
              key={group.id}
              variant={category === group.id ? 'default' : 'outline'}
              aria-pressed={category === group.id}
              onClick={() => setCategory(group.id)}
            >
              {group.label}
            </Button>
          ))}
        </fieldset>
        <div className="avatar-options">
          {groups
            .find((group) => group.id === category)!
            .fields.map((field) => (
              <fieldset disabled={busy} key={field}>
                <legend>{fieldLabels[field]}</legend>
                <div className="avatar-option-grid">
                  {Object.entries(avatarCatalogue.options[field]).map(
                    ([value, option]) => {
                      const color =
                        'color' in option ? String(option.color) : undefined;
                      return (
                        <button
                          type="button"
                          key={value}
                          aria-label={`${fieldLabels[field]}: ${option.label}`}
                          aria-pressed={draft[field] === value}
                          onClick={() => choose(field, value)}
                        >
                          {color ? (
                            <span
                              className="avatar-colour"
                              style={{ backgroundColor: color }}
                            />
                          ) : (
                            <StudentAvatar
                              avatar={{ ...draft, [field]: value }}
                            />
                          )}
                          <span>{option.label}</span>
                        </button>
                      );
                    },
                  )}
                </div>
              </fieldset>
            ))}
        </div>
        {error && (
          <p className="error" role="alert">
            {error} Your choices are still here. Try saving again.
          </p>
        )}
        <div className="avatar-save-bar">
          <output aria-live="polite">
            {busy
              ? 'Saving your avatar…'
              : dirty
                ? 'Unsaved avatar changes'
                : 'Ready when you are'}
          </output>
          <div className="button-row">
            <Button
              variant="outline"
              disabled={busy}
              onClick={() => {
                if (!dirty || window.confirm('Discard unsaved avatar changes?'))
                  onClose();
              }}
            >
              Cancel
            </Button>
            <Button disabled={busy} onClick={() => void save()}>
              <Sparkles size={16} />
              {busy
                ? 'Saving…'
                : savePreview
                  ? 'Use in preview'
                  : 'Save avatar'}
            </Button>
          </div>
        </div>
        {current && (
          <Button
            variant="ghost"
            disabled={busy}
            onClick={() => {
              if (
                window.confirm(
                  'Remove your avatar and show your initials instead?',
                )
              )
                void save(true);
            }}
          >
            Remove avatar and use initials
          </Button>
        )}
      </div>
    </EditorDrawer>
  );
}

export function AvatarBuilderPreview() {
  const [avatar, setAvatar] = useState<AvatarConfig | null>(null),
    [open, setOpen] = useState(false);
  return (
    <section className="panel stack avatar-design-demo">
      <h2>AKURU Student avatar builder</h2>
      <p>
        Four original starting characters with interchangeable features. This
        preview does not change an account.
      </p>
      <StudentAvatar
        avatar={avatar}
        fallback="A"
        label="Design preview avatar"
      />
      <Button variant="outline" onClick={() => setOpen(true)}>
        Try the avatar builder
      </Button>
      {open && (
        <StudentAvatarEditor
          current={avatar}
          onClose={() => setOpen(false)}
          onSaved={setAvatar}
          savePreview={async () => {}}
        />
      )}
    </section>
  );
}
