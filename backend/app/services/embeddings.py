import hashlib
import logging
from functools import lru_cache

from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.embedding import KnowledgeEmbedding
from app.models.knowledge import KnowledgeItem


logger = logging.getLogger(__name__)
settings = get_settings()


@lru_cache
def get_embedding_model() -> SentenceTransformer | None:
    try:
        return SentenceTransformer(settings.embedding_model)
    except Exception as exc:
        logger.warning("Falling back to deterministic embeddings because the model could not load: %s", exc)
        return None


def _fallback_embedding(text: str, size: int = 384) -> list[float]:
    values = [0.0] * size
    for index, token in enumerate(text.lower().split()):
        digest = hashlib.sha256(f"{index}:{token}".encode("utf-8")).digest()
        bucket = int.from_bytes(digest[:2], "big") % size
        values[bucket] += (digest[2] / 255.0) - 0.5
    norm = sum(value * value for value in values) ** 0.5 or 1.0
    return [value / norm for value in values]


def generate_embedding(text: str) -> list[float]:
    model = get_embedding_model()
    if model is None:
        return _fallback_embedding(text)
    return model.encode(text, normalize_embeddings=True).tolist()


def build_knowledge_embedding_text(item: KnowledgeItem) -> str:
    return "\n".join(
        part.strip()
        for part in [item.title, item.summary or "", item.content]
        if part and part.strip()
    )


def sync_knowledge_embedding(db: Session, item: KnowledgeItem) -> None:
    vector = generate_embedding(build_knowledge_embedding_text(item))
    record = db.scalar(select(KnowledgeEmbedding).where(KnowledgeEmbedding.knowledge_item_id == item.id))
    if record is None:
        record = KnowledgeEmbedding(knowledge_item_id=item.id, embedding=vector)
        db.add(record)
    else:
        record.embedding = vector
    db.commit()


def ensure_user_embeddings(db: Session, user_id: int) -> None:
    items = db.scalars(
        select(KnowledgeItem)
        .outerjoin(KnowledgeEmbedding, KnowledgeEmbedding.knowledge_item_id == KnowledgeItem.id)
        .where(KnowledgeItem.user_id == user_id)
    ).all()
    for item in items:
        if item.embedding is None:
            vector = generate_embedding(build_knowledge_embedding_text(item))
            db.add(KnowledgeEmbedding(knowledge_item_id=item.id, embedding=vector))
    db.commit()
