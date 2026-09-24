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
export const fieldLabels: Record<string, string> = {
  username: 'Username',
  name: 'Full name',
  password: 'Password',
  parentId: 'Parent account',
  progression: 'Grade and Term progression',
  subjects: 'Subjects',
  newPassword: 'New password',
};
export function apiErrorMessage(data: unknown) {
  if (!data || typeof data !== 'object')
    return 'The server could not process the request.';
  if ('error' in data && typeof data.error === 'object' && data.error) {
    const error = data.error as {
      message?: unknown;
      details?: unknown;
    };
    if (Array.isArray(error.details) && error.details.length) {
      const messages = error.details
        .map((item) => {
          if (!item || typeof item !== 'object') return '';
          const location =
            'location' in item && Array.isArray(item.location)
              ? item.location
              : [];
          const key = String(location.at(-1) ?? 'request');
          const label = fieldLabels[key] ?? key;
          const message =
            'message' in item && typeof item.message === 'string'
              ? item.message.replace(/^Value error,\s*/i, '')
              : 'is invalid';
          return `${label}: ${message}`;
        })
        .filter(Boolean);
      if (messages.length) return messages.join(' ');
    }
    if (typeof error.message === 'string') return error.message;
  }
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
