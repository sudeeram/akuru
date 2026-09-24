/** Admin release and Student study-session flashcard operations. */
import { request } from '../core/client';
import type { FlashcardDeck, FlashcardSession } from './flashcards.types';

export const getAdminFlashcardDecks = () => request<FlashcardDeck[]>('flashcards/admin/decks');
export const getAdminFlashcardDeck = (ref: string) => request<FlashcardDeck>(`flashcards/admin/decks/${ref}`);
export const generateFlashcardDeck = (topicRef: string, cardLimit: number, requestKey: string) => request<FlashcardDeck>('flashcards/admin/decks/generate', { method: 'POST', body: { topicRef, cardLimit, requestKey } });
export const reviewFlashcard = (deckRef: string, cardRef: string, front: string, back: string, decision: 'review_required' | 'approved' | 'rejected') => request<FlashcardDeck>(`flashcards/admin/decks/${deckRef}/cards/${cardRef}`, { method: 'PATCH', body: { front, back, decision } });
export const releaseFlashcardDeck = (deckRef: string) => request<FlashcardDeck>(`flashcards/admin/decks/${deckRef}/release`, { method: 'POST', body: {} });
export const getStudentFlashcardDecks = () => request<FlashcardDeck[]>('flashcards/student/decks');
export const startFlashcardSession = (deckRef: string, requestKey: string) => request<FlashcardSession>(`flashcards/student/decks/${deckRef}/sessions`, { method: 'POST', body: { requestKey } });
export const revealFlashcard = (sessionRef: string) => request<FlashcardSession>(`flashcards/student/sessions/${sessionRef}/reveal`, { method: 'POST', body: {} });
export const rateFlashcard = (sessionRef: string, rating: 'again' | 'difficult' | 'good' | 'easy', requestKey: string) => request<FlashcardSession>(`flashcards/student/sessions/${sessionRef}/rate`, { method: 'POST', body: { rating, requestKey } });
