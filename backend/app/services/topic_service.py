from collections import Counter

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.content_topic import ContentTopic
from app.models.knowledge import KnowledgeItem
from app.models.topic import Topic


TOPIC_RULES = {
    "Agriculture": {"mushroom", "farming", "hydroponic", "agriculture"},
    "AI / Technology": {"fastapi", "react", "embeddings", "vector", "semantic", "rag", "ai"},
    "Mathematics": {"nikhilam", "vedic", "multiplication", "subtraction", "math"},
    "Travel / Spiritual": {"jyotirlinga", "temple", "kashi", "kedarnath", "somnath"},
    "Knowledge Management": {"productivity", "second", "brain", "knowledge"},
}


def _extract_keywords(item: KnowledgeItem) -> list[str]:
    tag_values = [tag.strip().lower() for tag in (item.tags or "").split(",") if tag.strip()]
    text = " ".join([item.title or "", item.summary or "", item.content or ""]).lower()
    words = [token.strip(".,:;!?()[]{}") for token in text.split()]
    return tag_values + [word for word in words if word]


def suggest_topics_for_item(item: KnowledgeItem) -> list[tuple[str, float]]:
    keywords = _extract_keywords(item)
    counts = Counter(keywords)
    matched: list[tuple[str, float]] = []
    for topic_name, topic_keywords in TOPIC_RULES.items():
        score = sum(counts.get(keyword, 0) for keyword in topic_keywords)
        if score > 0:
            confidence = min(0.95, 0.45 + score * 0.1)
            matched.append((topic_name, round(confidence, 2)))

    if matched:
        return sorted(matched, key=lambda item: item[1], reverse=True)[:3]

    fallback_tokens = [token for token in keywords if len(token) > 4][:2]
    if fallback_tokens:
        return [(token.title(), 0.35) for token in fallback_tokens[:2]]
    return [("General", 0.3)]


def _get_or_create_topic(db: Session, user_id: int, name: str) -> tuple[Topic, bool]:
    topic = db.scalar(select(Topic).where(Topic.user_id == user_id, Topic.name == name))
    if topic is not None:
        return topic, False

    topic = Topic(user_id=user_id, name=name)
    db.add(topic)
    db.flush()
    return topic, True


def assign_topics_to_item(db: Session, item: KnowledgeItem) -> tuple[int, int]:
    db.execute(delete(ContentTopic).where(ContentTopic.knowledge_id == item.id))
    created_topics = 0
    created_links = 0
    for name, confidence in suggest_topics_for_item(item):
        topic, created = _get_or_create_topic(db, item.user_id, name)
        if created:
            created_topics += 1
        db.add(
            ContentTopic(
                user_id=item.user_id,
                knowledge_id=item.id,
                topic_id=topic.id,
                confidence_score=confidence,
            )
        )
        created_links += 1
    db.commit()
    return created_topics, created_links


def rebuild_topics_for_user(db: Session, user_id: int) -> tuple[int, int, int]:
    items = db.scalars(select(KnowledgeItem).where(KnowledgeItem.user_id == user_id)).all()
    processed_items = 0
    topics_created = 0
    links_created = 0
    for item in items:
        created_topics, created_links = assign_topics_to_item(db, item)
        processed_items += 1
        topics_created += created_topics
        links_created += created_links
    return processed_items, topics_created, links_created


def get_topics_with_counts(db: Session, user_id: int) -> list[tuple[Topic, int]]:
    stmt = (
        select(Topic, func.count(ContentTopic.id))
        .outerjoin(ContentTopic, ContentTopic.topic_id == Topic.id)
        .where(Topic.user_id == user_id)
        .group_by(Topic.id)
        .order_by(func.count(ContentTopic.id).desc(), Topic.name.asc())
    )
    return list(db.execute(stmt).all())
