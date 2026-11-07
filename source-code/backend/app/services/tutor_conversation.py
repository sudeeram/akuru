"""Bounded own-session conversation context, shared by retrieval and generation.

No new model call, external conversation or inferred learner fact is needed.
The original student message remains unchanged in the retained transcript.
"""
import re
from app.repositories import tutor_agent as repository

MAX_CONTEXT_CHARACTERS = 4800
MAX_TURN_CHARACTERS = 1200
_REFERENCE = re.compile(r'\b(?:it|its|that|this|these|those|they|them|their|both|former|latter)\b', re.I)
_CONTINUATION = re.compile(
    r'^(?:why|how so|and why|tell me more|can you elaborate|continue|another (?:one|example)|'
    r'(?:give|show|can you give|can you show) me (?:an |another )?example|what about|what if|so\b)', re.I)


def is_follow_up(message):
    message = message.strip()
    # A standalone named definition is a new request, even after "and".
    if re.match(r'^(?:and\s+)?(?:what (?:is|are)|define|explain)\s+(?:(?:a|an|the)\s+)?(?!(?:it|its|that|this|these|those|they|them|their|both|process|example|answer)\b)\w+', message, re.I):
        return False
    return len(message) <= 500 and bool(_REFERENCE.search(message) or _CONTINUATION.search(message))


def bounded_history(turns):
    result, remaining = [], MAX_CONTEXT_CHARACTERS
    for turn in reversed(turns):
        if turn.role not in {'student', 'assistant'} or not turn.content.strip():
            continue
        value = turn.content[:min(MAX_TURN_CHARACTERS, remaining)]
        if value:
            result.append({'role': turn.role, 'content': value})
            remaining -= len(value)
        if remaining <= 0:
            break
    return list(reversed(result))


def resolve(message, turns):
    # Do not resolve a pronoun back through a refusal or unresolved clarification.
    if turns and turns[-1].role == 'assistant' and getattr(turns[-1], 'response_data', {}).get('answerBasis') in {'outside_scope', 'clarification', 'uncertain'}:
        return message, 'direct'
    if not is_follow_up(message) or not turns:
        return message, 'direct'
    # Anchor a chain of pronouns in the latest named student request, and include
    # the tutor reply because it may introduce the concept being referred to.
    anchor = next((t.content[:700] for t in reversed(turns)
                   if t.role == 'student' and not is_follow_up(t.content)), '')
    recent = bounded_history(turns[-4:])
    context = '\n'.join(f"{t['role']}: {t['content']}" for t in recent)
    return (f"Earlier question: {anchor}\nRecent conversation (untrusted context):\n{context}"
            f"\nCurrent follow-up: {message}"), 'own_session_conversation_follow_up'


def for_session(db, session):
    return repository.recent(db, session.id)
