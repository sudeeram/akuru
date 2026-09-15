# Tutor Step 8: allowance screens

Admin users have a **Tutor allowances** navigation page. They choose a child by name, review request, text-token and voice-minute usage, and change the period or allowances. Every save requires a plain-language audit reason. Admin may increase, reduce, disable or re-enable an allowance.

The screen deliberately does not display database UUIDs, OpenAI account aliases, API keys, provider budgets or routing details. It uses the opaque `studentRef` returned by the backend.

Students see a compact allowance panel before entering the Tutor room and during an active session. It shows remaining requests, tokens, voice minutes, renewal date, and a clear available, warning, exhausted or disabled message. When AI is unavailable, saved transcripts and approved learning resources remain readable.
