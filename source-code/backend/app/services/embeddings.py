import hashlib
import math
import re

from openai import OpenAI
from app.config import Settings


TOKEN_RE = re.compile(r"[a-z0-9]+")


def _local_embedding(text: str, dimensions: int) -> list[float]:
    values = [0.0] * dimensions
    for token in TOKEN_RE.findall(text.lower()):
        digest = hashlib.sha256(token.encode()).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        values[index] += 1.0 if digest[4] & 1 else -1.0
    norm = math.sqrt(sum(value * value for value in values)) or 1.0
    return [value / norm for value in values]


def embed_texts(settings: Settings, texts: list[str]) -> list[list[float]]:
    if settings.embedding_provider == "local":
        return [_local_embedding(text, settings.embedding_dimensions) for text in texts]
    client = OpenAI(api_key=settings.openai_api_key.get_secret_value(), timeout=settings.ai_timeout_seconds)
    response = client.embeddings.create(
        model=settings.embedding_model, input=texts, dimensions=settings.embedding_dimensions,
    )
    return [row.embedding for row in sorted(response.data, key=lambda row: row.index)]
