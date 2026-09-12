export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}
export function errorMessage(error: unknown) {
  return error instanceof Error
    ? error.message
    : 'Something went wrong. Please try again.';
}
const fieldLabels: Record<string, string> = {
  username: 'Username',
  name: 'Full name',
  password: 'Password',
  parentId: 'Parent account',
  progression: 'Grade and Term progression',
  subjects: 'Subjects',
  newPassword: 'New password',
};
function apiErrorMessage(data: unknown) {
  if (!data || typeof data !== 'object')
    return 'The server could not process the request.';
  if ('error' in data && typeof data.error === 'string') return data.error;
  if ('detail' in data && typeof data.detail === 'string') return data.detail;
  if ('detail' in data && Array.isArray(data.detail)) {
    return data.detail
      .map((item) => {
        if (!item || typeof item !== 'object') return '';
        const location =
          'loc' in item && Array.isArray(item.loc) ? item.loc : [];
        const key = String(location.at(-1) ?? 'request');
        const label = fieldLabels[key] ?? key;
        const message =
          'msg' in item && typeof item.msg === 'string'
            ? item.msg.replace(/^Value error,\s*/i, '')
            : 'is invalid';
        return `${label}: ${message}`;
      })
      .filter(Boolean)
      .join(' ');
  }
  return 'The server could not process the request.';
}
export type Lesson = { explanation: string; points: string[]; hints: string[] };
export type FileRef = { id: string; name: string };
export type UiFeaturesAccess = {
  allowed: true;
  user: { name: string; role: 'admin' };
};
type ApiResult<P extends string> = P extends 'state'
  ? State
  : P extends 'admin/ui-features'
    ? UiFeaturesAccess
    : P extends `lesson${string}`
      ? Lesson
      : P extends 'hint'
        ? { hint: string; total: number }
        : P extends 'attempt'
          ? Attempt
          : P extends 'upload'
            ? FileRef
            : P extends `exams/${string}`
              ? Exam
              : unknown;
export async function api<P extends string>(
  path: P,
  body?: unknown,
): Promise<ApiResult<P>> {
  const csrfToken =
    typeof document === 'undefined'
      ? ''
      : decodeURIComponent(
          document.cookie
            .split('; ')
            .find((value) => value.startsWith('akuru_csrf='))
            ?.slice('akuru_csrf='.length) ?? '',
        );
  const headers: Record<string, string> = {};
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (body !== undefined && csrfToken) headers['X-CSRF-Token'] = csrfToken;
  const response = await fetch('/api/v1/' + path, {
    method: body === undefined ? 'GET' : 'POST',
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const raw = response.status === 204 ? '' : await response.text();
  let data: unknown = {};
  if (raw) {
    try {
      data = JSON.parse(raw);
    } catch {
      data = { detail: 'The server returned an unreadable response.' };
    }
  }
  if (!response.ok) {
    throw new ApiError(apiErrorMessage(data), response.status);
  }
  return data as ApiResult<P>;
}
export async function upload(
  file: File,
  extra: Record<string, string> = {},
): Promise<FileRef> {
  if (file.size > 5 * 1024 * 1024)
    throw new Error('Choose a file smaller than 5 MB.');
  const data = await new Promise<string>((resolve, reject) => {
    const r = new FileReader();
    r.onload = () =>
      typeof r.result === 'string'
        ? resolve(r.result)
        : reject(new Error('Could not read this file.'));
    r.onerror = () => reject(new Error('Could not read this file.'));
    r.readAsDataURL(file);
  });
  return api('upload', { name: file.name, data, purpose: 'working', ...extra });
}
export type Subject = {
  id: string;
  name: string;
  symbol: string;
  color: string;
  topic: string;
  topics: string[];
  course: string;
};
export type Student = {
  parentId: string;
  username: string;
  term: string;
  progression: { grade: string; term: string }[];
  needsConfiguration?: boolean;
  id: string;
  name: string;
  initial: string;
  grade: string;
  level: string;
  subjects: string[];
  courses: Record<string, { level: string; syllabus: string }>;
};
export type Question = {
  unitIds?: string[];
  course?: string;
  id: string;
  subject: string;
  topic: string;
  title: string;
  prompt: string;
  marks: number;
  type: string;
  unit?: string;
  diagram: string;
  source: string;
};
export type Attempt = {
  id: string;
  studentId: string;
  subject: string;
  questionId: string;
  title: string;
  answer: string;
  fileId: string;
  hints: number;
  mark: number | null;
  maxMarks: number;
  status: string;
  feedback: string;
  explanation: string;
  points: string[];
  createdAt: string;
  examId?: string;
};
export type Assignment = {
  id: string;
  studentId: string;
  subject: string;
  title: string;
  due: string;
  questionId: string;
  completed: boolean;
};
export type Doc = {
  course: string;
  textbookId?: string;
  paperId?: string;
  legacy?: boolean;
  id: string;
  name: string;
  subject: string;
  kind: string;
  status: string;
  notes: string;
};
export type Exam = {
  id: string;
  studentId: string;
  subject: string;
  status: string;
  startedAt: string;
  endsAt: string;
  questionIds: string[];
  answers: Record<string, string>;
  files: Record<string, string>;
};
export type State = {
  catalog: {
    courses: string[];
    activeCourses: string[];
    grades: string[];
    terms: string[];
    kinds: string[];
    progressionPairs: { grade: string; term: string }[];
  };
  accounts: { id: string; username: string; name: string; role: string }[];
  units: Unit[];
  coverage: Coverage[];
  questionBank: BankQuestion[];
  drafts: Record<string, string>;
  user: {
    id: string;
    username: string;
    name: string;
    role: string;
    mustChangePassword: boolean;
  };
  subjects: Subject[];
  questions: Question[];
  students: Student[];
  attempts: Attempt[];
  assignments: Assignment[];
  documents: Doc[];
  exams: Exam[];
  reviews: {
    id: string;
    studentId: string;
    feedback: string;
    createdAt: string;
  }[];
  plans: Record<
    string,
    {
      updatedAt: string;
      items: {
        subject: string;
        topic: string;
        minutes: number;
        reason: string;
      }[];
    }
  >;
};
export type Unit = {
  id: string;
  textbookId: string;
  subject: string;
  course: string;
  code: string;
  title: string;
};
export type Coverage = {
  course: string;
  subject: string;
  grade: string;
  term: string;
  unitIds: string[];
};
export type BankQuestion = Question & {
  paperId: string;
  number: string;
  status: string;
  unitIds: string[];
  explanation: string;
  points: string[];
  hints: string[];
  answer: number | null;
};
