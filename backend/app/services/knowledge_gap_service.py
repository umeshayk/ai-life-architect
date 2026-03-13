from collections import Counter, defaultdict

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.models.content_topic import ContentTopic
from app.models.knowledge import KnowledgeItem
from app.models.topic import Topic
from app.services.topic_service import get_raw_topics_with_counts


LEARNING_PATHS: list[dict[str, object]] = [
    {
        "name": "AI_RETRIEVAL_STACK",
        "domain": "AI",
        "topics": [
            "Embeddings",
            "Vector Databases",
            "Semantic Search",
            "Hybrid Search",
            "Retrieval Augmented Generation",
            "Retrieval Optimization",
            "LLM Systems",
        ],
    },
    {
        "name": "AGRICULTURE_STACK",
        "domain": "Agriculture",
        "topics": [
            "Mushroom Farming",
            "Hydroponic Farming",
            "Controlled Environment Agriculture",
            "Farm Automation",
            "Yield Optimization",
        ],
    },
    {
        "name": "KNOWLEDGE_STACK",
        "domain": "Knowledge",
        "topics": [
            "Knowledge Management",
            "Action Planning",
            "Personal Knowledge Systems",
            "AI Knowledge Architect",
        ],
    },
    {
        "name": "REAL_ESTATE_STACK",
        "domain": "Business",
        "topics": [
            "Real Estate",
            "Property Trends",
            "Real Estate Data Analytics",
        ],
    },
]

MIN_PATTERN_MATCHES = 2
MAX_SUGGESTIONS = 10
DEFAULT_NEXT_LIMIT = 5
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


def _normalize_topic_records(topics: list[tuple[Topic, int]]) -> tuple[set[str], Counter[str], dict[str, str]]:
    existing_topics: set[str] = set()
    linked_item_counts: Counter[str] = Counter()
    canonical_names: dict[str, str] = {}

    for topic, count in topics:
        for variant in _topic_name_variants(topic.name):
            existing_topics.add(variant)
            linked_item_counts[variant] = count
            canonical_names[variant] = topic.name

    return existing_topics, linked_item_counts, canonical_names


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


def _format_topic_list(topic_names: list[str]) -> str:
    if not topic_names:
        return ""
    if len(topic_names) == 1:
        return topic_names[0]
    if len(topic_names) == 2:
        return f"{topic_names[0]} and {topic_names[1]}"
    return f"{', '.join(topic_names[:-1])}, and {topic_names[-1]}"


def _topic_coverage(
    topic_name: str,
    linked_item_counts: Counter[str],
    revisit_counts: Counter[str],
    related_topics: dict[str, set[str]],
) -> dict[str, int | str]:
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


def _build_reason(pattern_topics: list[str], coverage_by_topic: dict[str, dict[str, int | str]], index: int) -> str:
    topic_name = pattern_topics[index]
    state = coverage_by_topic[topic_name]["state"]
    prerequisites = pattern_topics[:index]
    completed = [name for name in prerequisites if coverage_by_topic[name]["state"] in {"covered", "started"}]
    missing = [name for name in prerequisites if coverage_by_topic[name]["state"] == "missing"]

    if not prerequisites:
        return f"{topic_name} is the first step in this learning path."

    if state == "started":
        if completed:
            return f"You have already started {topic_name}. Build on {_format_topic_list(completed)} next."
        return f"You have already started {topic_name}. Focus here next to strengthen this part of the learning path."

    if not missing and completed:
        return f"You already know {_format_topic_list(completed)}."

    if len(missing) == 1 and missing[0] == prerequisites[-1]:
        return f"{missing[0]} is the next step toward {topic_name}."

    if completed and missing:
        return f"You already know {_format_topic_list(completed)}. Build through {_format_topic_list(missing[:3])} before moving to {topic_name}."

    return f"Build through {_format_topic_list(missing[:3])} before moving to {topic_name}."


def _compute_confidence(pattern_topics: list[str], coverage_by_topic: dict[str, dict[str, int | str]], index: int, state: str) -> float:
    prerequisites = pattern_topics[:index]
    if not prerequisites:
        base_confidence = 0.64
    else:
        covered_count = sum(1 for name in prerequisites if coverage_by_topic[name]["state"] == "covered")
        started_count = sum(1 for name in prerequisites if coverage_by_topic[name]["state"] == "started")
        completion_ratio = (covered_count + started_count * 0.6) / len(prerequisites)
        queue_bonus = max(0.04, 0.22 - index * 0.02)
        base_confidence = 0.48 + completion_ratio * 0.28 + queue_bonus

    if state == "started":
        base_confidence += 0.08

    return round(min(0.98, base_confidence), 2)


def _all_previous_ready(pattern_topics: list[str], coverage_by_topic: dict[str, dict[str, int | str]], index: int) -> bool:
    return all(coverage_by_topic[name]["state"] != "missing" for name in pattern_topics[:index])


def _frontier_index(pattern_topics: list[str], coverage_by_topic: dict[str, dict[str, int | str]]) -> int | None:
    for index, topic_name in enumerate(pattern_topics):
        if coverage_by_topic[topic_name]["state"] == "missing" and _all_previous_ready(pattern_topics, coverage_by_topic, index):
            return index

    for index, topic_name in enumerate(pattern_topics):
        if coverage_by_topic[topic_name]["state"] == "started" and _all_previous_ready(pattern_topics, coverage_by_topic, index):
            return index

    return None


def _collect_learning_candidates(db: Session, user_id: int) -> list[dict]:
    topic_rows = get_raw_topics_with_counts(db, user_id)
    items = db.scalars(
        select(KnowledgeItem)
        .options(selectinload(KnowledgeItem.content_topics).selectinload(ContentTopic.topic))
        .where(KnowledgeItem.user_id == user_id)
        .order_by(desc(KnowledgeItem.updated_at))
    ).all()

    if not topic_rows and not items:
        return []

    existing_topics, linked_item_counts, _canonical_names = _normalize_topic_records(topic_rows)
    revisit_counts, related_topics = _build_topic_relationship_stats(items)
    candidates: list[dict] = []

    for path in LEARNING_PATHS:
        pattern_topics = path["topics"]
        coverage_by_topic = {
            topic_name: _topic_coverage(topic_name, linked_item_counts, revisit_counts, related_topics)
            for topic_name in pattern_topics
        }
        active_count = sum(1 for topic_name in pattern_topics if coverage_by_topic[topic_name]["state"] != "missing")
        if active_count < MIN_PATTERN_MATCHES:
            continue

        frontier_index = _frontier_index(pattern_topics, coverage_by_topic)
        if frontier_index is None:
            continue

        for index, topic_name in enumerate(pattern_topics):
            coverage = coverage_by_topic[topic_name]
            state = coverage["state"]
            if state == "covered":
                continue

            prerequisites = pattern_topics[:index]
            missing_prereq_count = sum(1 for name in prerequisites if coverage_by_topic[name]["state"] == "missing")
            if prerequisites and missing_prereq_count == len(prerequisites):
                continue
            if index < frontier_index and state != "started":
                continue

            if index > frontier_index and missing_prereq_count > 0:
                queue_stage = 1 + missing_prereq_count
            elif index < frontier_index:
                queue_stage = 4
            elif index == frontier_index:
                queue_stage = 0
            else:
                queue_stage = 1

            future_distance = max(0, index - frontier_index)
            state_priority = 1 if state == "started" and index < frontier_index else 0

            candidates.append(
                {
                    "topic": topic_name,
                    "reason": _build_reason(pattern_topics, coverage_by_topic, index),
                    "confidence": _compute_confidence(pattern_topics, coverage_by_topic, index, state),
                    "domain": path["domain"],
                    "state": state,
                    "action": coverage["action"],
                    "topic_exists": any(variant in existing_topics for variant in _topic_name_variants(topic_name)),
                    "missing_prereq_count": missing_prereq_count,
                    "stack_index": index,
                    "frontier_index": frontier_index,
                    "queue_stage": queue_stage,
                    "future_distance": future_distance,
                    "state_priority": state_priority,
                    "domain_priority": DOMAIN_PRIORITY.get(path["domain"], 9),
                    "active_count": active_count,
                }
            )

    deduped: dict[str, dict] = {}
    for candidate in candidates:
        existing = deduped.get(candidate["topic"].lower())
        candidate_rank = (
            candidate["queue_stage"],
            candidate["future_distance"],
            candidate["missing_prereq_count"],
            candidate["state_priority"],
            -candidate["confidence"],
            candidate["domain_priority"],
            -candidate["active_count"],
        )
        if existing is None:
            deduped[candidate["topic"].lower()] = {**candidate, "_rank": candidate_rank}
            continue

        if candidate_rank < existing["_rank"]:
            deduped[candidate["topic"].lower()] = {**candidate, "_rank": candidate_rank}

    ranked = sorted(
        deduped.values(),
        key=lambda item: (
            item["queue_stage"],
            item["future_distance"],
            item["missing_prereq_count"],
            item["state_priority"],
            -item["confidence"],
            item["domain_priority"],
            -item["active_count"],
            item["topic"].lower(),
        ),
    )
    return ranked


def get_next_learning_topics(db: Session, user_id: int, limit: int = DEFAULT_NEXT_LIMIT) -> list[dict]:
    ranked = _collect_learning_candidates(db, user_id)
    return [
        {
            "topic": item["topic"],
            "reason": item["reason"],
            "confidence": item["confidence"],
            "domain": item["domain"],
            "state": item["state"],
            "action": item["action"],
            "priority": index + 1,
            "topic_exists": item["topic_exists"],
        }
        for index, item in enumerate(ranked[:limit])
    ]


def build_knowledge_gap_suggestions(db: Session, user_id: int) -> list[dict]:
    ranked = _collect_learning_candidates(db, user_id)
    return [
        {
            "suggested_topic": item["topic"],
            "reason": item["reason"],
            "confidence": item["confidence"],
            "domain": item["domain"],
            "topic_exists": item["topic_exists"],
            "state": item["state"],
            "action": item["action"],
        }
        for item in ranked[:MAX_SUGGESTIONS]
    ]
