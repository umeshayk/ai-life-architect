from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeItem
from app.models.knowledge_connection import KnowledgeConnection
from app.services.embeddings import ensure_user_embeddings
from app.services.retrieval import semantic_search


def rebuild_connections_for_user(db: Session, user_id: int) -> tuple[int, int]:
    ensure_user_embeddings(db, user_id)
    items = db.scalars(select(KnowledgeItem).where(KnowledgeItem.user_id == user_id)).all()
    db.execute(delete(KnowledgeConnection).where(KnowledgeConnection.user_id == user_id))
    db.commit()

    created = 0
    for item in items:
        matches = semantic_search(db, user_id, f"{item.title}\n{item.summary or ''}\n{item.content}", limit=6)
        kept = 0
        for match in matches:
            if match.item.id == item.id:
                continue
            db.add(
                KnowledgeConnection(
                    user_id=user_id,
                    source_knowledge_id=item.id,
                    target_knowledge_id=match.item.id,
                    connection_type="semantic_related",
                    similarity_score=match.similarity,
                )
            )
            created += 1
            kept += 1
            if kept >= 3:
                break
    db.commit()
    return len(items), created


def get_related_connections(db: Session, user_id: int, knowledge_id: int) -> list[KnowledgeConnection]:
    stmt = (
        select(KnowledgeConnection)
        .where(
            KnowledgeConnection.user_id == user_id,
            KnowledgeConnection.source_knowledge_id == knowledge_id,
        )
        .order_by(KnowledgeConnection.similarity_score.desc())
    )
    return db.scalars(stmt).all()


def build_connection_rebuild_response(processed_items: int, connections_created: int) -> dict:
    return {
        "processed_items": processed_items,
        "connections_created": connections_created,
        "created_at": datetime.now(timezone.utc),
    }
