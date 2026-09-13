# AKURU AI provider layer

Step 5 introduces a backend-only provider boundary for structured multimodal requests. It does not expose a student-facing AI endpoint yet. Textbook extraction, paper extraction, unit mapping, assessment and tutoring will call this shared layer as their workflows are implemented in later steps.

## Runtime flow

1. An authorized AKURU service selects the exact pages and approved curriculum context required for one operation.
2. It chooses a versioned prompt from `app/ai/prompts.py` and a strict Pydantic result type.
3. Source text and page images are placed only in the user input. Fixed AKURU instructions tell the model that uploaded content is untrusted reference material.
4. `OpenAIProvider` uses the Responses API structured parsing helper. The SDK converts the Pydantic model to a strict JSON schema, and AKURU validates the returned object again.
5. `AIService` records provider, model, purpose, prompt version, schema, page numbers, latency, attempts, token usage and response ID in `ai_invocations`. It deliberately does not store source text, images, credentials or model output there.
6. PostgreSQL permissions, curriculum scope, publication state and question eligibility remain authoritative. AI output is a proposal for the relevant review or assessment workflow.

The implementation follows the official [OpenAI Responses API create reference](https://developers.openai.com/api/reference/cli/resources/responses/methods/create), including `store=false`, `max_output_tokens`, typed structured output, image inputs, metadata and response usage capture.

## Local configuration

The default is safe and makes no provider call:

```dotenv
AKURU_AI_PROVIDER=disabled
AKURU_OPENAI_API_KEY=
AKURU_OPENAI_MODEL=
```

To use OpenAI locally, copy `.env.example` to the ignored backend `.env`, then set:

```dotenv
AKURU_AI_PROVIDER=openai
AKURU_OPENAI_API_KEY=your-project-key
AKURU_OPENAI_MODEL=your-approved-model-id
```

Keep the key only in `backend/.env`. Never prefix it with `VITE_`, return it through an API, commit it, put it in frontend storage or log the settings object. Tests use `FakeAIProvider` and never need a key or paid call.

Timeout, retry, concurrency, page, text, image and output-token ceilings are configurable with the `AKURU_AI_*` settings documented in `.env.example`. These bound request cost and resource use. Configure OpenAI project budgets and alerts as the account-wide monetary backstop.

## Production secrets

Store the key in OCI Vault as a secret. At deployment, grant only the AKURU backend service identity permission to read that secret and inject its current value into the backend process environment as `AKURU_OPENAI_API_KEY`. Do not grant the web server, frontend build, Redis worker users unrelated to AI work, or database users access to the vault secret. Rotate the vault secret and restart the backend/AI workers without rebuilding frontend assets.

The Ubuntu playbook creates infrastructure and application services; it must not contain an API key. A later deployment step can add a Vault retrieval unit or OCI SDK integration after the server identity and Vault OCIDs are known.

## Adding a workflow

- Define a Pydantic output model with `extra="forbid"` and explicit evidence/page fields.
- Use the corresponding prompt and keep its version unchanged after release; create a new version for behavioral changes.
- Select pages under the current user's server-side authorization and curriculum filters.
- Call `AIService.generate`, supplying actor/document IDs when applicable.
- Treat provider errors as reviewable failures. Never accept partial free-form output as a substitute for the required schema.
- Add fake-provider tests for valid, malformed and limit-exceeded responses before enabling the workflow.
