/** Reads the same-site token used to protect state-changing API requests. */
export function csrfToken(): string {
  return typeof document === 'undefined'
    ? ''
    : decodeURIComponent(
        document.cookie
          .split('; ')
          .find((value) => value.startsWith('akuru_csrf='))
          ?.slice('akuru_csrf='.length) ?? '',
      );
}
