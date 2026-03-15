from collections import Counter, defaultdict

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.models.content_topic import ContentTopic
from app.models.knowledge import KnowledgeItem
from app.models.topic import Topic
from app.services.learning_path_config import LEARNING_PATHS
from app.services.topic_service import get_raw_topics_with_counts


COVERED_COVERAGE_THRESHOLD = 8
DOMAIN_PRIORITY = {
    "AI": 0,
    "Knowledge": 1,
    "Agriculture": 2,
    "Business": 3,
    "Math": 4,
    "Mathematics": 4,
    "Spiritual": 5,
    "General": 6,
}


def _topic_name_variants(name: str) -> set[str]:
    normalized = (name or "").strip().lower()
    variants = {normalized}
    if normalized == "rag":
        variants.add("retrieval augmented generation")
    if normalized == "retrieval augmented generation":
        variants.add("rag")
    if normalized == "llms":
        variants.add("llm systems")
    if normalized == "llm systems":
        variants.add("llms")
    if normalized == "ai knowledge architect":
        variants.add("ai life architect")
    if normalized == "ai life architect":
        variants.add("ai knowledge architect")
    return variants


def _normalize_topic_records(topics: list[tuple[Topic, int]]) -> tuple[set[str], Counter[str]]:
    existing_topics: set[str] = set()
    linked_item_counts: Counter[str] = Counter()

    for topic, count in topics:
        for variant in _topic_name_variants(topic.name):
            existing_topics.add(variant)
            linked_item_counts[variant] = count

    return existing_topics, linked_item_counts


def _build_topic_relationship_stats(items: list[KnowledgeItem]) -> tuple[Counter[str], dict[str, set[str]]]:
    revisit_counts: Counter[str] = Counter()
    related_topics: dict[str, set[str]] = defaultdict(set)

    for item in items:
        topic_names = sorted(
            {
                content_topic.topic.name
                for content_topic in item.content_topics
                if content_topic.topic is not None and content_topic.topic.name
            }
        )
        if not topic_names:
            continue

        for topic_name in topic_names:
            revisit_counts[topic_name] += 1
        for topic_name in topic_names:
            related_topics[topic_name].update({name for name in topic_names if name != topic_name})

    return revisit_counts, related_topics


def _topic_coverage(topic_name: str, linked_item_counts: Counter[str], revisit_counts: Counter[str], related_topics: dict[str, set[str]]) -> dict[str, int | str]:
    variants = _topic_name_variants(topic_name)
    linked_item_count = max([linked_item_counts.get(variant, 0) for variant in variants], default=0)
    matching_related_names = [name for name in related_topics if name.lower() in variants]
    related_topic_count = max([len(related_topics.get(name, set())) for name in matching_related_names], default=0)
    revisit_count = max([revisit_counts.get(name, 0) for name in matching_related_names], default=0)
    revisit_count = max(0, revisit_count - 1)
    coverage_score = linked_item_count * 2 + related_topic_count + revisit_count

    if linked_item_count == 0:
        state = "missing"
        action = "add"
    elif linked_item_count >= 3 or coverage_score >= COVERED_COVERAGE_THRESHOLD:
        state = "covered"
        action = "none"
    else:
        state = "started"
        action = "focus"

    return {
        "state": state,
        "action": action,
        "linked_item_count": linked_item_count,
        "related_topic_count": related_topic_count,
        "revisit_count": revisit_count,
        "coverage_score": coverage_score,
    }


def _apply_path_sequence(raw_topics: list[dict[str, str]]) -> list[dict[str, str]]:
    sequenced_topics: list[dict[str, str]] = []
    encountered_gap = False

    for topic in raw_topics:
        next_topic = {**topic}
        state = next_topic["state"]

        if encountered_gap and state == "covered":
            next_topic["state"] = "started" if next_topic["action"] == "none" else next_topic["state"]
            next_topic["action"] = "focus"
        elif encountered_gap and state == "started":
            next_topic["action"] = "focus"

        if next_topic["state"] != "covered":
            encountered_gap = True

        sequenced_topics.append(next_topic)

    return sequenced_topics


def build_learning_paths(db: Session, user_id: int) -> list[dict]:
    topic_rows = get_raw_topics_with_counts(db, user_id)
    items = db.scalars(
        select(KnowledgeItem)
        .options(selectinload(KnowledgeItem.content_topics).selectinload(ContentTopic.topic))
        .where(KnowledgeItem.user_id == user_id)
        .order_by(desc(KnowledgeItem.updated_at))
    ).all()

    existing_topics, linked_item_counts = _normalize_topic_records(topic_rows)
    revisit_counts, related_topics = _build_topic_relationship_stats(items)
    path_summaries: list[dict] = []

    for path in LEARNING_PATHS:
        raw_topics_payload: list[dict] = []

        for topic_name in path["topics"]:
            coverage = _topic_coverage(topic_name, linked_item_counts, revisit_counts, related_topics)
            raw_topics_payload.append(
                {
                    "topic": topic_name,
                    "state": coverage["state"],
                    "action": coverage["action"],
                }
            )

        topics_payload = _apply_path_sequence(raw_topics_payload)
        covered_count = sum(1 for topic in topics_payload if topic["state"] == "covered")
        started_count = sum(1 for topic in topics_payload if topic["state"] == "started")
        total_count = len(topics_payload)
        next_topic = next((topic for topic in topics_payload if topic["state"] != "covered"), None)
        next_index = next((index for index, topic in enumerate(topics_payload) if topic["state"] != "covered"), total_count)
        completed_topics = [topic["topic"] for topic in topics_payload if topic["state"] == "covered"]
        upcoming_topics = [topic["topic"] for topic in topics_payload[next_index + 1:] if topic["state"] != "covered"]
        progress_percent = int(round((covered_count / total_count) * 100)) if total_count else 0
        active_count = covered_count + started_count

        path_summaries.append(
            {
                "path_name": path["path_name"],
                "domain": path["domain"],
                "progress_percent": progress_percent,
                "covered_count": covered_count,
                "total_count": total_count,
                "next_topic": {**next_topic, "domain": path["domain"]} if next_topic else None,
                "topics": topics_payload,
                "completed_topics": completed_topics,
                "upcoming_topics": upcoming_topics,
                "active_count": active_count,
                "domain_priority": DOMAIN_PRIORITY.get(path["domain"], 9),
                "path_exists": any(variant in existing_topics for topic_name in path["topics"] for variant in _topic_name_variants(topic_name)),
            }
        )

    return sorted(
        path_summaries,
        key=lambda item: (
            0 if item["next_topic"] else 1,
            -item["active_count"],
            -item["covered_count"],
            item["domain_priority"],
            item["path_name"].lower(),
        ),
    )
