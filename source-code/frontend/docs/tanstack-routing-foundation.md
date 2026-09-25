# TanStack routing foundation

Status: implemented locally; production release pending.

## Design

TanStack Router owns the application URL below the Vinext catch-all entry. Role paths, validation helpers and Flashcard URL builders are centralized in `lib/routes.ts`; `lib/app-router.tsx` declares the route tree. Public, Admin, Parent and Student layouts provide explicit presentation boundaries while FastAPI continues to authorize every request.

TanStack Query owns authenticated portal state and the routed Flashcard workflow. Query keys are actor-scoped where responses are private. The cache is memory-only, is cancelled before logout, and is cleared on logout and before a new authenticated identity is loaded.

The production Nginx configuration keeps `/api/`, `/health` and `/_next/` outside application fallback. Vinext accepts only known application paths through `app/[...path]/page.tsx`. Unknown pages and missing assets return 404.

## Verification

`npm run verify` covers generated contracts, frontend routing contracts, backend authorization, type checking, linting and the production build. A built local preview is additionally checked for direct `/login`, role and nested Flashcard URLs, plus 404 responses for unknown routes and missing versioned assets.

After deployment, run:

```bash
sudo /opt/akuru/deploy/ubuntu/release-acceptance.sh akuru.magicalinternational.com
```

Then sign in once as each role and verify the role landing page. With a Student, open a permitted deck, start a session, reload the current-card URL, use Back and Forward, and confirm another Student cannot open that session URL.

## Rollback

Record the current Git revision and `/etc/nginx/sites-available/akuru` before release. If routing acceptance fails, restore the preceding reviewed frontend revision and Nginx configuration, rebuild the frontend, restart `akuru-web`, reload Nginx, and rerun `release-acceptance.sh`. This change has no database migration, so frontend rollback does not require a database rollback.
