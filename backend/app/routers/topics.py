from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models.content_topic import ContentTopic
from app.models.knowledge import KnowledgeItem
from app.models.topic import Topic
from app.models.user import User
from app.routers.auth import get_current_user
from app.routers.knowledge import serialize_knowledge
from app.schemas.graph import GraphResponse
from app.schemas.topic import (
    KnowledgeSuggestion,
    NextLearningTopic,
    TopicCleanupResponse,
    TopicCreateRequest,
    TopicCreateResponse,
    TopicDetailResponse,
    TopicExpansionResponse,
    TopicItemsResponse,
    TopicNoteSummary,
    TopicRebuildResponse,
    TopicSearchResult,
    TopicSummary,
    TopicSummaryResponse,
)
from app.services.graph_service import _topic_group, build_topic_graph_for_user
from app.services.knowledge_expansion_service import suggest_missing_topics
from app.services.knowledge_gap_service import build_knowledge_gap_suggestions, get_next_learning_topics
from app.services.retrieval import _extract_item_concepts
from app.services.topic_service import cleanup_topics, discover_topics, get_topics_with_counts, rebuild_topics_for_user, reassign_topics
from app.services.topic_summary_service import get_topic_summary


router = APIRouter(tags=["topics"])


def _build_topic_note_summary(item: KnowledgeItem) -> TopicNoteSummary:
    preview_source = (item.summary or item.content or "").strip()
    preview = preview_source[:150].rstrip()
    if len(preview_source) > 150:
        preview = f"{preview}..."
    return TopicNoteSummary(id=item.id, title=item.title, type=item.type, preview=preview or "No preview available.")


@router.get("/api/knowledge-suggestions", response_model=list[KnowledgeSuggestion])
def get_knowledge_suggestions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    suggestions = build_knowledge_gap_suggestions(db, current_user.id)
    return [KnowledgeSuggestion(**suggestion) for suggestion in suggestions]


@router.get("/api/next-learning-topics", response_model=list[NextLearningTopic])
def get_next_learning_queue(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    topics = get_next_learning_topics(db, current_user.id)
    return [NextLearningTopic(**topic) for topic in topics]


@router.get("/api/topics", response_model=list[TopicSummary])
def list_topics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = get_topics_with_counts(db, current_user.id)
    return [
        TopicSummary(id=topic.id, name=topic.name, count=count, discovery_method="discovered", domain=_topic_group(topic.name))
        for topic, count in rows
        if count > 0
    ]


@router.post("/api/topics/add", response_model=TopicCreateResponse)
def add_topic(payload: TopicCreateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Topic name is required")

    existing = db.scalar(
        select(Topic).where(
            Topic.user_id == current_user.id,
            func.lower(Topic.name) == name.lower(),
        )
    )
    if existing is not None:
        return TopicCreateResponse(
            topic=TopicSummary(
                id=existing.id,
                name=existing.name,
                count=0,
                discovery_method="manual",
                domain=_topic_group(existing.name),
            ),
            created=False,
        )

    topic = Topic(user_id=current_user.id, name=name, type="standard", level=2)
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return TopicCreateResponse(
        topic=TopicSummary(
            id=topic.id,
            name=topic.name,
            count=0,
            discovery_method="manual",
            domain=_topic_group(topic.name),
        ),
        created=True,
    )


@router.get("/api/topics/search", response_model=list[TopicSearchResult])
def search_topics(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = q.strip().lower()
    if not query:
        return []

    rows = get_topics_with_counts(db, current_user.id)
    matches: list[TopicSearchResult] = []
    for topic, count in rows:
        topic_name = (topic.name or "").strip()
        normalized_name = topic_name.lower()
        if query not in normalized_name:
            continue
        matches.append(
            TopicSearchResult(
                id=topic.id,
                name=topic_name,
                domain=_topic_group(topic_name),
                count=count,
            )
        )

    matches.sort(
        key=lambda item: (
            0 if item.name.lower() == query else 1,
            0 if item.name.lower().startswith(query) else 1,
            -item.count,
            item.name,
        )
    )
    return matches[:8]


@router.get("/api/topics/{topic_name}/suggestions", response_model=TopicExpansionResponse)
def get_topic_suggestions(topic_name: str, refresh: bool = Query(False), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    payload = suggest_missing_topics(db, current_user.id, topic_name, refresh=refresh)
    return TopicExpansionResponse(**payload)


@router.get("/api/topics/{topic_id}/graph", response_model=GraphResponse)
def get_topic_graph(topic_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        return build_topic_graph_for_user(db, current_user.id, topic_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/api/topics/{topic_id}/summary", response_model=TopicSummaryResponse)
def get_topic_summary_endpoint(topic_id: int, refresh: bool = Query(False), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        return TopicSummaryResponse(**get_topic_summary(db, current_user.id, topic_id, refresh=refresh))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


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
        topic=TopicSummary(id=topic.id, name=topic.name, count=len(items), discovery_method="discovered", domain=_topic_group(topic.name)),
        items=[serialize_knowledge(item) for item in items],
    )


def _build_topic_detail(topic_name: str, db: Session, current_user: User) -> TopicDetailResponse:
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
            topic_id=topic.id,
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
        topic_id=None,
        notes=[_build_topic_note_summary(item) for item in matched_items],
        related_topics=[name for name, _ in related_counter.most_common(5)],
    )


@router.get("/api/topics/detail", response_model=TopicDetailResponse)
def get_topic_detail(name: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _build_topic_detail(name, db, current_user)


@router.get("/api/topics/{topic_name}", response_model=TopicDetailResponse)
def get_topic_by_name(topic_name: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _build_topic_detail(topic_name, db, current_user)


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


@router.post("/api/topics/cleanup", response_model=TopicCleanupResponse)
def cleanup_user_topics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    merged_topics = cleanup_topics(db, current_user.id)
    return TopicCleanupResponse(merged_topics=merged_topics, discovery_method="normalized")
