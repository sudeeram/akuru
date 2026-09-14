# Step 18 — Visual media UI

Admins use **Visual media** in the horizontal navigation. They select a subject and an approved source by readable unit/document/page label; internal identifiers are option values and are not displayed. Controlled visual types accept documented JSON parameters. Conceptual illustrations accept a bounded request and display as `pending review` until the Admin records review notes and publishes or rejects them.

Students see **Visual explanations** within the selected subject only when the backend returns published media for their assigned subject and cumulative unit coverage. Every card labels the asset as supporting material and cites the official document, unit, and page. The shared accessible image component provides contextual alternative text, enlargement, original-size access, Escape/focus behavior, and an image retry state.

The UI does not receive learner-visible generation prompts, parameters, model/response identifiers, object keys, or review notes. Media calls use the existing authenticated FastAPI boundary and CSRF handling.
