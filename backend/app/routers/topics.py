from collections import Counter

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models.content_topic import ContentTopic
from app.models.knowledge import KnowledgeItem
from app.models.topic import Topic
from app.models.user import User
from app.routers.auth import get_current_user
from app.routers.knowledge import serialize_knowledge
from app.schemas.topic import TopicDetailResponse, TopicItemsResponse, TopicNoteSummary, TopicRebuildResponse, TopicSummary
from app.services.retrieval import _extract_item_concepts
from app.services.topic_service import discover_topics, get_topics_with_counts, rebuild_topics_for_user, reassign_topics


router = APIRouter(tags=["topics"])


def _build_topic_note_summary(item: KnowledgeItem) -> TopicNoteSummary:
    preview_source = (item.summary or item.content or "").strip()
    preview = preview_source[:150].rstrip()
    if len(preview_source) > 150:
        preview = f"{preview}..."
    return TopicNoteSummary(id=item.id, title=item.title, type=item.type, preview=preview or "No preview available.")


@router.get("/api/topics", response_model=list[TopicSummary])
def list_topics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = get_topics_with_counts(db, current_user.id)
    return [
        TopicSummary(id=topic.id, name=topic.name, count=count, discovery_method="discovered")
        for topic, count in rows
        if count > 0
    ]


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
        topic=TopicSummary(id=topic.id, name=topic.name, count=len(items), discovery_method="discovered"),
        items=[serialize_knowledge(item) for item in items],
    )


@router.get("/api/topics/{topic_name}", response_model=TopicDetailResponse)
def get_topic_by_name(topic_name: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    normalized_topic_name = topic_name.strip().lower()
    topic = db.scalar(
        select(Topic).where(
            Topic.user_id == current_user.id,
            func.lower(Topic.name) == normalized_topic_name,
        )
    )
    if topic is not None:
        items = db.scalars(
            select(KnowledgeItem)
            .join(ContentTopic, ContentTopic.knowledge_id == KnowledgeItem.id)
            .where(ContentTopic.topic_id == topic.id, KnowledgeItem.user_id == current_user.id)
        ).all()

        related_counter: Counter[str] = Counter()
        for item in items:
            sibling_topics = db.scalars(
                select(Topic.name)
                .join(ContentTopic, ContentTopic.topic_id == Topic.id)
                .where(ContentTopic.knowledge_id == item.id, Topic.user_id == current_user.id, Topic.id != topic.id)
            ).all()
            for sibling_topic in sibling_topics:
                if sibling_topic:
                    related_counter[sibling_topic] += 1

        return TopicDetailResponse(
            topic=topic.name,
            notes=[_build_topic_note_summary(item) for item in items],
            related_topics=[name for name, _ in related_counter.most_common(5)],
        )

    items = db.scalars(
        select(KnowledgeItem)
        .options(selectinload(KnowledgeItem.content_topics).selectinload(ContentTopic.topic))
        .where(KnowledgeItem.user_id == current_user.id)
    ).all()

    matched_items: list[KnowledgeItem] = []
    related_counter: Counter[str] = Counter()
    for item in items:
        concepts = _extract_item_concepts(item)
        normalized_concepts = {concept.lower(): concept for concept in concepts}
        if normalized_topic_name not in normalized_concepts:
            continue
        matched_items.append(item)
        for concept in concepts:
            if concept.lower() != normalized_topic_name:
                related_counter[concept] += 1

    if not matched_items:
        raise HTTPException(status_code=404, detail="Topic not found")

    return TopicDetailResponse(
        topic=topic_name,
        notes=[_build_topic_note_summary(item) for item in matched_items],
        related_topics=[name for name, _ in related_counter.most_common(5)],
    )


@router.post("/api/topics/rebuild", response_model=TopicRebuildResponse)
def rebuild_topics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    processed_items, topics_created, links_created = rebuild_topics_for_user(db, current_user.id)
    return TopicRebuildResponse(
        processed_items=processed_items,
        topics_created=topics_created,
        links_created=links_created,
        discovery_method="discovered",
    )


@router.post("/api/topics/discover", response_model=TopicRebuildResponse)
def discover_user_topics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    processed_items, topics_created, links_created = discover_topics(db, current_user.id)
    return TopicRebuildResponse(
        processed_items=processed_items,
        topics_created=topics_created,
        links_created=links_created,
        discovery_method="discovered",
    )


@router.post("/api/topics/reassign", response_model=TopicRebuildResponse)
def reassign_user_topics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    processed_items, topics_created, links_created = reassign_topics(db, current_user.id)
    return TopicRebuildResponse(
        processed_items=processed_items,
        topics_created=topics_created,
        links_created=links_created,
        discovery_method="discovered",
    )
