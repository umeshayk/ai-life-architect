from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.content_topic import ContentTopic
from app.models.knowledge import KnowledgeItem
from app.models.topic import Topic
from app.models.user import User
from app.routers.auth import get_current_user
from app.routers.knowledge import serialize_knowledge
from app.schemas.topic import TopicItemsResponse, TopicRebuildResponse, TopicSummary
from app.services.topic_service import get_topics_with_counts, rebuild_topics_for_user


router = APIRouter(tags=["topics"])


@router.get("/api/topics", response_model=list[TopicSummary])
def list_topics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = get_topics_with_counts(db, current_user.id)
    return [TopicSummary(id=topic.id, name=topic.name, count=count) for topic, count in rows]


@router.get("/api/topics/{topic_id}/items", response_model=TopicItemsResponse)
def get_topic_items(topic_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    topic = db.scalar(select(Topic).where(Topic.id == topic_id, Topic.user_id == current_user.id))
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    items = db.scalars(
        select(KnowledgeItem)
        .join(ContentTopic, ContentTopic.knowledge_id == KnowledgeItem.id)
        .where(ContentTopic.topic_id == topic.id, KnowledgeItem.user_id == current_user.id)
    ).all()
    return TopicItemsResponse(
        topic=TopicSummary(id=topic.id, name=topic.name, count=len(items)),
        items=[serialize_knowledge(item) for item in items],
    )


@router.post("/api/topics/rebuild", response_model=TopicRebuildResponse)
def rebuild_topics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    processed_items, topics_created, links_created = rebuild_topics_for_user(db, current_user.id)
    return TopicRebuildResponse(
        processed_items=processed_items,
        topics_created=topics_created,
        links_created=links_created,
    )
