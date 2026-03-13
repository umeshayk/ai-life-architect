from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.models.content_topic import ContentTopic
from app.models.knowledge import KnowledgeItem
from app.schemas.evolution import EvolutionResponse, EvolutionSeries
from app.services.forecast_service import build_knowledge_forecast
from app.schemas.timeline import (
    KnowledgeGrowthPoint,
    KnowledgeGrowthResponse,
    KnowledgeForecast,
    KnowledgeProject,
    KnowledgeStrategy,
    StrategyStep,
    TimelineGroup,
    TimelineInsights,
    TimelineItem,
    TimelineResponse,
    TimelineSummary,
    TimelineTopicCount,
)


VALID_RANGES = {"7d", "30d", "all"}
VALID_GROUPS = {"day", "week", "month"}
CURIOUS_TOPIC_MAP = {
    "Embeddings": ["Vector Databases", "Index Optimization", "Embedding Evaluation"],
    "Semantic Search": ["Hybrid Search", "Query Expansion", "Search Ranking"],
    "Retrieval Augmented Generation": ["Retrieval Optimization", "Context Compression", "Chunking Strategy"],
    "LLM Systems": ["Prompt Engineering", "Model Evaluation", "Inference Optimization"],
    "Vector Databases": ["ANN Indexes", "Hybrid Search", "Metadata Filtering"],
    "Mushroom Farming": ["Mushroom Business Models", "Spawn Quality", "Yield Optimization"],
    "Hydroponic Farming": ["Controlled Environment Agriculture", "Nutrient Scheduling", "Greenhouse Automation"],
    "Farm Business": ["Unit Economics", "Go To Market", "Local Distribution"],
    "Vedic Mathematics": ["Vedic Multiplication Techniques", "Mental Math Speed Techniques", "Sutra Practice Systems"],
    "Mathematics": ["Mental Math Speed Techniques", "Pattern Recognition", "Worked Example Sets"],
    "Knowledge Management": ["Note Linking Systems", "Knowledge Review Rituals", "Second Brain Workflows"],
    "AI Life Architect": ["Personal Knowledge Architecture", "Agent Workflows", "Memory System Design"],
    "Travel / Spiritual": ["Pilgrimage Planning", "Temple Research", "Travel Journaling"],
}
KNOWLEDGE_GAP_MAP = {
    "Embeddings": ["Vector Databases", "Embedding Evaluation", "Vector Indexing"],
    "Semantic Search": ["Hybrid Search", "Index Optimization", "Vector Indexing"],
    "Retrieval Augmented Generation": ["Retrieval Optimization", "Context Compression", "Chunking Strategy"],
    "Mushroom Farming": ["Spawn Quality", "Substrate Sterilization", "Mushroom Business Models"],
    "Hydroponic Farming": ["Climate Control", "Controlled Environment Agriculture", "Nutrient Scheduling"],
    "Vedic Mathematics": ["Vedic Multiplication", "Mental Math Speed Techniques", "Sutra Practice Systems"],
}
STRATEGY_MAPS = [
    {
        "domain": "AI Systems",
        "seeds": {"Embeddings", "Semantic Search", "Retrieval Augmented Generation", "LLM Systems", "Vector Databases"},
        "path": ["Embeddings", "Vector Databases", "Hybrid Search", "Retrieval Optimization", "Evaluation Metrics"],
    },
    {
        "domain": "Agriculture",
        "seeds": {"Mushroom Farming", "Hydroponic Farming", "Farm Business"},
        "path": ["Mushroom Farming", "Spawn Quality", "Substrate Sterilization", "Yield Optimization", "Mushroom Business Models"],
    },
    {
        "domain": "Mathematics",
        "seeds": {"Vedic Mathematics", "Mathematics"},
        "path": ["Vedic Mathematics", "Nikhilam Sutra", "Urdhva Tiryagbhyam", "Speed Multiplication", "Mental Math"],
    },
]
PROJECT_MAPS = [
    {
        "name": "AI Systems",
        "seeds": {"Embeddings", "Semantic Search", "Vector Databases", "Retrieval Augmented Generation", "LLM Systems"},
        "topics": ["Embeddings", "Semantic Search", "Vector Databases", "Hybrid Search", "Retrieval Optimization"],
    },
    {
        "name": "Agriculture",
        "seeds": {
            "Mushroom Farming",
            "Hydroponic Farming",
            "Spawn Quality",
            "Substrate Sterilization",
            "Yield Optimization",
            "Climate Control",
            "Controlled Environment Agriculture",
            "Farm Business",
        },
        "topics": [
            "Mushroom Farming",
            "Hydroponic Farming",
            "Spawn Quality",
            "Substrate Sterilization",
            "Yield Optimization",
            "Climate Control",
        ],
    },
    {
        "name": "Vedic Mathematics",
        "seeds": {"Vedic Mathematics", "Nikhilam Sutra", "Urdhva Tiryagbhyam", "Speed Multiplication", "Mental Math"},
        "topics": ["Vedic Mathematics", "Nikhilam Sutra", "Urdhva Tiryagbhyam", "Speed Multiplication", "Mental Math"],
    },
]


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
    evolution = _build_evolution_data(items, all_items, normalized_range, normalized_group, limit_topics=8)
    summary = _build_summary(groups, top_topics)
    insights = _build_insights(items, all_items, top_topics, normalized_range, evolution)
    return TimelineResponse(groups=groups, top_topics=top_topics, summary=summary, insights=insights)


def get_timeline_evolution(
    db: Session,
    user_id: int,
    range_key: str = "30d",
    group_by: str = "week",
    limit_topics: int = 5,
) -> EvolutionResponse:
    normalized_range = range_key if range_key in VALID_RANGES else "30d"
    normalized_group = group_by if group_by in VALID_GROUPS else "week"
    bounded_limit = max(1, min(limit_topics, 8))
    items = _load_items(db, user_id, normalized_range)
    if not items:
        return EvolutionResponse(labels=[], series=[])

    all_items = _load_items(db, user_id, "all")
    return _build_evolution_data(items, all_items, normalized_range, normalized_group, bounded_limit)


def get_knowledge_growth(db: Session, user_id: int) -> KnowledgeGrowthResponse:
    all_items = list(reversed(_load_items(db, user_id, "all")))
    if not all_items:
        return KnowledgeGrowthResponse(
            notes_count=0,
            topics_count=0,
            this_week_count=0,
            previous_week_count=0,
            weekly_growth_delta=0,
            fastest_topic=None,
            timeline=[],
        )

    now = datetime.now(UTC)
    this_week_cutoff = now - timedelta(days=7)
    previous_week_cutoff = now - timedelta(days=14)
    this_week_count = sum(1 for item in all_items if item.created_at.astimezone(UTC) >= this_week_cutoff)
    previous_week_count = sum(
        1
        for item in all_items
        if previous_week_cutoff <= item.created_at.astimezone(UTC) < this_week_cutoff
    )
    weekly_growth_delta = this_week_count - previous_week_count
    topic_counts: Counter[str] = Counter()
    cumulative_topics: set[str] = set()
    monthly_notes: dict[str, int] = {}
    monthly_topics: dict[str, int] = {}

    current = all_items[0].created_at.astimezone(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    item_index = 0
    notes_total = 0
    timeline: list[KnowledgeGrowthPoint] = []

    while current <= end:
        while item_index < len(all_items):
            item_month = all_items[item_index].created_at.astimezone(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if item_month > current:
                break

            item = all_items[item_index]
            notes_total += 1
            for content_topic in item.content_topics:
                if content_topic.topic is not None:
                    topic_name = content_topic.topic.name
                    cumulative_topics.add(topic_name)
                    topic_counts[topic_name] += 1
            item_index += 1

        label = current.strftime("%b") if current.year == end.year else current.strftime("%b %Y")
        monthly_notes[label] = notes_total
        monthly_topics[label] = len(cumulative_topics)
        timeline.append(
            KnowledgeGrowthPoint(
                month=label,
                notes=monthly_notes[label],
                topics=monthly_topics[label],
            )
        )

        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)

    return KnowledgeGrowthResponse(
        notes_count=len(all_items),
        topics_count=len(cumulative_topics),
        this_week_count=this_week_count,
        previous_week_count=previous_week_count,
        weekly_growth_delta=weekly_growth_delta,
        fastest_topic=topic_counts.most_common(1)[0][0] if topic_counts else None,
        timeline=timeline,
    )


def _build_evolution_data(
    items: list[KnowledgeItem],
    all_items: list[KnowledgeItem],
    range_key: str,
    group_by: str,
    limit_topics: int,
) -> EvolutionResponse:
    start_date, end_date = _evolution_window(items, all_items, range_key)
    labels = _generate_bucket_labels(start_date, end_date, group_by)
    if not labels:
        return EvolutionResponse(labels=[], series=[])

    bucket_topic_counts: dict[str, Counter[str]] = defaultdict(Counter)
    topic_totals: Counter[str] = Counter()

    for item in items:
        bucket = _bucket_key(item.created_at, group_by)
        topic_names = sorted(
            {
                content_topic.topic.name
                for content_topic in item.content_topics
                if content_topic.topic is not None
            }
        )
        for topic_name in topic_names:
            bucket_topic_counts[bucket][topic_name] += 1
            topic_totals[topic_name] += 1

    top_topic_names = [
        topic_name
        for topic_name, _ in topic_totals.most_common(limit_topics)
    ]
    series = [
        EvolutionSeries(
            topic=topic_name,
            values=[bucket_topic_counts[label].get(topic_name, 0) for label in labels],
        )
        for topic_name in top_topic_names
    ]
    return EvolutionResponse(labels=labels, series=series)


def _evolution_window(
    items: list[KnowledgeItem],
    all_items: list[KnowledgeItem],
    range_key: str,
) -> tuple[datetime, datetime]:
    end_date = datetime.now(UTC)
    start_date = _range_start(range_key)
    if start_date is not None:
        return start_date, end_date

    earliest_item = min(all_items, key=lambda item: item.created_at, default=None)
    if earliest_item is None:
        return end_date, end_date
    return earliest_item.created_at.astimezone(UTC), end_date


def _generate_bucket_labels(start_date: datetime, end_date: datetime, group_by: str) -> list[str]:
    normalized_start = start_date.astimezone(UTC)
    normalized_end = end_date.astimezone(UTC)

    if group_by == "day":
        current = normalized_start.replace(hour=0, minute=0, second=0, microsecond=0)
        final = normalized_end.replace(hour=0, minute=0, second=0, microsecond=0)
        labels: list[str] = []
        while current <= final:
            labels.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)
        return labels

    if group_by == "month":
        current = normalized_start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        final = normalized_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        labels: list[str] = []
        while current <= final:
            labels.append(current.strftime("%Y-%m"))
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        return labels

    current = (normalized_start - timedelta(days=normalized_start.weekday())).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    final = (normalized_end - timedelta(days=normalized_end.weekday())).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    labels = []
    while current <= final:
        iso_year, iso_week, _ = current.isocalendar()
        labels.append(f"{iso_year}-W{iso_week:02d}")
        current += timedelta(days=7)
    return labels


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
    evolution: EvolutionResponse,
) -> TimelineInsights:
    if len(items) < 2 or not top_topics:
        return TimelineInsights(
            summary="Not enough activity yet to generate insights.",
            emerging_topics=[],
            dominant_topic=None,
            fastest_topic=None,
            emerging_topic=None,
            stable_topic=None,
            suggested_topics=[],
            knowledge_gaps=[],
            strategies=[],
            projects=[],
            forecast=[],
            suggestions=[],
        )

    all_topic_counts: Counter[str] = Counter()
    for item in all_items:
        for content_topic in item.content_topics:
            if content_topic.topic is not None:
                all_topic_counts[content_topic.topic.name] += 1

    dominant_topic = top_topics[0].name if top_topics else None
    emerging_topics = _detect_emerging_topics(top_topics, all_topic_counts, range_key)
    fastest_topic, emerging_topic, stable_topic = _detect_momentum(evolution)
    emerging_topic = _select_curated_emerging_topic(evolution, emerging_topics, fastest_topic, emerging_topic)
    suggested_topics = _build_suggested_topics(top_topics, emerging_topics)
    knowledge_gaps = _build_knowledge_gaps(top_topics, emerging_topics, all_topic_counts)
    strategies = _build_knowledge_strategies(top_topics, emerging_topics, all_topic_counts)
    projects = _build_knowledge_projects(top_topics, emerging_topics, all_topic_counts)
    forecast = build_knowledge_forecast(top_topics, projects, evolution)
    summary = _build_insight_summary(top_topics, dominant_topic, emerging_topics, range_key)
    suggestions = _build_suggestions(top_topics, emerging_topics)

    return TimelineInsights(
        summary=summary,
        emerging_topics=emerging_topics,
        dominant_topic=dominant_topic,
        fastest_topic=fastest_topic,
        emerging_topic=emerging_topic,
        stable_topic=stable_topic,
        suggested_topics=suggested_topics,
        knowledge_gaps=knowledge_gaps,
        strategies=strategies,
        projects=projects,
        forecast=forecast,
        suggestions=suggestions[:3],
    )


def _build_suggested_topics(
    top_topics: list[TimelineTopicCount],
    emerging_topics: list[str],
) -> list[str]:
    seeds = [topic.name for topic in top_topics[:4]] + emerging_topics[:2]
    suggestions: list[str] = []
    seen = set()

    for seed in seeds:
        for related in CURIOUS_TOPIC_MAP.get(seed, []):
            if related in seen or related in seeds:
                continue
            seen.add(related)
            suggestions.append(related)
            if len(suggestions) >= 5:
                return suggestions

    return suggestions


def _build_knowledge_gaps(
    top_topics: list[TimelineTopicCount],
    emerging_topics: list[str],
    all_topic_counts: Counter[str],
) -> list[str]:
    seeds = [topic.name for topic in top_topics[:4]] + emerging_topics[:2]
    existing_topics = set(all_topic_counts.keys())
    gaps: list[str] = []
    seen = set()

    for seed in seeds:
        for related in KNOWLEDGE_GAP_MAP.get(seed, []):
            if related in existing_topics or related in seen or related in seeds:
                continue
            seen.add(related)
            gaps.append(related)
            if len(gaps) >= 5:
                return gaps

    return gaps


def _build_knowledge_strategies(
    top_topics: list[TimelineTopicCount],
    emerging_topics: list[str],
    all_topic_counts: Counter[str],
) -> list[KnowledgeStrategy]:
    seeds = {topic.name for topic in top_topics[:4]} | set(emerging_topics[:2])
    existing_topics = set(all_topic_counts.keys())
    strategies: list[KnowledgeStrategy] = []
    seen_domains = set()

    for config in STRATEGY_MAPS:
        if config["domain"] in seen_domains:
            continue
        if not seeds.intersection(config["seeds"]):
            continue

        steps = []
        seen_topics = set()
        for topic_name in config["path"]:
            if topic_name in seen_topics:
                continue
            seen_topics.add(topic_name)
            steps.append(
                StrategyStep(
                    topic=topic_name,
                    completed=topic_name in existing_topics,
                )
            )
        strategies.append(KnowledgeStrategy(domain=config["domain"], path=steps))
        seen_domains.add(config["domain"])

    return strategies[:2]


def _build_knowledge_projects(
    top_topics: list[TimelineTopicCount],
    emerging_topics: list[str],
    all_topic_counts: Counter[str],
) -> list[KnowledgeProject]:
    seeds = {topic.name for topic in top_topics[:5]} | set(emerging_topics[:2])
    existing_topics = set(all_topic_counts.keys())
    projects: list[KnowledgeProject] = []
    seen_names = set()

    for config in PROJECT_MAPS:
        if config["name"] in seen_names:
            continue
        matched_topics = [topic for topic in config["topics"] if topic in existing_topics]
        if len(set(config["seeds"]).intersection(seeds)) == 0 and not matched_topics:
            continue

        total_topics = len(config["topics"])
        completed_topics = len(matched_topics)
        progress = round(completed_topics / total_topics, 2) if total_topics else 0.0
        next_step = next((topic for topic in config["topics"] if topic not in existing_topics), None)
        visible_topics = matched_topics[:4] if matched_topics else config["topics"][:3]

        projects.append(
            KnowledgeProject(
                name=f"{config['name']} Project",
                topics=visible_topics,
                progress=progress,
                next_step=next_step,
            )
        )
        seen_names.add(config["name"])

    projects.sort(key=lambda project: (-project.progress, project.name))
    return projects[:3]


def _select_curated_emerging_topic(
    evolution: EvolutionResponse,
    emerging_topics: list[str],
    fastest_topic: str | None,
    fallback_topic: str | None,
) -> str | None:
    if len(evolution.labels) < 2:
        return fallback_topic

    momentum_map = {
        series.topic: (series.values[-2], series.values[-1])
        for series in evolution.series
    }
    for topic_name in emerging_topics:
        previous, current = momentum_map.get(topic_name, (0, 0))
        if topic_name != fastest_topic and previous == 0 and current > 0:
            return topic_name
    return fallback_topic


def _detect_momentum(evolution: EvolutionResponse) -> tuple[str | None, str | None, str | None]:
    if len(evolution.labels) < 2 or not evolution.series:
        return None, None, None

    fastest_topic = None
    fastest_growth = -1
    emerging_topic = None
    stable_candidates: list[tuple[int, int, str]] = []
    growth_candidates: list[tuple[int, int, str]] = []
    emerging_candidates: list[tuple[int, str]] = []

    for series in evolution.series:
        previous = series.values[-2]
        current = series.values[-1]
        growth = current - previous

        growth_candidates.append((-growth, -current, series.topic))

        if previous == 0 and current > 0:
            emerging_candidates.append((-current, series.topic))
        if growth > fastest_growth:
            fastest_growth = growth
            fastest_topic = series.topic

        if previous > 0 and current > 0:
            stable_candidates.append((abs(growth), -current, series.topic))

    if fastest_topic is not None:
        for _, topic_name in sorted(emerging_candidates):
            if topic_name != fastest_topic:
                emerging_topic = topic_name
                break
    if emerging_topic is None and emerging_candidates:
        emerging_topic = sorted(emerging_candidates)[0][1]

    stable_topic = None
    for _, _, topic_name in sorted(stable_candidates):
        if topic_name != fastest_topic and topic_name != emerging_topic:
            stable_topic = topic_name
            break
    if stable_topic is None and stable_candidates:
        stable_topic = sorted(stable_candidates)[0][2]
    if fastest_topic is None and growth_candidates:
        fastest_topic = sorted(growth_candidates)[0][2]

    return fastest_topic, emerging_topic, stable_topic


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
