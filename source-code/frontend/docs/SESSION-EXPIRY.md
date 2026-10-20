# Session-expiry login recovery

20 October 2026. Frontend-only fix for expired sessions leaving the portal visible or displaying a raw fetch error.

## Behavior

- Confirmed HTTP 401 responses from authenticated JSON requests trigger the existing shared expiry event before reading the body. A failed response-body read therefore cannot disguise a confirmed expiry as “Failed to fetch”.
- The portal's state query handles its own 401: an authenticated refresh expires the session, while an initial signed-out protected-page visit redirects to `/login`. Login validation errors remain on the sign-in form.
- Expiry immediately hides authenticated content, clears private query data and stale error/notice/password state, and replaces the URL with `/login`. Repeated expiry events are coalesced. Late feature errors are not shown over the expiry explanation.
- The original authorized destination is retained in component memory and validated against the newly signed-in role before returning there. Explicit sign-out resets that destination. Nothing is persisted in browser storage, and no password or draft is put in the URL.
- While authenticated and visible, the portal checks existing `/auth/me` on focus/visibility return and once per minute. It never changes the backend's fixed expiry policy. Auth checks use `cache: no-store`.
- Network failures and 5xx responses are not proof of expiry: they do not sign out the user. Network failures have a readable connection/retry message. Requests from an older login generation cannot expire a newly authenticated identity.
- Manual logout reports recoverable connection failures and handles an already-expired session through the same redirect path.

## Validation

97 frontend tests pass, including seven executable API-client regressions: 401 with an unreadable body, typed state 401, invalid login, offline request, interrupted successful body, server/success response, and a late old-session 401 after a new login. Typecheck, lint and build pass.

Local browser acceptance uses a disposable development-only Admin account and expiration of only that account's session records. Signed-out `/admin/profile` redirects to `/login`; successful sign-in restores `/admin/profile`. A real expired local session redirected from `/admin/profile` to `/login` without a page reload, showed the expiry explanation, cleared the password and removed the private portal without a raw fetch error. Reauthentication restored `/admin/profile`; manual sign-out returned to a clean login form. Incorrect credentials retained their validation message. A stale dev hot-reload blank-page artifact cleared after restarting the identified development server; the clean-start redirect and form render passed.

No backend code, API contract, expiry duration, database schema or dependency changes. Existing unrelated sidebar hover edits are excluded.
