/** Decorative category colours, deliberately separate from semantic status tones. */
export type SubjectAccent =
  | 'blue'
  | 'teal'
  | 'violet'
  | 'amber'
  | 'coral'
  | 'neutral';
const accents: Readonly<Record<string, SubjectAccent>> = {
  maths: 'blue',
  science: 'teal',
  biology: 'teal',
  chemistry: 'violet',
  physics: 'amber',
  english: 'coral',
  french: 'coral',
  'human-biology': 'teal',
  ict: 'violet',
};
export function subjectAccent(subjectId?: string): SubjectAccent {
  return subjectId && Object.hasOwn(accents, subjectId)
    ? accents[subjectId]
    : 'neutral';
}
