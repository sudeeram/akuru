// Public frontend API. Feature components import from this barrel, while each
// implementation remains close to the domain that owns its contract.
export * from './core/client';
export * from './core/errors';
export * from './core/csrf';

export * from './state/state.api';
export * from './state/state.types';
export * from './tutoring/tutor.api';
export * from './tutoring/tutor.types';
export * from './documents/documents.api';
export * from './documents/documents.types';
export * from './textbooks/textbooks.api';
export * from './textbooks/textbooks.types';
export * from './curriculum/curriculum.api';
export * from './curriculum/curriculum.types';
export * from './assessments/assessments.api';
export * from './assessments/assessments.types';
export * from './flashcards/flashcards.api';
export * from './flashcards/flashcards.types';
export * from './mastery/mastery.types';

export type {
  ApiOperation,
  ApiOperations,
  Schemas as BackendSchemas,
} from '../lib/generated/api-contract';
