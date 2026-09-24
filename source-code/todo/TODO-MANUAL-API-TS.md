# Manual `api.ts` refactor

**Status: Completed on 21 September 2026.** The former `frontend/lib/api.ts` was replaced by the domain modules below, React imports now use `@/api`, and the API contract check, tests, type checking, linting and production build passed.

Refactor the current large TypeScript API client file (`api.ts`) into multiple smaller files so the code is easier for a human reviewer to understand and maintain. Also add descriptive, informative comments so it is easier for human reviewers, but don't make them too lengthy.

The current file mixes:
- shared HTTP request logic
- CSRF handling
- API error handling
- tutoring APIs and types
- document APIs and types
- textbook APIs and types
- curriculum APIs and types
- assessment APIs and types
- flashcard APIs and types
- mastery types
- state types
- upload logic
- realtime tutor logic
- document extraction logic

Please refactor it by domain.

Target structure:

```text
src/api/
├── core/
│   ├── client.ts
│   ├── errors.ts
│   └── csrf.ts
│
├── tutoring/
│   ├── tutor.api.ts
│   └── tutor.types.ts
│
├── documents/
│   ├── documents.api.ts
│   └── documents.types.ts
│
├── textbooks/
│   ├── textbooks.api.ts
│   └── textbooks.types.ts
│
├── curriculum/
│   ├── curriculum.api.ts
│   └── curriculum.types.ts
│
├── assessments/
│   ├── assessments.api.ts
│   └── assessments.types.ts
│
├── flashcards/
│   ├── flashcards.api.ts
│   └── flashcards.types.ts
│
├── mastery/
│   └── mastery.types.ts
│
├── state/
│   ├── state.api.ts
│   └── state.types.ts
│
└── index.ts
```

Refactoring requirements:

1. Move the generic HTTP request functionality into:

```text
src/api/core/client.ts
```

Use a generic request function:

```ts
export async function request<T>(
  path: string,
  options: {
    method?: 'GET' | 'POST' | 'PATCH' | 'DELETE';
    body?: unknown;
  } = {},
): Promise<T>
```

The shared client must continue to handle:
- `/api/v1/` path prefix
- GET, POST, PATCH and DELETE
- JSON serialization
- JSON response parsing
- 204 responses
- CSRF headers
- backend API errors
- unreadable backend responses

Prefer:

```ts
request<TutorOptions>('tutoring/options')
```

instead of:

```ts
request('tutoring/options') as Promise<TutorOptions>
```

2. Move CSRF logic into:

```text
src/api/core/csrf.ts
```

Keep the existing behaviour of reading the `akuru_csrf` cookie and returning the CSRF token.

3. Move error handling into:

```text
src/api/core/errors.ts
```

This should contain:
- `ApiError`
- `errorMessage`
- `apiErrorMessage`
- `fieldLabels`

Preserve the current backend validation error handling and user-friendly field labels.

4. Remove the current conditional `ApiResult<P>` type logic if it is no longer required.

Avoid complex type inference such as:

```ts
type ApiResult<P extends string> =
  P extends 'state'
    ? State
    : ...
```

Prefer explicit API return types:

```ts
request<State>('state')
```

and:

```ts
request<CurriculumPlan>(
  `admin/curriculum-plans/${subjectId}`,
)
```

The goal is to favour readability over clever type-level logic.

5. Move all tutoring-related types into:

```text
src/api/tutoring/tutor.types.ts
```

This includes, where applicable:
- TutorAvatar
- TutorVoice
- TutorOptions
- TutorProfileDraft
- TutorProfile
- TutorAdminPresets
- TutorQuota
- TutorQuotaAmount
- TutorQuotaAudit
- TutorHistorySummary
- TutorSafetyEvent
- TutorSessionTopic
- TutorTurn
- TutorSession
- TutorSessionOptions
- NextTopicResult
- TutorCitation
- TutorSourceSearch
- TutorCitationContext
- TutorAgentReply
- TutorPractice
- TutorSignal
- RealtimeCredential
- RealtimeLanguageMode

Move all tutor-related HTTP functions into:

```text
src/api/tutoring/tutor.api.ts
```

This should include:
- tutor profiles
- tutor presets
- tutor quotas
- tutor history
- safety events
- transcript access/purge operations
- realtime credentials/state/transcript
- tutor sessions
- topic/profile switching
- agent turns
- source search
- citation context
- tutor practice
- tutor signals

6. Move document-related types and operations into:

```text
src/api/documents/
```

This includes:
- document upload
- learning document metadata
- document extraction
- extraction pages
- extraction blocks
- document processing jobs
- retry
- deletion
- working upload where appropriate

Keep binary file upload behaviour working exactly as before.

Do not unnecessarily convert binary uploads to JSON or Base64 unless the existing API already requires Base64.

7. Move textbook-related types and operations into:

```text
src/api/textbooks/
```

This includes:
- TextbookStructure
- TextbookStructureGroup
- TextbookStructureTopic
- topic source roles
- topic document sources
- topic quality reports
- topic review checklist
- topic visual assets
- topic launch readiness
- retrieval preflight
- textbook create/update/archive
- group operations
- topic operations
- source role operations
- topic publishing
- visual review
- topic document uploads
- batch topic document uploads
- topic-part suggestions

8. Move curriculum-related code into:

```text
src/api/curriculum/
```

This includes:
- CurriculumPlan
- CurriculumPlanPeriod
- CurriculumPlanTopic
- CurriculumPlanTopicGroup
- get curriculum plan
- save curriculum plan
- create draft
- publish curriculum plan

9. Move past-paper / official-material-related code to the most appropriate domain.

If it fits better under assessments or documents, place it there consistently.

This includes:
- OfficialMaterialReview
- SourceLocation
- get official material review
- propose review
- save review
- publish review
- PaperMappings
- TopicMapping
- question mapping suggestion/save/publish operations

Use domain clarity rather than forcing everything into one file.

10. Move assessment-related types and functions into:

```text
src/api/assessments/
```

This includes:
- Attempt
- AssessmentAudit
- AssessmentApiResponse
- AssessmentResult
- reassessment
- assessment audit
- marking decisions and related types

11. Move flashcard functionality into:

```text
src/api/flashcards/
```

This includes:
- FlashcardSource
- FlashcardCard
- FlashcardDeck
- FlashcardSession
- admin deck APIs
- generation
- review
- release
- student deck APIs
- session start
- reveal
- rating

12. Move mastery-related types into:

```text
src/api/mastery/mastery.types.ts
```

This includes:
- TopicMastery
- MasteryGroup
- ImprovementRecommendation

If there are mastery-specific API calls elsewhere, move them into a matching `mastery.api.ts`.

13. Move global application state types into:

```text
src/api/state/state.types.ts
```

This includes:
- State
- Subject
- Student
- Question
- Assignment
- Exam
- Doc
- BankQuestion
- and other types that are genuinely part of the global application state

If some of these types belong more naturally to another domain, prefer domain ownership and import them into `State`.

Do not duplicate types.

14. Create:

```text
src/api/state/state.api.ts
```

for state-specific API operations.

15. Create:

```text
src/api/index.ts
```

as the public API barrel.

It should re-export the relevant API functions and public types so existing React components can continue to use clean imports such as:

```ts
import {
  startTutorSession,
  getTutorPractice,
  type TutorSession,
} from '@/api';
```

16. Avoid creating one huge shared `types.ts` file.

Types should live with the domain that owns them.

For example:

```text
tutoring/tutor.types.ts
documents/documents.types.ts
textbooks/textbooks.types.ts
assessments/assessments.types.ts
```

17. Keep behaviour unchanged.

This is primarily an architectural/readability refactor.

Do not:
- change backend endpoint paths
- change HTTP methods
- change request payloads
- change response shapes
- rename API functions unnecessarily
- change existing application behaviour
- remove validation
- remove security checks
- change CSRF behaviour
- change file size limits
- change idempotency behaviour

18. Preserve existing exported API names wherever practical so the rest of the frontend requires minimal changes.

19. Update imports throughout the codebase after moving the code.

Ensure there are:
- no broken imports
- no circular dependencies where avoidable
- no duplicate type definitions
- no unused imports introduced by the refactor

20. Keep files reasonably small and cohesive.

A reviewer should be able to open a file and immediately understand its responsibility.

For example:

```text
tutor.api.ts
```

should answer:

"What operations can the frontend perform against the tutoring API?"

and:

```text
tutor.types.ts
```

should answer:

"What data structures belong to the tutoring domain?"

21. Use `import type` where appropriate.

For example:

```ts
import type {
  TutorProfile,
  TutorSession,
  TutorAgentReply,
} from './tutor.types';
```

22. Do not over-engineer the refactor.

Do not introduce:
- dependency injection frameworks
- repository patterns
- service classes unless genuinely useful
- unnecessary abstractions
- generated wrappers
- complex generic frameworks

Simple functions grouped by domain are preferred.

23. After refactoring, run the relevant:
- TypeScript type check
- linting
- frontend tests
- build

Fix any issues caused by the refactor.

24. At the end, provide a concise summary showing:

```text
Old structure
    ↓
New structure
```

and list:
- files created
- files removed or reduced
- important import changes
- any architectural decisions made
- whether tests/type-check/build passed

The main goals, in priority order, are:

1. Human readability
2. Clear domain boundaries
3. Easy code review
4. Maintainability
5. Type safety
6. Minimal behavioural change

Please perform the refactor rather than only suggesting the new structure.
