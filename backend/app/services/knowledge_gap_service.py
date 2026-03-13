from collections import Counter

from sqlalchemy.orm import Session

from app.models.topic import Topic
from app.services.topic_service import get_raw_topics_with_counts


KNOWLEDGE_PATTERNS: list[dict[str, object]] = [
    {
        "name": "AI_VECTOR_STACK",
        "domain": "AI",
        "topics": [
            "Embeddings",
            "Vector Databases",
            "Semantic Search",
            "Hybrid Search",
            "Retrieval Augmented Generation",
        ],
    },
    {
        "name": "AI_RETRIEVAL_SYSTEMS",
        "domain": "AI",
        "topics": [
            "Embeddings",
            "Semantic Search",
            "Retrieval Optimization",
            "Retrieval Augmented Generation",
            "LLM Systems",
        ],
    },
    {
        "name": "AI_AGENT_STACK",
        "domain": "AI",
        "topics": [
            "LLM Systems",
            "Retrieval Augmented Generation",
            "Knowledge Management",
            "Prompt Engineering",
            "Agent Workflows",
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
        "name": "MUSHROOM_OPERATIONS",
        "domain": "Agriculture",
        "topics": [
            "Mushroom Farming",
            "Spawn Quality",
            "Substrate Sterilization",
            "Climate Control",
            "Yield Optimization",
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
        "name": "PROPERTY_INTELLIGENCE",
        "domain": "Business",
        "topics": [
            "Real Estate",
            "Property Trends",
            "Market Research",
            "Data Visualization",
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
    {
        "name": "MATHEMATICS_LEARNING",
        "domain": "Mathematics",
        "topics": [
            "Mathematics",
            "Vedic Mathematics",
            "Mental Math",
        ],
    },
]
MIN_PATTERN_MATCHES = 2
MAX_MISSING_PER_PATTERN = 2
MAX_SUGGESTIONS = 10


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


def _normalize_known_topics(topics: list[tuple[Topic, int]]) -> tuple[set[str], Counter[str], dict[str, str]]:
    normalized: set[str] = set()
    counts_by_name: Counter[str] = Counter()
    canonical_names: dict[str, str] = {}
    for topic, count in topics:
        for variant in _topic_name_variants(topic.name):
            normalized.add(variant)
            counts_by_name[variant] = count
            canonical_names[variant] = topic.name
    return normalized, counts_by_name, canonical_names


def _format_topic_list(topic_names: list[str]) -> str:
    if not topic_names:
        return ""
    if len(topic_names) == 1:
        return topic_names[0]
    if len(topic_names) == 2:
        return f"{topic_names[0]} and {topic_names[1]}"
    return f"{', '.join(topic_names[:-1])}, and {topic_names[-1]}"


def _build_reason(matched_topics: list[str]) -> str:
    if not matched_topics:
        return "This suggestion completes a pattern in your knowledge graph."
    return f"You already know {_format_topic_list(matched_topics)}."


def build_knowledge_gap_suggestions(db: Session, user_id: int) -> list[dict]:
    topic_rows = get_raw_topics_with_counts(db, user_id)
    if not topic_rows:
        return []

    known_topics, topic_counts, canonical_names = _normalize_known_topics(topic_rows)
    suggestions: list[dict] = []

    for pattern in KNOWLEDGE_PATTERNS:
        pattern_topics = pattern["topics"]
        matched_topics: list[str] = []
        missing_topics: list[str] = []
        total_weight = 0
        matched_weight = 0

        for topic_name in pattern_topics:
            variants = _topic_name_variants(topic_name)
            topic_weight = max([topic_counts.get(variant, 0) for variant in variants], default=0) or 1
            total_weight += topic_weight
            if any(variant in known_topics for variant in variants):
                canonical = next((canonical_names[variant] for variant in variants if variant in canonical_names), topic_name)
                matched_topics.append(canonical)
                matched_weight += topic_weight
            else:
                missing_topics.append(topic_name)

        if len(matched_topics) < MIN_PATTERN_MATCHES:
            continue
        if not missing_topics or len(missing_topics) > MAX_MISSING_PER_PATTERN:
            continue

        completion_ratio = len(matched_topics) / len(pattern_topics)
        weighted_ratio = matched_weight / max(total_weight, 1)
        confidence = round(min(0.98, 0.38 + completion_ratio * 0.32 + weighted_ratio * 0.24), 2)

        for missing_topic in missing_topics:
            suggestions.append(
                {
                    "suggested_topic": missing_topic,
                    "reason": _build_reason(matched_topics),
                    "confidence": confidence,
                    "domain": pattern["domain"],
                    "_matched_count": len(matched_topics),
                    "_pattern_name": pattern["name"],
                }
            )

    deduped: dict[str, dict] = {}
    for suggestion in suggestions:
        existing = deduped.get(suggestion["suggested_topic"])
        if existing is None or suggestion["confidence"] > existing["confidence"]:
            deduped[suggestion["suggested_topic"]] = suggestion

    ranked = sorted(
        deduped.values(),
        key=lambda item: (-item["confidence"], -item["_matched_count"], item["suggested_topic"].lower()),
    )
    return [
        {
            "suggested_topic": item["suggested_topic"],
            "reason": item["reason"],
            "confidence": item["confidence"],
            "domain": item["domain"],
        }
        for item in ranked[:MAX_SUGGESTIONS]
    ]
