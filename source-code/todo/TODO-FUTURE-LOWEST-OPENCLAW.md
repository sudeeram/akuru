# Lowest priority — OpenClaw Telegram Quick Mock

**Status: Future work — not started. Begin only after AKURU text learning, model routing and production operations are stable.**

This plan is deliberately last because it adds another production runtime, Telegram identity, temporary Student assessment state, OpenAI usage outside AKURU's normal provider path and a separate security boundary. It must not block the web Student experience.

## Future Step 7 — Add OpenClaw Telegram Quick Mock

### Purpose and boundary

Build an optional **Telegram Quick Mock** experience in which OpenClaw acts as the conversational mock-exam agent, uses its configured OpenAI integration to generate and mark temporary mocks, and queries AKURU for trusted identity, enrolment, curriculum coverage and approved educational evidence.

The Quick Mock is intentionally separate from AKURU's permanent assessment system:

- AKURU PostgreSQL continues to store the student account, Telegram link, enrolments, grade/term progression, topic coverage and approved learning sources;
- OpenClaw temporarily stores the generated paper, answers, marking decisions and result in its isolated session/plugin state;
- Quick Mock papers, answers and results do not enter AKURU assessment history, mastery, study plans, Parent reviews or long-term progress reports;
- the Student must be told clearly that the result is temporary and does not update AKURU progress;
- tracked mocks, official-paper attempts and mastery-producing practice continue to use AKURU's existing assessment services.

### Production architecture and installation decision

- [ ] Review and pin a supported OpenClaw version before installation; record Node.js, operating-system, storage and upgrade requirements.
- [ ] Decide whether the production pilot uses Telegram long polling or an HTTPS webhook behind Nginx and document the operational trade-off.
- [ ] Run OpenClaw under a dedicated Linux service account or isolated container with its own persistent state directory outside the Git checkout.
- [ ] Keep OpenClaw unable to read AKURU environment files, PostgreSQL credentials, document-storage roots and unrelated service secrets.
- [ ] Store the Telegram bot token and restricted AKURU integration credential in protected server configuration, never in Git or OpenClaw prompts.
- [ ] Add independent health checks, service restart policy, structured operational logs, backup rules for configuration and a documented rollback/uninstall procedure.
- [ ] Disable filesystem, shell, browser, general web, cross-agent and unrelated messaging tools for the AKURU exam agent.
- [ ] Expose only the reviewed AKURU Quick Mock plugin tools and the Telegram delivery capabilities required for the workflow.
- [ ] Do not install or enable OpenClaw in production until the backend APIs, isolation tests, privacy review and release gate pass.

### Telegram account linking and lifecycle

- [ ] Add a student-channel-link domain model for Telegram numeric user ID, private chat ID, link status, timestamps, actor and revocation evidence.
- [ ] Require a short-lived, single-use pairing code or signed Telegram deep link created from an authenticated AKURU Student session.
- [ ] Complete pairing through an authenticated backend endpoint that receives trusted Telegram runtime identity from the OpenClaw plugin.
- [ ] Never use Telegram username, display name or a model-provided student name as identity.
- [ ] Enforce one initial active Telegram identity per Student and prevent one Telegram identity from linking to multiple Students.
- [ ] Provide Student, Parent and Admin visibility of link status without displaying internal UUIDs or unnecessary Telegram profile data.
- [ ] Let the Student, linked Parent and Admin revoke the association and invalidate active Quick Mock access immediately.
- [ ] Require a new pairing flow after revocation or Telegram-identity change and write auditable link/revoke events.
- [ ] Permit only private bot conversations for Quick Mock; disable group and forum-topic use.
- [ ] Add rate limits and abuse controls for pairing attempts, invalid codes and repeated link changes.

### Laura and Enya isolation model

- [ ] Configure OpenClaw direct-message scope as `per-channel-peer` so each Telegram sender receives a separate conversation session.
- [ ] Key plugin-owned Quick Mock state by the trusted Telegram account, sender ID, OpenClaw session ID and temporary mock reference.
- [ ] Pass Telegram sender identity from plugin runtime context to AKURU outside model-controlled tool parameters.
- [ ] Do not include `studentId`, `familyId`, arbitrary Telegram sender ID or arbitrary Student name in model-callable tool schemas.
- [ ] Resolve the linked Student independently on every AKURU API call and enforce active account, course, subject and coverage authorization.
- [ ] Restrict OpenClaw session visibility, memory search and agent-to-agent access so Laura's session cannot inspect Enya's history or state.
- [ ] Fail closed when sender context, pairing, session ownership or subject eligibility is missing or inconsistent.
- [ ] Test direct and indirect attempts by Laura to request Enya's subjects, sources, mock state, answers, results or session history.
- [ ] Test concurrent mocks for multiple Students using the same Telegram bot and OpenClaw agent without state leakage or answer crossover.

### Read-only AKURU Quick Mock APIs

- [ ] Define a restricted service-authentication mechanism with scopes limited to identity resolution and Quick Mock source retrieval.
- [ ] Add a sender-scoped `get_my_profile` response containing only the minimum Student information required for the conversation.
- [ ] Add `get_my_enrolments`, `get_my_covered_topics` and `get_my_mock_options` endpoints that derive the Student from trusted Telegram identity.
- [ ] Add a bounded mock-generation-context endpoint that returns only eligible published topic evidence, permitted question material, mark constraints and source references.
- [ ] Add a bounded marking-context endpoint that returns the frozen temporary question context supplied by the plugin plus authorized marking evidence, without exposing unrelated mark schemes or documents.
- [ ] Use public references and controlled schemas; never expose database IDs, storage paths, provider credentials, hidden prompts or raw unrestricted document records.
- [ ] Apply normal subject boundaries so Chemistry requests cannot retrieve Biology, Physics or another subject's topics and sources.
- [ ] Apply cumulative grade/term coverage and publication rules exactly as the AKURU web experience does.
- [ ] Add response-size, question-count, source-count and page-content limits so a model cannot bulk-export the document library.
- [ ] Log security-safe tool invocations and authorization failures without persisting the generated paper, Student answers or marking result.

### AKURU OpenClaw plugin and tool contracts

- [ ] Build a versioned OpenClaw plugin dedicated to the AKURU Quick Mock workflow.
- [ ] Register narrowly scoped tools for profile, enrolments, covered topics, mock options, generation context and marking context.
- [ ] Register deterministic commands such as `/link`, `/unlink`, `/mock`, `/status`, `/question`, `/next`, `/previous`, `/flag`, `/submit`, `/result` and `/delete_mock` where commands improve reliability.
- [ ] Ensure command and inline-button callbacks use trusted sender context and idempotency keys derived from Telegram/OpenClaw delivery identifiers.
- [ ] Define strict input/output schemas for every tool and reject unknown fields, arbitrary URLs, unsupported subjects and unbounded source requests.
- [ ] Prevent the agent from accessing any AKURU write endpoint other than link/revoke operations explicitly required for identity lifecycle.
- [ ] Version agent instructions, tool schemas, mock-generation prompts and marking prompts and include those versions in temporary diagnostic metadata.
- [ ] Provide safe user messages for unavailable AKURU, expired pairing, ineligible subject, missing published evidence, exhausted quota and invalid temporary state.

### Temporary mock generation

- [ ] Let the Student request a mock conversationally, for example `prepare an iGCSE Chemistry Unit 1 mock`.
- [ ] Require OpenClaw to confirm the requested course, subject and scope against AKURU enrolment and coverage before generation.
- [ ] Retrieve approved textbook evidence, eligible past-paper material, mark schemes and examiner guidance through the bounded AKURU tools.
- [ ] Generate a strict temporary paper schema containing title, scope, duration, total marks, ordered questions, topic/source references, private marking criteria and required assets.
- [ ] Ensure every generated question is grounded in returned authorized evidence and belongs to an eligible topic in the requested subject.
- [ ] Apply deterministic plugin validation for total marks, question count, duplicate questions, missing sources, invalid topics, missing marking criteria and accidental answer leakage.
- [ ] Refuse to start the mock when source evidence or marking criteria are insufficient rather than inventing educational content.
- [ ] Keep Student-visible question content separate from private marking context throughout the active mock.
- [ ] Render complex equations, tables and diagrams into Telegram-compatible assets with readable text alternatives and source-safe delivery.
- [ ] Record the generated paper only in Laura's or Enya's isolated temporary OpenClaw state; do not call AKURU assessment-creation endpoints.

### Question-by-question Telegram experience

- [ ] Present one question at a time with question number, total questions, marks and any required image or equation asset.
- [ ] Accept ordinary free-form messages as the current question's answer only while a Quick Mock is active and the message is not an authorized command.
- [ ] Support previous, next, flag, status and submit actions through commands and accessible inline buttons.
- [ ] Save answers in plugin state before acknowledging success and make replayed Telegram/OpenClaw deliveries idempotent.
- [ ] Maintain a server-side timer in temporary state and present an authoritative remaining-time response.
- [ ] Support reconnect/resume while temporary state remains valid and explain when an expired or deleted mock cannot be resumed.
- [ ] Prohibit hints, Tutor explanations, source opening, answer generation, marking criteria and correct-answer disclosure while the mock is active.
- [ ] Respond safely when a Student asks for the answer, attempts prompt injection or asks the agent to ignore exam rules.
- [ ] Require explicit confirmation before final submission and prevent answer changes after submission.
- [ ] Classify the experience as a home practice mock rather than an invigilated examination.

### OpenClaw/OpenAI answer marking

- [ ] After submission, give OpenClaw only the frozen temporary question, the Student's answer and the authorized marking/textbook/examiner evidence required for that question.
- [ ] Require a strict structured marking result containing maximum marks, awarded marks, per-point decision, Student evidence, rationale, mistakes, improved answer, teaching explanation, confidence and review indicator.
- [ ] Validate that awarded marks do not exceed maximum marks and every decision refers to a supplied marking point.
- [ ] Validate that quoted Student evidence occurs in the submitted answer and prevent invented quotations or unsupported criteria.
- [ ] Apply a stronger configured model or bounded second pass for complex questions, failed structural validation or low-confidence marking.
- [ ] Prevent escalation loops and cap generation, marking, retry and output usage per temporary mock.
- [ ] Label low-confidence feedback clearly or withhold the affected score when the result cannot be validated reliably.
- [ ] Calculate the overall result from validated per-question results and show question-by-question mistakes and improved answers after submission.
- [ ] Do not call AKURU marking, assessment-history, mastery or study-plan mutation endpoints for Quick Mock results.
- [ ] Tell the Student that OpenClaw generated and marked the temporary practice mock and that it is not an official Edexcel result.

### Temporary state and retention

- [ ] Store structured paper, answers, current position, flags, timer, marking results and completion state outside conversation text so context compaction cannot corrupt the mock.
- [ ] Keep active state in OpenClaw/plugin-owned storage outside PostgreSQL and outside the AKURU project checkout.
- [ ] Retain incomplete mocks for a reviewed short period, initially proposed as seven days, to permit safe resume after interruption.
- [ ] Retain completed results only for a reviewed short period, initially proposed as 24 hours or until explicit deletion.
- [ ] Add `/delete_mock` and automatic expiry that remove paper, answers and result together.
- [ ] Decide separately whether OpenClaw conversation transcripts are retained; make the policy visible and avoid assuming that deleting mock state deletes Telegram's copy.
- [ ] Prevent expired state, deleted state and another sender's state from being reconstructed through session tools or memory search.
- [ ] Define backup exclusions so temporary Student answers are not retained indefinitely through general server backups.

### Quotas, model configuration and cost

- [ ] Decide whether OpenClaw uses an OpenAI API key or supported subscription authentication for the pilot and document the accounting differences.
- [ ] Prefer API-key-backed usage when exact token/cost measurement and per-child limits are required.
- [ ] Add per-linked-Student Quick Mock limits for active mocks, mocks per day, questions per mock, generation tokens, marking tokens and retries.
- [ ] Keep Quick Mock quotas in OpenClaw/plugin state unless a later decision explicitly approves persistent AKURU quota records.
- [ ] Capture provider-reported usage by generation, orchestration, marking and escalation without sending paper or answer contents to AKURU.
- [ ] Define economy and stronger model roles independently from AKURU's permanent model-policy configuration, or explicitly share a reviewed read-only policy catalogue.
- [ ] Stop safely before additional provider calls when the temporary quota is exhausted and preserve the Student's resumable state where possible.
- [ ] Provide Admin operational totals without retaining Student paper content, answers or results.

### Student, Parent and Admin communication

- [ ] Show a clear notice before starting: `This is a temporary Telegram practice mock. Its result will not update your AKURU progress.`
- [ ] Distinguish Telegram Quick Mock from tracked AKURU mocks in names, commands and help text.
- [ ] Explain that Telegram processes and may retain delivered messages and media outside AKURU.
- [ ] Provide Student instructions for pairing, starting, resuming, submitting, viewing and deleting a temporary mock.
- [ ] Let Parents and Admins see and revoke the Telegram link while keeping temporary paper, answers and marks outside their AKURU views.
- [ ] Document that Quick Mock attempts do not contribute to mastery, study plans, repeated-mistake counts, assessment history or Parent session summaries.
- [ ] Provide an optional secure link back to the AKURU portal for tracked mocks and long-term learning activities.

### Security, privacy and evaluation gates

- [ ] Threat-model malicious Telegram messages, prompt injection in Student answers, malicious source text, tool-parameter manipulation, callback replay and forged sender claims.
- [ ] Test that model instructions cannot override tool authorization, subject coverage, temporary-state ownership, mock restrictions or retention rules.
- [ ] Test Laura/Enya separation across sessions, plugin state, tool calls, media, logs, retries, deletion and model context.
- [ ] Test Telegram duplicate delivery and crash boundaries so no answer, navigation action or submission is applied twice.
- [ ] Test OpenClaw, AKURU and OpenAI timeouts; server restarts; network interruption; expired sessions; invalid structured output and unavailable models.
- [ ] Evaluate generated Chemistry mocks for syllabus relevance, topic coverage, difficulty, mark balance, evidence grounding, duplicate content and answer leakage.
- [ ] Evaluate marking against reviewed human/mark-scheme decisions before releasing automatic scores to Students.
- [ ] Test equations, scientific notation, diagrams, tables, multipart questions, long answers and image attachments in Telegram.
- [ ] Run OpenClaw's security audit and AKURU's production release checks against the final restricted configuration.
- [ ] Pilot with one Student and one reviewed Chemistry scope before adding Enya or another subject.
- [ ] Provide a release switch that disables Quick Mock and revokes its integration credential without affecting the AKURU web application.

**Done when:** Laura and Enya can independently ask the shared Telegram bot for an eligible temporary mock, OpenClaw retrieves only each Student's authorized AKURU context, generates and conducts the paper, uses OpenAI to mark submitted answers, keeps all paper/answer/result state outside AKURU PostgreSQL, expires or deletes that state as documented, communicates that no AKURU progress is updated, and passes cross-student isolation, educational-quality, privacy, cost and operational release gates.
