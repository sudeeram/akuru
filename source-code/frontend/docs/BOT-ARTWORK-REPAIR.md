# AKURU bot artwork repair

20 October 2026. User requested inspection, reconstruction of clipped artwork, replacement and production deployment.

## Audit and delivered assets

Reviewed all 18 existing bot-related raster assets: ten individual poses, the original overview sheet, five route-loading images, the legacy hero illustration and the favicon. The ten original individual poses were cropped from a shared sheet: some lost parts of the character or prop, while others retained fragments of neighbouring poses. All ten were rebuilt as independent illustrations. The overview sheet, five loading illustrations, hero and favicon were visually intact for their intended use and retained.

Final replacements are `public/akuru-bots/akuru-bot-{curious,wink,reader,celebrate,question,laptop,checklist,idea,runner,say}.png`. Existing filenames and API avatar paths remain valid. No backend, database, dependency or schema changes.

The built-in image-generation tool reconstructed the artwork using each corresponding original as its edit target. Character identity, red/cyan palette, pose and prop purpose were retained. The images were exported at 512 × 512 using standard proportional downscaling and PNG compression; no further reconstruction or cropping was performed by code. Full-resolution generation outputs remain in the generated-images library.

## Prompt set

Common production edit brief: rebuild one complete original rounded coral-red 3D AKURU robot with a dark navy face screen, luminous cyan features/hands/feet, familiar proportions and softly lit toy material. Reconstruct every clipped part; remove all neighbouring sprite fragments. Center the full body and complete prop on a square genuinely transparent canvas, requesting at least 10% empty margin around props, glow and a self-contained shadow. No background, ground plane, watermark, frame or extra character. Preserve identity and original pose meaning rather than redesigning the mascot.

Pose-specific instructions:

| Asset | Pose and invariants |
| --- | --- |
| Curious | Upright curious friendly robot; open cyan eyes, small smile and subtle cyan orbit/sparkle. |
| Wink | Standing, waving one hand, one open eye and one wink, small smile and yellow greeting rays. |
| Reader | Complete open navy book; smiling crescent eyes; exact cover text `LEARN EXPLORE GROW` on three lines. |
| Celebrate | Jumping with both arms raised, smiling crescent eyes and yellow celebration rays around both hands. |
| Question | Thoughtful hand at chin, puzzled friendly eyes and a complete glowing cyan question mark. |
| Laptop | Sitting with a complete open navy laptop, glowing graduation-cap symbol and both feet visible. |
| Checklist | Standing beside and pointing to a complete floating cyan panel with three green checks. |
| Idea | Holding a complete glowing yellow bulb, smiling crescent eyes and one foot lifted. |
| Runner | Running with both arms visible, one foot forward, energetic eyes, small smile and short cyan motion trail. |
| Say | Standing and waving beneath a complete cyan speech bubble with the exact word `AKURU`. |

The generation brief requested 10% margin; measured final margins vary. Acceptance is based on complete visible silhouettes, props and contained glows rather than claiming an exact generated percentage.

## Caller and cache handling

Login/learning CSS background references now include `?v=20261020-uncropped`. Tutor profile cards, avatar options and Admin preset previews append the same version to local `/akuru-bots/` paths. Other image paths retain their existing URL. Existing contain sizing is preserved, so props remain visible. Canonical unversioned URLs also serve the replacement files; an already cached direct URL may need refresh until its existing cache expires.

## Validation

- All ten PNGs have actual RGBA transparency, 512 × 512 dimensions and 23–48px minimum visible-content margin (alpha > 24). Boundary alpha is at most 2/255: there is no opaque edge truncation.
- Browser review displayed all ten exports on alternating white/navy cards; all loaded at their expected resolution with complete artwork and no neighbouring pieces.
- Local AKURU login checked with the repaired curious, reader and checklist composition. Existing contain behavior keeps all artwork inside its slot.
- 90 frontend tests, typecheck, lint and production build pass. Existing build advisories remain.
- Temporary local review HTML was removed before release. Existing unrelated sidebar hover changes are excluded.

## Release

Deployed `bdd0d43f5f6420c9a70aca7259ff9a970ab2d4a1` on 20 October 2026 at 05:46 UTC. Exact-revision preflight, encrypted database/document backup and standard build/deploy passed. Schema remains `0012_student_community`, with no new upgrade operations.

Evidence: `/data/akuru/release-evidence/deployed-bdd0d43f5f6420c9a70aca7259ff9a970ab2d4a1-20261020T054634Z.txt`.

Post-deployment HTTPS, security headers, routed entry points, missing asset/API boundaries, services, timers and loopback-binding checks passed. Production checkout is clean at the release SHA with no failed services. Browser inspection confirms the live login uses the repaired curious, reader and checklist PNGs with the new cache version. Existing dependency audit/build advisories remain unchanged; no dependencies were upgraded.

All ten public versioned PNG responses were downloaded from the production host over verified HTTPS and matched the deployed source assets by SHA-256. Local direct-download checks were affected by local certificate-store/transfer issues; production-host checks and browser rendering passed without disabling certificate verification.

Previous runtime release for rollback reference: `c4526d914c0baddf0b9d2f3e7202eef2f4af548e`. Follow the established release process for any rollback; this asset/frontend change requires no reverse database migration.
