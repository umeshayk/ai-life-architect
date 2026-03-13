from collections import Counter, defaultdict

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.models.content_topic import ContentTopic
from app.models.knowledge import KnowledgeItem
from app.models.topic import Topic
from app.services.topic_service import get_raw_topics_with_counts


KNOWLEDGE_PATTERNS: list[dict[str, object]] = [
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
    {
        "name": "KNOWLEDGE_SYSTEMS",
        "domain": "Knowledge",
        "topics": [
            "Knowledge Management",
            "AI Life Architect",
            "Semantic Search",
            "Action Planning",
        ],
    },
]
MIN_PATTERN_MATCHES = 2
MAX_SUGGESTIONS = 10
STARTED_COVERAGE_THRESHOLD = 6
COVERED_COVERAGE_THRESHOLD = 8


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
            siblings = {name for name in topic_names if name != topic_name}
            related_topics[topic_name].update(siblings)

    return revisit_counts, related_topics


def _format_topic_list(topic_names: list[str]) -> str:
    if not topic_names:
        return ""
    if len(topic_names) == 1:
        return topic_names[0]
    if len(topic_names) == 2:
        return f"{topic_names[0]} and {topic_names[1]}"
    return f"{', '.join(topic_names[:-1])}, and {topic_names[-1]}"


def _build_reason(pattern_topics: list[str], matched_topics: list[str], missing_index: int) -> str:
    if missing_index == 0 or not matched_topics:
        return f"{pattern_topics[0]} is the first step in this learning path."

    previous_topics = pattern_topics[:missing_index]
    covered_previous = [topic for topic in previous_topics if topic in matched_topics]
    if missing_index == len(covered_previous):
        return f"You already know {_format_topic_list(covered_previous)}."

    previous_topic = pattern_topics[missing_index - 1]
    return f"{previous_topic} is already in place, and this is the next step in the learning path."


def _topic_coverage(topic_name: str, linked_item_counts: Counter[str], revisit_counts: Counter[str], related_topics: dict[str, set[str]]) -> dict[str, int | str]:
    variants = _topic_name_variants(topic_name)
    linked_item_count = max([linked_item_counts.get(variant, 0) for variant in variants], default=0)
    canonical_topic = next((variant for variant in variants if variant in related_topics), topic_name)
    related_topic_count = len(related_topics.get(canonical_topic, set()))
    revisit_count = max(0, linked_item_count - 1)
    coverage_score = linked_item_count * 2 + related_topic_count + revisit_count

    if linked_item_count == 0:
        return {
            "state": "missing",
            "action": "add",
            "linked_item_count": linked_item_count,
            "related_topic_count": related_topic_count,
            "revisit_count": revisit_count,
            "coverage_score": coverage_score,
        }

    if linked_item_count >= 3 or coverage_score >= COVERED_COVERAGE_THRESHOLD:
        return {
            "state": "covered",
            "action": "none",
            "linked_item_count": linked_item_count,
            "related_topic_count": related_topic_count,
            "revisit_count": revisit_count,
            "coverage_score": coverage_score,
        }

    return {
        "state": "started",
        "action": "focus",
        "linked_item_count": linked_item_count,
        "related_topic_count": related_topic_count,
        "revisit_count": revisit_count,
        "coverage_score": coverage_score,
    }


def build_knowledge_gap_suggestions(db: Session, user_id: int) -> list[dict]:
    topic_rows = get_raw_topics_with_counts(db, user_id)
    items = db.scalars(
        select(KnowledgeItem)
        .options(selectinload(KnowledgeItem.content_topics).selectinload(ContentTopic.topic))
        .where(KnowledgeItem.user_id == user_id)
        .order_by(desc(KnowledgeItem.updated_at))
    ).all()
    if not topic_rows and not items:
        return []

    existing_topics, linked_item_counts, canonical_names = _normalize_topic_records(topic_rows)
    revisit_counts, related_topics = _build_topic_relationship_stats(items)
    suggestions: list[dict] = []

    for pattern in KNOWLEDGE_PATTERNS:
        pattern_topics = pattern["topics"]
        matched_topics: list[str] = []
        coverage_by_topic: dict[str, dict[str, int | str]] = {}

        for topic_name in pattern_topics:
            coverage = _topic_coverage(topic_name, linked_item_counts, revisit_counts, related_topics)
            coverage_by_topic[topic_name] = coverage
            if coverage["state"] == "covered":
                matched_topics.append(canonical_names.get(topic_name.lower(), topic_name))

        if len(matched_topics) < MIN_PATTERN_MATCHES:
            continue

        for index, topic_name in enumerate(pattern_topics):
            coverage = coverage_by_topic[topic_name]
            state = coverage["state"]
            action = coverage["action"]
            if state == "covered":
                continue

            prerequisite_topics = pattern_topics[:index]
            covered_prerequisites = [name for name in prerequisite_topics if coverage_by_topic[name]["state"] == "covered"]
            started_prerequisites = [name for name in prerequisite_topics if coverage_by_topic[name]["state"] == "started"]

            if prerequisite_topics and not covered_prerequisites and not started_prerequisites:
                continue

            completion_ratio = len(covered_prerequisites) / max(len(prerequisite_topics), 1) if prerequisite_topics else 0
            progression_bonus = max(0, len(prerequisite_topics) - index * 0.1)
            confidence = round(min(0.98, 0.42 + completion_ratio * 0.3 + progression_bonus * 0.05), 2)
            if state == "started":
                confidence = max(confidence, 0.76)

            suggestions.append(
                {
                    "suggested_topic": topic_name,
                    "reason": _build_reason(pattern_topics, covered_prerequisites + started_prerequisites, index),
                    "confidence": confidence,
                    "domain": pattern["domain"],
                    "topic_exists": any(variant in existing_topics for variant in _topic_name_variants(topic_name)),
                    "state": state,
                    "action": action,
                    "_order": index,
                    "_domain_priority": 0 if pattern["domain"] == "AI" else 1,
                }
            )

    deduped: dict[str, dict] = {}
    for suggestion in suggestions:
        existing = deduped.get(suggestion["suggested_topic"])
        if existing is None or (suggestion["_order"], -suggestion["confidence"]) < (existing["_order"], -existing["confidence"]):
            deduped[suggestion["suggested_topic"]] = suggestion

    ranked = sorted(
        deduped.values(),
        key=lambda item: (item["_order"], -item["confidence"], item["_domain_priority"], item["suggested_topic"].lower()),
    )
    return [
        {
            "suggested_topic": item["suggested_topic"],
            "reason": item["reason"],
            "confidence": item["confidence"],
            "domain": item["domain"],
            "topic_exists": item["topic_exists"],
            "state": item["state"],
            "action": item["action"],
        }
        for item in ranked[:MAX_SUGGESTIONS]
    ]
