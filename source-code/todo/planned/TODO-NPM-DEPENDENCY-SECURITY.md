# Review AKURU npm dependency vulnerabilities

Created: 2026-10-31
Status: planned
Priority: high — separately scoped dependency remediation.

The Node runtime security patch does not resolve npm package vulnerabilities. The 2026-10-31 production `npm ci` audit reported 29 findings including development dependencies (1 low, 13 moderate, 12 high, 3 critical). The production-only report recorded 23 findings (1 low, 11 moderate, 10 high, 1 critical). Counts change with advisory data; rerun and inspect individual dependency paths before remediation. An earlier production-only audit also flagged transitive `proxy-addr` GHSA-jqcg-44mw-7w3h.

- [ ] Capture full and `--omit=dev` audit reports with installed versions and dependency paths; retain detailed reports outside Git if they contain internal information.
- [ ] Triage runtime reachability, affected functions and available fixed packages for every critical/high finding. Do not equate an audit count with demonstrated exploitation or assume indirect dependencies are harmless.
- [ ] Update direct dependencies or reviewed compatible transitive resolutions in the lockfile; handle framework changes as separately reviewable upgrades. Avoid blind `npm audit fix --force`.
- [ ] Run frontend tests, typecheck, lint, build, route/authentication and populated learning/review workflow checks.
- [ ] Commit/push the reviewed dependency changes, deploy with backups and run production acceptance.
- [ ] Rerun the audit; document resolved findings and any explicitly accepted remaining risk with a concrete follow-up. Update the plan status and evidence.

## Reconfirmed during text Tutor deployment — 2026-11-01

Production `npm ci` again reported 29 findings; `npm audit --omit=dev` reported the same 23 (1 critical, 10 high, 11 moderate, 1 low). Detailed report: `/tmp/akuru-text-pilot-dependency-audit.json` on the Ubuntu server. The critical entry remains `proxy-addr`; other high entries include body-parser, seroval, undici and build/tooling paths. This is a repeat of existing findings, not evidence that every affected function is reachable or that the running application is unaffected. No package/lockfile remediation was attempted in the teaching pilot. Complete the runtime-path triage and compatible security updates above.

## Reconfirmed during supplementary Tutor deployment — 2026-11-02

The unchanged lockfile again reports 29 total findings and 23 with `--omit=dev` (1 critical, 10 high, 11 moderate, 1 low). The production-only report is `/tmp/akuru-supplementary-npm-audit.json` on vm02-large. `proxy-addr` remains the critical transitive entry. Follow the existing reachability and compatible-upgrade triage above; no blind dependency upgrades were included in the supplementary teaching release.
