from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.models.content_topic import ContentTopic
from app.models.knowledge import KnowledgeItem
from app.models.topic import Topic
from app.schemas.timeline import TimelineGroup, TimelineItem, TimelineResponse, TimelineSummary, TimelineTopicCount


VALID_RANGES = {"7d", "30d", "all"}
VALID_GROUPS = {"day", "week", "month"}


def get_timeline(db: Session, user_id: int, range_key: str = "30d", group_by: str = "week") -> TimelineResponse:
    normalized_range = range_key if range_key in VALID_RANGES else "30d"
    normalized_group = group_by if group_by in VALID_GROUPS else "week"
    items = _load_items(db, user_id, normalized_range)

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
    return TimelineResponse(groups=groups, top_topics=top_topics, summary=summary)


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
