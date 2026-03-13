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
from app.services.retrieval import find_related_knowledge_by_topics, semantic_search
from app.services.upload_ingestion_service import create_ingested_knowledge_item, update_ingested_knowledge_item


router = APIRouter(prefix="/knowledge", tags=["knowledge"])
api_router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


def serialize_knowledge(item: KnowledgeItem, ingestion_summary: dict | None = None) -> KnowledgeResponse:
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
        ingestion_summary=ingestion_summary,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.post("", response_model=KnowledgeResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge(
    payload: KnowledgeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item, ingestion_summary = create_ingested_knowledge_item(
        db,
        user_id=current_user.id,
        item_type=payload.type,
        title=payload.title,
        content=payload.content,
        source_url=str(payload.source_url) if payload.source_url else None,
        tags=payload.tags,
        file_name=payload.file_name,
    )
    return serialize_knowledge(item, ingestion_summary=ingestion_summary)


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
    title = data.get("title", item.title)
    content = data.get("content", item.content)
    source_url = data.get("source_url", item.source_url)
    if source_url is not None:
        source_url = str(source_url)
    tags = data.get("tags")
    if tags is None:
        tags = [tag.strip() for tag in (item.tags or "").split(",") if tag.strip()]

    item, ingestion_summary = update_ingested_knowledge_item(
        db,
        item,
        item_type=item.type,
        title=title,
        content=content,
        source_url=source_url,
        tags=tags,
        file_name=item.file_name,
    )
    return serialize_knowledge(item, ingestion_summary=ingestion_summary)


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
