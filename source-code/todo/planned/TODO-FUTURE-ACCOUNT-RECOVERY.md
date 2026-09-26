# Future Parent-assisted and self-service account recovery

**Status:** Planned for a future phase.

This roadmap begins only after the Admin-managed password lifecycle in
`TODO-ACCOUNT-PASSWORD-LIFECYCLE.md` is complete. It adds recovery requests and
verified communication channels without weakening family separation.

## Future Step 1 — Parent requests for linked-child password resets

- [ ] Allow an authenticated Parent to request a reset only for a Student
  currently linked to that Parent.
- [ ] Keep reset execution with an Admin initially; a request must not change a
  password or revoke sessions by itself.
- [ ] Give Admins a queue showing the requesting Parent, linked Student, request
  time, status and non-sensitive reason.
- [ ] Prevent duplicate open requests and rate-limit repeated submissions.
- [ ] Notify the Parent when the request is approved, rejected or completed
  without sending a password through an insecure notification channel.
- [ ] Audit request, review and completion events without credentials.
- [ ] Test family isolation so a Parent cannot discover or request a reset for
  any unrelated Student.

**Acceptance:** a Parent can ask for help with a linked child's account while
an Admin retains control of the secure one-time temporary-password handover.

## Future Step 2 — Establish verified recovery contacts

- [ ] Add verified email addresses for eligible accounts with uniqueness,
  normalization and change-verification rules.
- [ ] Decide whether Students recover through their linked Parent, their own
  verified address at an appropriate age, or both.
- [ ] Add a production email provider, delivery monitoring and privacy-safe
  templates.
- [ ] Never expose a partially masked email unless the requester has already
  authenticated and is authorized to see it.
- [ ] Provide Admin support procedures for lost or changed recovery contacts.

**Acceptance:** AKURU has a verified, privacy-reviewed delivery destination
before enabling self-service recovery.

## Future Step 3 — Add expiring one-time recovery tokens

- [ ] Generate cryptographically secure, single-use reset tokens and store only
  a hash of each token.
- [ ] Bind each token to one account, purpose and expiration time.
- [ ] Invalidate earlier tokens when a newer request is accepted, after use, or
  after an Admin reset or successful password change.
- [ ] Use a generic response for known and unknown account identifiers.
- [ ] Apply strict request, token-validation and password-submission rate
  limits.
- [ ] Prevent tokens from leaking through logs, analytics, referrer headers or
  frontend persistence.
- [ ] Revoke all account sessions after a successful self-service reset and
  notify the verified recovery contact.

**Acceptance:** a captured, expired, reused or superseded token cannot reset an
account, and the workflow does not reveal whether an account exists.

## Future Step 4 — UX, safety and release evaluation

- [ ] Build accessible Forgot password, Check your email, Invalid or expired
  link and Set a new password screens.
- [ ] Use the same password policy and session-revocation behavior as the
  Admin-managed lifecycle.
- [ ] Add abuse monitoring for request floods, token guessing and delivery
  anomalies.
- [ ] Test account enumeration, timing behavior, token replay, family
  separation, email changes and concurrent reset attempts.
- [ ] Update privacy information, user documentation and operational support
  procedures before release.
- [ ] Pilot with Admin and selected Parent accounts before enabling it for the
  wider AKURU audience.

**Done when:** verified users can recover access without Admin intervention and
the security, privacy and family-isolation release gates pass.

