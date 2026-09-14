# Ordered OpenAI account routing

Step 5A lets AKURU use multiple backend-only OpenAI credentials in a deterministic priority order. PostgreSQL stores account aliases, models, priorities and operational health. Secret keys remain in the ignored backend dotenv file.

## Credential aliases

Define one JSON alias-to-key map in `backend/.env`:

```dotenv
AKURU_OPENAI_ACCOUNT_KEYS='{"HOME":"sk-...","BACKUP":"sk-..."}'
```

In **OpenAI accounts** in the Admin portal, create rows using the matching aliases `HOME` and `BACKUP`. Each enabled account has a unique priority from 0–100. The lowest number is attempted first. API responses expose `credentialConfigured` and never return a key.

The legacy `AKURU_OPENAI_API_KEY` setting can support a single provider configuration, but aliases are the mechanism used by ordered routing.

## Failover behavior

The router attempts enabled, correctly configured accounts in priority order. Backups must use the same model as the preferred account so a retry does not silently change model behavior. Account switching occurs only between complete requests. A failed partial response is discarded, and the next account receives the identical request object, prompt version, schema and selected source pages.

Switching can add retry latency and may lose project-specific prompt caching, but it does not change AKURU's curriculum context or an in-progress assessment record. Attempts share one operation ID and are recorded in `ai_provider_attempts`.

Capacity errors that are safe to route include `organization_usage_limit_exceeded`, `organization_spend_limit_exceeded` and `project_spend_limit_exceeded`. Authentication, malformed-request and content-validation errors are surfaced instead of being treated as evidence that another account has credits.

## Administration and security

Admin users can create, enable, disable and reprioritize account aliases. Priorities must remain unique. The database and frontend receive aliases only. Rotate a key in `backend/.env` and restart the backend and AI workers; no frontend rebuild is required.

See [Step 5 provider boundary](step-05-ai-provider.md) for request schemas, prompt versioning, usage records and production secret handling.
