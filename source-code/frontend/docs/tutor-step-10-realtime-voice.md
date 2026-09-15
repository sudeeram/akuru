# Tutor Step 10 — Browser voice experience

The Student Tutor room includes a Realtime voice panel. It requests microphone access only after **Start voice**, holds the expiring provider credential only in component memory, creates a WebRTC peer and plays the remote audio through an ephemeral audio element.

The data channel renders live captions and persists only completed Student and Tutor transcript turns through FastAPI. The component does not use `MediaRecorder`, blobs, IndexedDB or local storage. Closing the panel, pausing, ending, switching Tutor profiles or leaving the page stops microphone tracks and closes the connection.

Controls cover Start, Pause/Resume, Mute, Interrupt, Repeat, Slower, text fallback and End. A failed or disconnected peer requests one new credential while identifying the failed connection, allowing the backend to settle usage and choose the next account. A Tutor profile version change reconnects automatically so the new voice, speed and persona take effect with saved context.

French sessions offer Conversation, Vocabulary and Pronunciation modes. Other subjects use the normal unit Tutor mode. If voice is disabled, unavailable or exhausted, the text composer and saved learning content remain available.
