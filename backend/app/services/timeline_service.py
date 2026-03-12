from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.models.content_topic import ContentTopic
from app.models.knowledge import KnowledgeItem
from app.schemas.timeline import (
    TimelineGroup,
    TimelineInsights,
    TimelineItem,
    TimelineResponse,
    TimelineSummary,
    TimelineTopicCount,
)


VALID_RANGES = {"7d", "30d", "all"}
VALID_GROUPS = {"day", "week", "month"}


def get_timeline(db: Session, user_id: int, range_key: str = "30d", group_by: str = "week") -> TimelineResponse:
    normalized_range = range_key if range_key in VALID_RANGES else "30d"
    normalized_group = group_by if group_by in VALID_GROUPS else "week"
    items = _load_items(db, user_id, normalized_range)
    all_items = _load_items(db, user_id, "all")

    topic_counts: Counter[str] = Counter()
    groups_map: dict[str, list[TimelineItem]] = defaultdict(list)

    for item in items:
        serialized_item = _serialize_item(item)
        bucket_key = _bucket_key(item.created_at, normalized_group)
        groups_map[bucket_key].append(serialized_item)
        for topic_name in serialized_item.topics:
            topic_counts[topic_name] += 1

    groups = []
    for date_key, bucket_items in sorted(groups_map.items(), reverse=True):
        groups.append(
            TimelineGroup(
                label=_group_label(date_key, normalized_group),
                date_key=date_key,
                count=len(bucket_items),
                items=bucket_items,
            )
        )

    top_topics = [
        TimelineTopicCount(name=name, count=count)
        for name, count in topic_counts.most_common(8)
        if count > 0
    ]
    summary = _build_summary(groups, top_topics)
    insights = _build_insights(items, all_items, top_topics, normalized_range)
    return TimelineResponse(groups=groups, top_topics=top_topics, summary=summary, insights=insights)


def _load_items(db: Session, user_id: int, range_key: str) -> list[KnowledgeItem]:
    stmt = (
        select(KnowledgeItem)
        .options(selectinload(KnowledgeItem.content_topics).selectinload(ContentTopic.topic))
        .where(KnowledgeItem.user_id == user_id)
        .order_by(desc(KnowledgeItem.created_at))
    )

    since = _range_start(range_key)
    if since is not None:
        stmt = stmt.where(KnowledgeItem.created_at >= since)

    return db.scalars(stmt).all()


def _range_start(range_key: str) -> datetime | None:
    now = datetime.now(UTC)
    if range_key == "7d":
        return now - timedelta(days=7)
    if range_key == "30d":
        return now - timedelta(days=30)
    return None


def _serialize_item(item: KnowledgeItem) -> TimelineItem:
    return TimelineItem(
        id=item.id,
        title=item.title,
        type=item.type,
        summary=item.summary,
        tags=[tag.strip() for tag in (item.tags or "").split(",") if tag.strip()],
        topics=[
            content_topic.topic.name
            for content_topic in item.content_topics
            if content_topic.topic is not None
        ],
        created_at=item.created_at,
    )


def _bucket_key(created_at: datetime, group_by: str) -> str:
    value = created_at.astimezone(UTC)
    if group_by == "day":
        return value.strftime("%Y-%m-%d")
    if group_by == "month":
        return value.strftime("%Y-%m")
    iso_year, iso_week, _ = value.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def _group_label(date_key: str, group_by: str) -> str:
    now = datetime.now(UTC)
    if group_by == "day":
        target = datetime.strptime(date_key, "%Y-%m-%d").replace(tzinfo=UTC)
        delta_days = (now.date() - target.date()).days
        if delta_days == 0:
            return "Today"
        if delta_days == 1:
            return "Yesterday"
        return target.strftime("%b %d, %Y")

    if group_by == "month":
        target = datetime.strptime(date_key, "%Y-%m").replace(tzinfo=UTC)
        if target.year == now.year and target.month == now.month:
            return "This Month"
        return target.strftime("%B %Y")

    year_value, week_value = date_key.split("-W")
    year = int(year_value)
    week = int(week_value)
    current_year, current_week, _ = now.isocalendar()
    if year == current_year and week == current_week:
        return "This Week"
    week_start = datetime.fromisocalendar(year, week, 1).replace(tzinfo=UTC)
    week_end = week_start + timedelta(days=6)
    return f"{week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}"


def _build_summary(groups: list[TimelineGroup], top_topics: list[TimelineTopicCount]) -> TimelineSummary:
    total_items = sum(group.count for group in groups)
    most_active_group = max(groups, key=lambda group: group.count, default=None)
    latest_item_title = groups[0].items[0].title if groups and groups[0].items else None
    return TimelineSummary(
        total_items=total_items,
        most_active_period=most_active_group.label if most_active_group else "No activity yet",
        top_topics=[topic.name for topic in top_topics[:3]],
        latest_item_title=latest_item_title,
    )


def _build_insights(
    items: list[KnowledgeItem],
    all_items: list[KnowledgeItem],
    top_topics: list[TimelineTopicCount],
    range_key: str,
) -> TimelineInsights:
    if len(items) < 2 or not top_topics:
        return TimelineInsights(
            summary="Not enough activity yet to generate insights.",
            emerging_topics=[],
            dominant_topic=None,
            suggestions=[],
        )

    all_topic_counts: Counter[str] = Counter()
    for item in all_items:
        for content_topic in item.content_topics:
            if content_topic.topic is not None:
                all_topic_counts[content_topic.topic.name] += 1

    dominant_topic = top_topics[0].name if top_topics else None
    emerging_topics = _detect_emerging_topics(top_topics, all_topic_counts, range_key)
    summary = _build_insight_summary(top_topics, dominant_topic, emerging_topics, range_key)
    suggestions = _build_suggestions(top_topics, emerging_topics)

    return TimelineInsights(
        summary=summary,
        emerging_topics=emerging_topics,
        dominant_topic=dominant_topic,
        suggestions=suggestions[:3],
    )


def _detect_emerging_topics(
    top_topics: list[TimelineTopicCount],
    all_topic_counts: Counter[str],
    range_key: str,
) -> list[str]:
    if range_key == "all":
        return []

    ranked_topics = sorted(
        top_topics,
        key=lambda topic: (topic.count, all_topic_counts[topic.name], topic.name),
        reverse=True,
    )

    emerging = [
        topic.name
        for topic in ranked_topics[2:]
        if topic.count > 0
    ]
    return emerging[:2]


def _build_insight_summary(
    top_topics: list[TimelineTopicCount],
    dominant_topic: str | None,
    emerging_topics: list[str],
    range_key: str,
) -> str:
    period_label = {
        "7d": "This week",
        "30d": "This month",
        "all": "Across your saved history",
    }.get(range_key, "In this period")
    topic_names = [topic.name for topic in top_topics[:3]]
    if not topic_names:
        return "Not enough activity yet to generate insights."
    if len(topic_names) == 1:
        summary = f"{period_label} you focused mainly on {topic_names[0]}."
    elif len(topic_names) == 2:
        summary = f"{period_label} you focused on {topic_names[0]} and {topic_names[1]}."
    else:
        summary = f"{period_label} you focused on {topic_names[0]}, {topic_names[1]}, and {topic_names[2]}."
    if dominant_topic and emerging_topics and emerging_topics[0] != dominant_topic:
        summary += f" {emerging_topics[0]} is starting to emerge in your recent knowledge."
    return summary


def _build_suggestions(top_topics: list[TimelineTopicCount], emerging_topics: list[str]) -> list[str]:
    suggestions: list[str] = []
    topic_names = [topic.name for topic in top_topics[:4]]

    if any("Embedding" in name or "Semantic Search" in name or "Retrieval Augmented Generation" in name for name in topic_names):
        suggestions.append("Your AI system notes are deepening. Consider grouping them into a dedicated architecture or RAG reference section.")
    if any("Mushroom Farming" in name or "Hydroponic Farming" in name or "Farm Business" in name for name in topic_names):
        suggestions.append("Your farming knowledge is growing. Consider creating a focused business or operations collection for those notes.")
    if any("Vedic Mathematics" in name or "Mathematics" in name for name in topic_names):
        suggestions.append("Your Vedic math notes are gaining depth. Consider organizing them into techniques, sutras, and worked examples.")
    if any("Knowledge Management" in name or "AI Life Architect" in name for name in topic_names):
        suggestions.append("You have enough system-design material to document your personal knowledge workflow more explicitly.")
    if any("Travel / Spiritual" in name for name in topic_names):
        suggestions.append("Your spiritual and travel notes are accumulating. Consider curating them into a dedicated journey or pilgrimage collection.")
    for topic in emerging_topics:
        if topic == "Vedic Mathematics":
            suggestions.append("Vedic Mathematics is emerging in your recent saves. It may be worth creating a dedicated practice track for it.")
            break

    deduped: list[str] = []
    seen = set()
    for suggestion in suggestions:
        if suggestion in seen:
            continue
        seen.add(suggestion)
        deduped.append(suggestion)
    return deduped
