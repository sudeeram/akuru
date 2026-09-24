/** Admin release and Student study-session flashcard operations. */
import { request } from '../core/client';
import type { FlashcardDeck, FlashcardMode, FlashcardSession, FlashcardStudyOptions } from './flashcards.types';

export const getAdminFlashcardDecks = () => request<FlashcardDeck[]>('flashcards/admin/decks');
export const getAdminFlashcardDeck = (ref: string) => request<FlashcardDeck>(`flashcards/admin/decks/${ref}`);
export const withdrawFlashcardDeck = (deckRef: string, reason: string) => request<FlashcardDeck>(`flashcards/admin/decks/${deckRef}/withdraw`, { method: 'POST', body: { reason } });
export const getStudentFlashcardDecks = () => request<FlashcardDeck[]>('flashcards/student/decks');
export const getFlashcardStudyOptions = (deckRef: string) => request<FlashcardStudyOptions>(`flashcards/student/decks/${deckRef}/study-options`);
export const startFlashcardSession = (deckRef: string, mode: FlashcardMode, requestKey: string) => request<FlashcardSession>(`flashcards/student/decks/${deckRef}/sessions`, { method: 'POST', body: { requestKey, mode } });
export const revealFlashcard = (sessionRef: string) => request<FlashcardSession>(`flashcards/student/sessions/${sessionRef}/reveal`, { method: 'POST', body: {} });
export const rateFlashcard = (sessionRef: string, rating: 'again' | 'difficult' | 'good' | 'easy', requestKey: string) => request<FlashcardSession>(`flashcards/student/sessions/${sessionRef}/rate`, { method: 'POST', body: { rating, requestKey } });
