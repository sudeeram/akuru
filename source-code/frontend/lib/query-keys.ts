/** Query-key factories keep identity and domain boundaries explicit. */
export const queryKeys = {
  auth: {
    state: ['auth', 'state'] as const,
  },
  flashcards: {
    all: (actorRef: string) => ['flashcards', actorRef] as const,
    studentDecks: (actorRef: string) =>
      [...queryKeys.flashcards.all(actorRef), 'student-decks'] as const,
    studyOptions: (actorRef: string, deckRef: string) =>
      [...queryKeys.flashcards.all(actorRef), 'study-options', deckRef] as const,
    mastery: (actorRef: string, deckRef: string) =>
      [...queryKeys.flashcards.all(actorRef), 'mastery', deckRef] as const,
    session: (actorRef: string, sessionRef: string, position?: number) =>
      [...queryKeys.flashcards.all(actorRef), 'session', sessionRef, position ?? 'current'] as const,
    adminDecks: (actorRef: string) =>
      [...queryKeys.flashcards.all(actorRef), 'admin-decks'] as const,
    adminDeck: (actorRef: string, deckRef: string) =>
      [...queryKeys.flashcards.all(actorRef), 'admin-deck', deckRef] as const,
  },
} as const;
