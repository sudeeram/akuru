# Tutor Step 1 — Role-specific profile interface

The portal adds three horizontal-navigation destinations backed by authenticated FastAPI APIs:

- **My tutors** lets a Student create multiple tutor profiles, choose a curated AKURU BOT hero and voice style, edit or freely rename a tutor, and remove a profile.
- **Tutors** lets a Parent see the current tutor profiles for each linked child without edit controls.
- **Tutor presets** lets Admin enable, disable and order the curated avatar and voice choices.

`features/tutor-profiles.tsx` owns these experiences. `api/tutoring` owns the browser contract and uses the shared session-cookie and CSRF behavior in `api/core`. The component never displays internal Student or tutor UUIDs, provider voice references or credentials.

Profile editing sends a complete snapshot and the backend creates a new immutable version. A disabled preset remains available for rendering an existing profile but is filtered out of the Student picker. The UI uses the existing optimized image component, explicit labels, radio controls, responsive grids and descriptive avatar alternative text.

Tutor profiles configure future Tutor sessions; they do not start a conversation in Step 1. Text and voice remain controlled by the disabled-by-default release flags established in Tutor Step 0.
