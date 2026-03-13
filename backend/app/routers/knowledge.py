from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.models.content_topic import ContentTopic
from app.core.database import get_db
from app.models.knowledge import KnowledgeItem
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.knowledge import (
    KnowledgeCreate,
    KnowledgeResponse,
    KnowledgeTopic,
    KnowledgeUpdate,
    RelatedKnowledgeResponse,
    SearchRequest,
)
from app.services.connection_service import rebuild_connections_for_user
from app.services.embeddings import sync_knowledge_embedding
from app.services.retrieval import find_related_knowledge_by_topics, semantic_search
from app.services.summarizer import build_summary_and_tags
from app.services.topic_service import assign_topics_to_item


router = APIRouter(prefix="/knowledge", tags=["knowledge"])
api_router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


def serialize_knowledge(item: KnowledgeItem) -> KnowledgeResponse:
    return KnowledgeResponse(
        id=item.id,
        user_id=item.user_id,
        type=item.type,
        title=item.title,
        content=item.content,
        summary=item.summary,
        tags=[tag.strip() for tag in (item.tags or "").split(",") if tag.strip()],
        topics=[
            KnowledgeTopic(
                id=content_topic.topic.id,
                name=content_topic.topic.name,
                confidence_score=content_topic.confidence_score,
            )
            for content_topic in item.content_topics
            if content_topic.topic is not None
        ],
        related_count=len(item.outgoing_connections),
        source_url=item.source_url,
        file_name=item.file_name,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.post("", response_model=KnowledgeResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge(
    payload: KnowledgeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    summary, generated_tags = build_summary_and_tags(payload.title, payload.content)
    item = KnowledgeItem(
        user_id=current_user.id,
        type=payload.type,
        title=payload.title,
        content=payload.content,
        summary=summary,
        tags=",".join(payload.tags or generated_tags),
        source_url=str(payload.source_url) if payload.source_url else None,
        file_name=payload.file_name,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    sync_knowledge_embedding(db, item)
    assign_topics_to_item(db, item)
    rebuild_connections_for_user(db, current_user.id)
    db.refresh(item)
    item = db.scalar(
        select(KnowledgeItem)
        .options(
            selectinload(KnowledgeItem.content_topics).selectinload(ContentTopic.topic),
            selectinload(KnowledgeItem.outgoing_connections),
        )
        .where(KnowledgeItem.id == item.id)
    )
    return serialize_knowledge(item)


@router.get("", response_model=list[KnowledgeResponse])
def list_knowledge(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items = db.scalars(
        select(KnowledgeItem)
        .options(
            selectinload(KnowledgeItem.content_topics).selectinload(ContentTopic.topic),
            selectinload(KnowledgeItem.outgoing_connections),
        )
        .where(KnowledgeItem.user_id == current_user.id)
        .order_by(desc(KnowledgeItem.updated_at))
    ).all()
    return [serialize_knowledge(item) for item in items]


@router.put("/{item_id}", response_model=KnowledgeResponse)
def update_knowledge(
    item_id: int,
    payload: KnowledgeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.scalar(
        select(KnowledgeItem).where(KnowledgeItem.id == item_id, KnowledgeItem.user_id == current_user.id)
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge item not found")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        if field == "source_url" and value is not None:
            value = str(value)
        if field == "tags" and value is not None:
            value = ",".join(value)
        setattr(item, field, value)

    item.summary, generated_tags = build_summary_and_tags(item.title, item.content)
    if "tags" not in data:
        item.tags = ",".join(generated_tags)

    db.commit()
    db.refresh(item)
    sync_knowledge_embedding(db, item)
    assign_topics_to_item(db, item)
    rebuild_connections_for_user(db, current_user.id)
    db.refresh(item)
    item = db.scalar(
        select(KnowledgeItem)
        .options(
            selectinload(KnowledgeItem.content_topics).selectinload(ContentTopic.topic),
            selectinload(KnowledgeItem.outgoing_connections),
        )
        .where(KnowledgeItem.id == item.id)
    )
    return serialize_knowledge(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.scalar(
        select(KnowledgeItem).where(KnowledgeItem.id == item_id, KnowledgeItem.user_id == current_user.id)
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge item not found")
    db.delete(item)
    db.commit()
    rebuild_connections_for_user(db, current_user.id)


@router.post("/search", response_model=list[KnowledgeResponse])
def search_knowledge(
    payload: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = semantic_search(db, current_user.id, payload.query, payload.limit)
    loaded_items = db.scalars(
        select(KnowledgeItem)
        .options(
            selectinload(KnowledgeItem.content_topics).selectinload(ContentTopic.topic),
            selectinload(KnowledgeItem.outgoing_connections),
        )
        .where(KnowledgeItem.id.in_([match.item.id for match in items]))
    ).all()
    item_map = {item.id: item for item in loaded_items}
    return [serialize_knowledge(item_map[match.item.id]) for match in items if match.item.id in item_map]


@api_router.get("/{item_id}/related", response_model=RelatedKnowledgeResponse)
def get_related_knowledge(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    related = find_related_knowledge_by_topics(db, current_user.id, item_id)
    if related is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge item not found")
    return related
