# Patch the local AKURU development Node runtime

Created: 2026-10-31
Status: planned — explicitly excluded from the production/OpenClaw update by the user.

Production AKURU and OpenClaw are tracked in [the production security patch record](../completed/TODO-NODEJS-SECURITY-PATCH.md). The laptop remains on Node 22.23.2. No local software was installed by that task. The frontend wrapper now refuses known affected Node versions, so local frontend commands require a patched runtime before use.

- [ ] Obtain approval before installing local software.
- [ ] Review current official Node security releases and install a patched Node 22 version using existing NVM (October 2026 advisory floor: 22.23.4).
- [ ] Select the version, set the NVM default alias and confirm `node`, `npm` and AKURU's wrapper resolve it in new/existing terminals.
- [ ] Run the runtime-policy check, frontend tests, typecheck, lint and build. Check backend helper commands still launch Python correctly.
- [ ] Stop temporary test servers; record installed versions/results and move this plan to completed.
