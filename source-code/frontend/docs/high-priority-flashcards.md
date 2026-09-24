# Flashcard interfaces

Admins open **Flashcard release** to inspect imported curated releases. The page shows release identity, validation state, category distribution, approved cards and exact evidence. It contains no card-generation controls. A released deck can be withdrawn with an audited reason.

Students open **Flashcards**, choose an eligible topic deck and then choose Quick review, Normal review, Full topic practice, Difficult cards, Due today or Unit mixed practice. Disabled modes show their zero available count. The study view supports keyboard navigation and screen readers, shows progress, hides the answer until requested, presents four recall ratings and exposes exact textbook evidence after reveal.

The evidence panel shows a reviewed figure only when its approved caption matches the figure reference in the primary text, or when the curated card explicitly names that approved visual. The figure comes from the current primary source. **View matching textbook page** opens the corresponding printed page image from the separately reviewed visual-reference scan; raw evidence JSON is never presented to a Student. Extraction boundary markers are removed from the displayed excerpt.

The UI sends only a deck, mode and idempotency key. The backend owns eligibility, adaptive selection, the immutable session snapshot and scheduling.
