"""Bounded supplementary teaching policy and source-basis validation.

This does not authorize sources, assessment help, marks or learner-history claims.
Unretrieved supplementary concepts need a reviewed topic policy, not just a model's
assertion that something is related. Additional topic policies can be added here
without changing the shared Tutor API or presentation.
"""
import re
import unicodedata
from app.errors import DomainError

POLICY_VERSION = 'supplementary-teaching-v1.1'
TOPIC_POLICIES = {
    ('chemistry', 'states of matter'): (
        'evaporation', 'evaporat', 'boiling', 'boil', 'melting', 'melt', 'freezing', 'freeze',
        'condens', 'sublim', 'diffusion', 'diffus', 'solubility', 'soluble', 'dissolv', 'saturat',
        'particle', 'kinetic energy', 'changes of state', 'change of state', 'latent heat',
        'solid', 'liquid', 'gas', 'temperature', 'heat', 'energy', 'cooling', 'heating', 'density',
        'liquid surface', 'humidity', 'drying clothes', 'wet clothes', 'sweating', 'surface area',
    ),
}


# Reviewed school-level concept boundaries; these grant no access to another
# topic's documents and do not permit invented textbook or examiner citations.
BIOLOGY_TOPIC_CONCEPTS = {
    'Life Processes': ('cell', 'organelle', 'nucle', 'chromosome', 'enzyme', 'respir', 'diffus', 'osmosis', 'active transport', 'stem cell'),
    'The Variety of Living Organisms': ('classif', 'organism', 'bacter', 'virus', 'viral', 'fung', 'protoctist', 'eukary', 'prokary'),
    'Breathing and Gas Exchange': ('breath', 'ventilat', 'alveol', 'gas exchange', 'lung', 'diaphragm', 'smoking', 'diffus'),
    'Food and Digestion': ('digest', 'enzyme', 'amylase', 'protease', 'lipase', 'bile', 'villi', 'absorp', 'nutrient', 'food test'),
    'Blood and Circulation': ('blood', 'heart', 'vessel', 'capillar', 'platelet', 'clot', 'vaccin', 'antigen', 'antibod', 'memory cell', 'immun'),
    'Coordination': ('neuron', 'neurone', 'reflex', 'synap', 'impulse', 'retina', 'accommodation', 'ciliary', 'stimulus', 'receptor'),
    'Chemical Coordination': ('hormon', 'insulin', 'glucagon', 'adrenalin', 'blood glucose', 'diabetes', 'adh', 'pituitary'),
    'Homeostasis and Excretion': ('homeostas', 'excret', 'kidney', 'nephron', 'urea', 'urine', 'adh', 'water balance', 'thermoregulat', 'sweat'),
    'Reproduction in Humans': ('gamete', 'sperm', 'egg', 'fertil', 'ovulat', 'menstr', 'placenta', 'puberty', 'embryo', 'reproduct'),
    'Plants and Food': ('photosynth', 'respir', 'chlorophyll', 'chloroplast', 'starch', 'carbon dioxide', 'limiting factor', 'glucose', 'gas exchange'),
    'Transport in Plants': ('osmosis', 'water potential', 'turg', 'xylem', 'phloem', 'transpir', 'translocat', 'stoma', 'guard cell', 'root hair'),
    'Chemical Coordination in Plants': ('auxin', 'tropism', 'phototrop', 'gravitrop', 'geotrop', 'clinostat', 'coleoptile', 'plant response'),
    'Reproduction in Plants': ('pollin', 'fertil', 'pollen', 'anther', 'stigma', 'ovule', 'seed', 'fruit', 'germinat', 'asexual', 'cutting'),
    'Ecosystems': ('ecosystem', 'habitat', 'population', 'community', 'food chain', 'food web', 'trophic', 'biomass', 'quadrat', 'nitrogen cycle'),
    'Human Influences on the Environment': ('eutroph', 'pollut', 'greenhouse', 'climate', 'acid rain', 'deforest', 'conserv', 'biodivers', 'biological control'),
    'Chromosomes,Genes and DNA': ('chromosome', 'gene', 'dna', 'rna', 'transcript', 'translat', 'codon', 'mutation', 'protein synthesis', 'base pair'),
    'Cell Division': ('mitosis', 'meiosis', 'chromosome', 'chromatid', 'diploid', 'haploid', 'gamete', 'cell division', 'genetic variation'),
    'Genes and Inheritance': ('inherit', 'allele', 'dominant', 'recessive', 'heterozyg', 'homozyg', 'codominan', 'incomplete dominance', 'genotype', 'phenotype', 'pedigree', 'probability'),
    'Natural Selection and Evolution': ('natural selection', 'evol', 'adapt', 'variation', 'mutation', 'antibiotic resistance', 'fossil', 'reproductive success'),
    'Selective Breeding': ('selective breeding', 'artificial selection', 'clone', 'cloning', 'hybrid', 'inbreed', 'dolly', 'tissue culture'),
    'Using Microorganisms': ('ferment', 'yeast', 'bread', 'yoghurt', 'yogurt', 'pasteuris', 'pasteuriz', 'microorganism', 'bioreactor', 'lactobacillus'),
    'Genetic Modification': ('genetic modif', 'genetic engineer', 'restriction enzyme', 'ligase', 'plasmid', 'vector', 'recombinant', 'golden rice', 'transgenic', 'insulin', 'antitrypsin'),
}


def normalized(text):
    return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', ' ', unicodedata.normalize('NFKC', text).lower())).strip()


TOPIC_POLICIES.update({('biology', normalized(title)): terms
                       for title, terms in BIOLOGY_TOPIC_CONCEPTS.items()})

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
    if re.search(r'\b(?:diagnose me|(?:what|which|how much) (?:insulin|medicine|medication|dose)|(?:change|adjust|increase|decrease) my (?:insulin|dose|medication)|should i (?:take|inject))\b', value):
        return 'outside_scope', 'I can explain the science at iGCSE level, but I cannot recommend a personal medicine or dose. Ask a qualified healthcare professional about treatment.'
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
