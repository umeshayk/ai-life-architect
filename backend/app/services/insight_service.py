from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.content_topic import ContentTopic
from app.models.knowledge import KnowledgeItem
from app.models.topic import Topic
from app.services.topic_service import discover_topics, get_topics_with_counts, rebuild_topics_for_user


def suggestion_for_topic(topic_name: str) -> str:
    lowered = topic_name.lower()
    if any(token in lowered for token in {"mushroom", "farm", "agriculture", "hydroponic"}):
        return "You saved several agriculture-focused items. Consider drafting a business or operations plan."
    if any(token in lowered for token in {"semantic", "vector", "embedding", "ai", "llm", "fastapi", "react"}):
        return "You saved multiple AI system topics. Consider documenting your architecture and implementation patterns."
    if any(token in lowered for token in {"knowledge management", "second brain", "workflow"}):
        return "Your knowledge system is becoming richer. Consider organizing it into a reusable memory workflow."
    if any(token in lowered for token in {"math", "vedic", "multiplication"}):
        return "You saved mathematics material. Consider creating a practice or teaching collection."
    if any(token in lowered for token in {"travel", "spiritual", "temple", "jyotirlinga"}):
        return "You saved travel or spiritual material. Consider building a dedicated itinerary or pilgrimage collection."
    return f"You are building depth around {topic_name}. Consider creating a focused collection or summary note."


def build_weekly_insights(db: Session, user_id: int) -> dict:
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    items = db.scalars(
        select(KnowledgeItem)
        .where(KnowledgeItem.user_id == user_id)
        .order_by(desc(KnowledgeItem.created_at))
    ).all()
    existing_topic_link = db.scalar(
        select(ContentTopic.id)
        .join(KnowledgeItem, KnowledgeItem.id == ContentTopic.knowledge_id)
        .where(KnowledgeItem.user_id == user_id)
        .limit(1)
    )
    if items and existing_topic_link is None:
        discover_topics(db, user_id)
    recent_items = [item for item in items if item.created_at >= week_ago]
    top_tags_counter: Counter[str] = Counter()
    for item in recent_items or items[:10]:
        for tag in (item.tags or "").split(","):
            cleaned = tag.strip()
            if cleaned:
                top_tags_counter[cleaned] += 1

    topic_rows = db.execute(
        select(Topic.name, Topic.id)
        .join(ContentTopic, ContentTopic.topic_id == Topic.id)
        .join(KnowledgeItem, KnowledgeItem.id == ContentTopic.knowledge_id)
        .where(KnowledgeItem.user_id == user_id, KnowledgeItem.created_at >= week_ago)
    ).all()
    topic_counts = Counter(name for name, _ in topic_rows)
    topic_lookup = {
        topic.name: topic.id
        for topic, _ in get_topics_with_counts(db, user_id)
    }
    if not topic_counts:
        all_topics = get_topics_with_counts(db, user_id)
        topic_counts = Counter({topic.name: count for topic, count in all_topics})

    top_topics = [
        {"id": topic_lookup.get(name, 0), "name": name, "count": count}
        for name, count in topic_counts.most_common(8)
        if count > 1 or len(topic_counts) <= 5
    ]

    suggestions = []
    for topic_name, _ in topic_counts.most_common(3):
        suggestions.append(suggestion_for_topic(topic_name))
    if not suggestions and recent_items:
        suggestions.append("You added new knowledge this week. Consider reviewing and tagging it for easier retrieval.")
    while len(suggestions) < 3:
        suggestions.append("Keep adding notes, links, and files so your memory engine can build stronger topic patterns.")

    return {
        "total_items": len(items),
        "items_added_this_week": len(recent_items),
        "top_topics": top_topics,
        "top_tags": [tag for tag, _ in top_tags_counter.most_common(5)],
        "recent_titles": [item.title for item in items[:5]],
        "suggestions": suggestions[:3],
    }
