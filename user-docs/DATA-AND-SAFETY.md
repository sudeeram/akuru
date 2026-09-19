# AKURU: Data and Current Limits

Admin manages accounts, curriculum and learning documents. Each parent sees
only linked children; students see their own work. Learning resources are
shared by subject after Admin approval. Student answer attachments remain private
to the child, their linked parent and Admin.

The backend stores accounts, enrolments, learning records, reviews and audit
evidence in PostgreSQL. Uploaded learning and answer files use private storage
outside the application checkout. Protect encrypted backups because they contain
family records and private document evidence.

Passwords are stored only as Argon2 hashes. Newly created Parent and Student
accounts must replace their temporary password on first sign-in. AKURU contains
no demo credentials. Sign out on shared devices.

AKURU performs deterministic PDF rendering and OCR on the AKURU server. When an
AI-backed feature is enabled, AKURU may send the minimum authorized textbook
evidence, answer or task context required to the configured OpenAI service.
Provider credentials stay on the backend. Admin review and release gates apply
to extracted learning content, generated flashcards, assessment feedback and
conceptual media according to the feature.

Automated marking can make mistakes, particularly with handwriting, ambiguous
answers and method marks. Low-confidence results require review. Scores are not
predicted grades. Course names and subject settings do not certify content as
official Edexcel material. Use only resources the family is entitled to store
and study.

The production service uses HTTPS, private database and storage services,
role-based access, encrypted backups and audited retention operations. Report an
incorrect family link, unexpected document access or safety concern to the Admin
immediately. Admins should use the Operations page and the procedures in the
developer handbook when investigating incidents or processing deletion requests.
