import pytest

from app.config import Settings
from app.services.embeddings import embed_texts


SUBJECT_QUERIES = {
    "english": "analyse the writer's use of metaphor and persuasive language",
    "maths": "solve quadratic equations using factorisation",
    "ict": "database primary key and relational table",
    "biology": "photosynthesis chlorophyll glucose plant leaf",
    "chemistry": "ionic bonding electron transfer sodium chloride",
    "physics": "calculate force mass acceleration newton",
    "french": "french past tense perfect avoir verb",
    "human-biology": "heart circulation blood vessel artery vein",
}


def _settings() -> Settings:
    return Settings(
        database_password="test", embedding_provider="local",
        embedding_model="akuru-local-v1", embedding_dimensions=256,
    )


@pytest.mark.parametrize("subject,query", SUBJECT_QUERIES.items())
def test_local_retrieval_embedding_ranks_matching_subject(subject: str, query: str) -> None:
    labels = list(SUBJECT_QUERIES)
    documents = [SUBJECT_QUERIES[label] for label in labels]
    vectors = embed_texts(_settings(), [query, *documents])
    query_vector, candidates = vectors[0], vectors[1:]
    scores = [sum(left * right for left, right in zip(query_vector, candidate)) for candidate in candidates]
    assert labels[max(range(len(scores)), key=scores.__getitem__)] == subject


def test_local_embeddings_are_version_stable_and_normalized() -> None:
    settings = _settings()
    first, second = embed_texts(settings, ["cell division mitosis", "cell division mitosis"])
    assert first == second
    assert sum(value * value for value in first) == pytest.approx(1.0)
