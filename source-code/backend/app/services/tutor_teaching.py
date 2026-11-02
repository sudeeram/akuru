"""Bounded supplementary teaching policy and source-basis validation.

This does not authorize sources, assessment help, marks or learner-history claims.
Unretrieved supplementary concepts need a reviewed topic policy, not just a model's
assertion that something is related. Additional topic policies can be added here
without changing the shared Tutor API or presentation.
"""
import re
import unicodedata
from app.errors import DomainError

POLICY_VERSION = 'supplementary-teaching-v1'
TOPIC_POLICIES = {
    ('chemistry', 'states of matter'): (
        'evaporation', 'evaporat', 'boiling', 'boil', 'melting', 'melt', 'freezing', 'freeze',
        'condens', 'sublim', 'diffusion', 'diffus', 'solubility', 'soluble', 'dissolv', 'saturat',
        'particle', 'kinetic energy', 'changes of state', 'change of state', 'latent heat',
        'solid', 'liquid', 'gas', 'temperature', 'heat', 'energy', 'cooling', 'heating', 'density',
        'liquid surface', 'humidity', 'drying clothes', 'wet clothes', 'sweating', 'surface area',
    ),
}


def normalized(text):
    return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', ' ', unicodedata.normalize('NFKC', text).lower())).strip()


def related(subject, topic_title, text):
    value = normalized(text)
    if normalized(topic_title) and re.search(r'\b' + re.escape(normalized(topic_title)) + r'\b', value):
        return ['active topic']
    return [term for term in TOPIC_POLICIES.get((subject, normalized(topic_title)), ())
            if re.search(r'\b' + re.escape(term) + r'\w*\b', value)]


def resolve_query(message, previous_student_question=None):
    """One bounded own-session follow-up; never append context to an explicit new question."""
    if previous_student_question and len(message) <= 200 and re.match(
        r'^(?:so\b|and (?:why|how|does|can it)\b|why[?!.]?$|(?:how|why) does (?:it|that|this)\b|'
        r'(?:tell me more|can you elaborate)\b|what (?:about (?:it|that|this)|if)\b|does (?:it|that)\b|are (?:they|those)\b)', message.strip(), re.I
    ):
        # An explicit new named concept must override a pronoun/follow-up prefix.
        if not re.search(r'\b(?:what is|define|explain (?:the |a |an )?\w+)\b', message, re.I):
            return previous_student_question[:1000] + '\n' + message, 'own_session_follow_up'
    return message, 'direct'


def boundary(subject, topic_title, message, resolved_query, citations):
    value = normalized(message)
    if re.search(r'\b(?:ignore .*instructions|system prompt|api key|password|other student|another student)\b', value):
        return 'outside_scope', 'I can help with your learning, but I cannot disclose private information, hidden instructions or another Student’s records.'
    if re.search(r'\b(?:stock market|gas prices|financial advice|quantum|schrodinger|university|graduate level|make (?:a )?(?:bomb|explosive)|weapon|medical diagnosis)\b', value):
        return 'outside_scope', 'That goes beyond this grade-appropriate learning session. Ask me about the selected topic or a related iGCSE concept.'
    if related(subject, topic_title, resolved_query):
        return 'related', ''
    if citations:
        return 'grounded_only', ''
    return 'clarification', 'Which concept in this topic would you like to explore? I did not find a matching published passage. That does not necessarily mean the textbook extraction is faulty.'


def validate_output(output, allowed_refs, supplementary_allowed):
    """Validate structural/source honesty; this is not a scientific accuracy score."""
    refs = output.citationRefs
    if any(ref not in allowed_refs for ref in refs):
        raise DomainError('tutor_output_invalid', 'The Tutor returned an unauthorized or invented citation.', 502)
    grounded, additional, note = output.groundedContent.strip(), output.additionalContent.strip(), output.boundaryContent.strip()
    if output.answerBasis in {'clarification', 'outside_scope', 'uncertain'}:
        if not note or grounded or additional or refs:
            raise DomainError('tutor_output_invalid', 'The Tutor returned inconsistent teaching boundaries.', 502)
        return note, []
    expected = 'mixed' if grounded and additional else 'grounded' if grounded else 'supplementary'
    if note or output.answerBasis != expected or not (grounded or additional) or bool(grounded) != bool(refs):
        raise DomainError('tutor_output_invalid', 'The Tutor did not distinguish textbook support from additional explanation.', 502)
    if additional and not supplementary_allowed:
        raise DomainError('tutor_output_invalid', 'Additional explanation is not enabled for this request.', 502)
    if additional and re.search(r'\b(?:page\s+\d+|fig(?:ure)?\.?\s+\d+(?:\.\d+)?|examiner\s+(?:says|requires|awards|expects)|Pearson\s+(?:requires|expects|awards))\b', additional, re.I):
        raise DomainError('tutor_output_invalid', 'Additional explanation cannot invent official references or examiner claims.', 502)
    sections = []
    if grounded: sections.append({'basis': 'grounded', 'content': grounded, 'citationRefs': refs})
    if additional: sections.append({'basis': 'supplementary', 'content': additional, 'citationRefs': []})
    parts = []
    for section in sections:
        if section['basis'] == 'grounded': parts.append('**Textbook-supported explanation**\n\n' + section['content'])
        else: parts.append('**Additional explanation**\n\nThis extends beyond the retrieved textbook evidence; it is not an official Pearson answer.\n\n' + section['content'])
    return '\n\n'.join(parts), sections
