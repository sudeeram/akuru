# AKURU: Getting Started

For the hosted service, open the AKURU address supplied by the Admin. For local
development, the person managing the computer starts PostgreSQL, Redis, FastAPI,
the document worker and the portal, then opens `http://127.0.0.1:5180/`.

Sign in with the account created for you by an AKURU Admin. On your first
sign-in, replace the temporary password before entering the portal. There are
no demo accounts or passwords. Sign out on shared computers.

## Admin first login

1. Open Accounts & enrolments. Create a parent account before its child accounts.
2. Set each child's iGCSE subjects, Grade 10 or 11, and Grade + Term progression.
   For a Grade 10 Term2 student, select Grade 10 Term1 and Grade 10 Term2.
3. Confirm migrated learners marked as requiring configuration.
4. Follow the [Admin guide](ADMIN-GUIDE.md) to prepare textbook groups, topics, term coverage and questions.

## Parent first login

1. Check the children linked to your account in Family overview.
2. View Children & courses. Ask Admin to correct any grade, term or subject.
3. Use Assessment reviews and Assignments for your own children.

## Student first login

1. Check your name, current grade and term. Earlier completed terms are used
   when selecting mock questions.
2. Open My subjects. Tell Admin or your parent if your enrolment is wrong.
3. Start practice when approved questions are available for your covered topics.

An empty question list is expected until Admin completes curriculum setup.
The portal does not fill an empty term with questions from untaught units.

If the page cannot open, check that the server is running and the port is right.
If sign-in fails, confirm that FastAPI is running on port 8000 and PostgreSQL is
available. Sessions are stored by the backend and expire automatically.
