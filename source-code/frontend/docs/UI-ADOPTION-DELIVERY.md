# UI adoption delivery coverage

20 October 2026. Frontend presentation delta; all existing domain handlers retained.

Shared changes: compact spacing, tinted divided card headers, toolbar/table surfaces, explicit navigation/focus states, profile banners, Community sections, neutral reading surfaces and responsive layouts. All roles inherit these through the existing shell. Root/login and missing-route boundaries retain the existing presentation.

Data contracts: Community retains API-backed page parameters and response totals. Existing workspace searches remain over their current authorized response or existing server filters; this change adds no paging, wider fetch, synthetic counts, bulk operation or import service. Only existing avatar/enrolment responses supply identity decoration. Attendance and carousel product adoption are intentionally deferred.

R = existing behavior retained; S = shared presentation adopted; T = targeted component change. These are code dispositions, not claims that each populated state was browser-tested. See the ongoing plan for the exact browser evidence and outstanding acceptance.

| Route | Disposition | Evidence / composition |
| --- | --- | --- |
| `/` | R | Existing sign-in and recovery retained |
| `/login` | R | Existing sign-in and recovery retained |
| `/admin` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/admin/accounts` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/admin/community-reports` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/admin/exam-documents` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/admin/textbooks` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/admin/coverage` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/admin/questions` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/admin/flashcards` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/admin/blueprints` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/admin/ai-accounts` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/admin/tutor-presets` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/admin/tutor-quotas` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/admin/tutor-history` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/admin/assessment-audit` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/admin/media` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/admin/evaluations` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/admin/operations` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/admin/profile` | S + T | Shared tokens plus explicit category/identity component wiring |
| `/admin/security` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/parent` | S + T | Shared tokens plus explicit category/identity component wiring |
| `/parent/students` | S + T | Shared tokens plus explicit category/identity component wiring |
| `/parent/tutors` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/parent/tutor-history` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/parent/library` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/parent/reviews` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/parent/assignments` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/parent/progress` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/parent/profile` | S + T | Shared tokens plus explicit category/identity component wiring |
| `/parent/security` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/student` | S + T | Shared tokens plus explicit category/identity component wiring |
| `/student/subjects` | S + T | Shared tokens plus explicit category/identity component wiring |
| `/student/community` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/student/textbooks` | S + T | Shared tokens plus explicit category/identity component wiring |
| `/student/tutors` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/student/tutor-room` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/student/practice` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/flashcards` | S + T | Shared tokens plus explicit category/identity component wiring |
| `/student/exams` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/student/progress` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/student/study-plan` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/student/profile` | S + T | Shared tokens plus explicit category/identity component wiring |
| `/student/security` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/admin/library` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/admin/textbooks/new` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/admin/textbooks/review` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/admin/exam-documents/past-papers` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/admin/exam-documents/mark-schemes` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/admin/exam-documents/examiner-reports` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/admin/exam-documents/references` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/admin/textbooks/$bookRef` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/admin/textbooks/$bookRef/topics/$topicRef` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/admin/textbooks/review/$documentRef` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/admin/exam-documents/review/$paperId` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/flashcards/decks/$deckRef` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/flashcards/decks/$deckRef/start` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/flashcards/sessions/$sessionRef/cards/$position` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/student/textbooks/$bookRef` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/student/textbooks/$bookRef/topics/$topicRef` | S + R | Existing route/feature dispatch and handlers retained; shared shell/workspace presentation |
| `/ui-features` | S + T | Actual production subject-card examples in Cards family; 27-family registry unchanged. |

Dynamic routes retain existing source/editor, reader and session layouts. Automated route matching covers all 60 registered patterns plus malformed references and role boundaries. Populated dynamic acceptance remains open because no representative content is available locally. No source image, equation, question text, answer, timer or score calculation changed.
