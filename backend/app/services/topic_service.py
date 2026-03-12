from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.content_topic import ContentTopic
from app.models.knowledge import KnowledgeItem
from app.models.topic import Topic
from app.services.topic_discovery_service import discover_topics_for_user, reassign_topics_for_user


def assign_topics_to_item(db: Session, item: KnowledgeItem) -> tuple[int, int]:
    _, topics_created, links_created = reassign_topics_for_user(db, item.user_id)
    return topics_created, links_created


def rebuild_topics_for_user(db: Session, user_id: int) -> tuple[int, int, int]:
    return discover_topics_for_user(db, user_id, reset_topics=True)


def discover_topics(db: Session, user_id: int) -> tuple[int, int, int]:
    return discover_topics_for_user(db, user_id, reset_topics=True)


def reassign_topics(db: Session, user_id: int) -> tuple[int, int, int]:
    return reassign_topics_for_user(db, user_id)


def get_topics_with_counts(db: Session, user_id: int) -> list[tuple[Topic, int]]:
    stmt = (
        select(Topic, func.count(ContentTopic.id))
        .outerjoin(ContentTopic, ContentTopic.topic_id == Topic.id)
        .where(Topic.user_id == user_id)
        .group_by(Topic.id)
        .order_by(func.count(ContentTopic.id).desc(), Topic.name.asc())
    )
    return list(db.execute(stmt).all())
