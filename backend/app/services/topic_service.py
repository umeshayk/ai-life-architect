from collections import Counter

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.content_topic import ContentTopic
from app.models.knowledge import KnowledgeItem
from app.models.topic import Topic
from app.services.topic_discovery_service import assign_topics_for_item as assign_topics_directly_for_item
from app.services.topic_discovery_service import discover_topics_for_user, preview_topic_discovery_for_item, reassign_topics_for_user
from app.services.topic_normalizer_service import merge_similar_topics


def assign_topics_to_item(db: Session, item: KnowledgeItem) -> tuple[int, int]:
    topics_created, links_created = assign_topics_directly_for_item(db, item)
    return topics_created, links_created


def preview_topics_for_item(item: KnowledgeItem) -> dict[str, list[str]]:
    return preview_topic_discovery_for_item(item)


def rebuild_topics_for_user(db: Session, user_id: int) -> tuple[int, int, int]:
    return discover_topics_for_user(db, user_id, reset_topics=True)


def discover_topics(db: Session, user_id: int) -> tuple[int, int, int]:
    return discover_topics_for_user(db, user_id, reset_topics=True)


def reassign_topics(db: Session, user_id: int) -> tuple[int, int, int]:
    return reassign_topics_for_user(db, user_id)


def cleanup_topics(db: Session, user_id: int) -> int:
    return merge_similar_topics(db, user_id)


def get_topics_with_counts(db: Session, user_id: int) -> list[tuple[Topic, int]]:
    raw_rows = list(
        db.execute(
            select(Topic, func.count(ContentTopic.id))
            .outerjoin(ContentTopic, ContentTopic.topic_id == Topic.id)
            .where(Topic.user_id == user_id)
            .group_by(Topic.id)
        ).all()
    )
    return select_stable_topics_with_counts(raw_rows)


def select_stable_topics_with_counts(rows: list[tuple[Topic, int]]) -> list[tuple[Topic, int]]:
    filtered = [(topic, count) for topic, count in rows if count >= 2]
    if filtered:
        return sorted(filtered, key=lambda row: (-row[1], row[0].name.lower()))

    fallback = [(topic, count) for topic, count in rows if count > 0]
    return sorted(fallback, key=lambda row: (-row[1], row[0].name.lower()))


def build_stable_topic_counts(topic_names: list[str]) -> Counter[str]:
    counts = Counter(topic_names)
    stable = Counter({name: count for name, count in counts.items() if count >= 2})
    return stable or counts


def get_raw_topics_with_counts(db: Session, user_id: int) -> list[tuple[Topic, int]]:
    stmt = (
        select(Topic, func.count(ContentTopic.id))
        .outerjoin(ContentTopic, ContentTopic.topic_id == Topic.id)
        .where(Topic.user_id == user_id)
        .group_by(Topic.id)
        .order_by(func.count(ContentTopic.id).desc(), Topic.name.asc())
    )
    return list(db.execute(stmt).all())
