/** Admin release and Student study-session flashcard operations. */
import { request } from '../core/client';
import type { FlashcardDeck, FlashcardDifficulty, FlashcardMastery, FlashcardMode, FlashcardRating, FlashcardReport, FlashcardSession, FlashcardStudyOptions } from './flashcards.types';

export const getAdminFlashcardDecks = () => request<FlashcardDeck[]>('flashcards/admin/decks');
export const getAdminFlashcardDeck = (ref: string) => request<FlashcardDeck>(`flashcards/admin/decks/${ref}`);
export const withdrawFlashcardDeck = (deckRef: string, reason: string) => request<FlashcardDeck>(`flashcards/admin/decks/${deckRef}/withdraw`, { method: 'POST', body: { reason } });
export const getStudentFlashcardDecks = () => request<FlashcardDeck[]>('flashcards/student/decks');
export const getFlashcardStudyOptions = (deckRef: string) => request<FlashcardStudyOptions>(`flashcards/student/decks/${deckRef}/study-options`);
export const getFlashcardMastery = (deckRef: string) => request<FlashcardMastery>(`flashcards/student/decks/${deckRef}/mastery`);
export const startFlashcardSession = (deckRef: string, mode: FlashcardMode, difficulty: FlashcardDifficulty | null, requestedCount: 20 | 30, requestKey: string) => request<FlashcardSession>(`flashcards/student/decks/${deckRef}/sessions`, { method: 'POST', body: { requestKey, mode, difficulty, requestedCount } });
export const getFlashcardSession = (sessionRef: string, position?: number) => request<FlashcardSession>(`flashcards/student/sessions/${sessionRef}${position ? `?position=${position}` : ''}`);
export const revealFlashcard = (sessionRef: string) => request<FlashcardSession>(`flashcards/student/sessions/${sessionRef}/reveal`, { method: 'POST', body: {} });
export const rateFlashcard = (sessionRef: string, rating: FlashcardRating, requestKey: string) => request<FlashcardSession>(`flashcards/student/sessions/${sessionRef}/rate`, { method: 'POST', body: { rating, requestKey } });
export const discardFlashcardSession = (sessionRef: string) => request<{sessionRef: string; status: 'discarded'; message: string}>(`flashcards/student/sessions/${sessionRef}/discard`, { method: 'POST', body: {} });
export const reportFlashcard = (sessionRef: string, reason: string) => request<FlashcardReport>(`flashcards/student/sessions/${sessionRef}/report`, { method: 'POST', body: { reason } });
export const getFlashcardReports = () => request<FlashcardReport[]>('flashcards/admin/reports');
export const decideFlashcardReport = (reportRef: string, decision: 'exclude'|'restore', note = '') => request<FlashcardReport>(`flashcards/admin/reports/${reportRef}/decision`, { method: 'POST', body: { decision, note } });
