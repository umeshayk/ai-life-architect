from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.models.content_topic import ContentTopic
from app.models.knowledge import KnowledgeItem
from app.models.knowledge_gap_cache import KnowledgeGapCache
from app.models.topic import Topic
from app.services.learning_path_service import build_learning_paths
from app.services.ollama_service import generate_list
from app.services.topic_normalizer_service import canonical_topic_key, normalize_topic_label


logger = logging.getLogger(__name__)
CACHE_TTL_HOURS = 24
RULE_CONFIDENCE_THRESHOLD = 0.8
RULE_MIN_SUGGESTIONS = 2
MAX_PATH_GAPS = 5
GENERIC_AI_JUNK = {
    "concept",
    "concepts",
    "topic",
    "topics",
    "system",
    "systems",
    "method",
    "methods",
    "technique",
    "techniques",
    "approach",
    "approaches",
}


def _build_cache_key(topic_count: int, domain: str = "", topic: str = "", level: int | None = None) -> str:
    normalized_domain = canonical_topic_key(domain) or "all-domains"
    normalized_topic = canonical_topic_key(topic) or "all-topics"
    normalized_level = level or 0
    return f"knowledge-gaps:v3:{max(1, topic_count)}:{normalized_level}:{normalized_domain}:{normalized_topic}"


def _load_cached_payload(db: Session, user_id: int, cache_key: str, ttl_hours: int = CACHE_TTL_HOURS) -> list[dict] | None:
    entry = db.scalar(
        select(KnowledgeGapCache).where(
            KnowledgeGapCache.user_id == user_id,
            KnowledgeGapCache.cache_key == cache_key,
        )
    )
    if entry is None or not (entry.payload_blob or "").strip():
        return None

    updated_at = entry.updated_at
    if updated_at is not None:
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        if updated_at < datetime.now(timezone.utc) - timedelta(hours=ttl_hours):
            return None

    try:
        return json.loads(entry.payload_blob)
    except json.JSONDecodeError:
        return None


def _save_cached_payload(db: Session, user_id: int, cache_key: str, payload: list[dict]) -> None:
    serialized = json.dumps(payload)
    entry = db.scalar(
        select(KnowledgeGapCache).where(
            KnowledgeGapCache.user_id == user_id,
            KnowledgeGapCache.cache_key == cache_key,
        )
    )
    if entry is None:
        entry = KnowledgeGapCache(user_id=user_id, cache_key=cache_key, payload_blob=serialized)
        db.add(entry)
    else:
        entry.payload_blob = serialized
    db.commit()


def _existing_topic_keys(db: Session, user_id: int) -> tuple[set[str], int]:
    topics = db.scalars(select(Topic).where(Topic.user_id == user_id)).all()
    topic_keys = {canonical_topic_key(topic.name) for topic in topics if canonical_topic_key(topic.name)}
    return topic_keys, len(topics)


def _build_related_topic_map(db: Session, user_id: int) -> dict[str, set[str]]:
    items = db.scalars(
        select(KnowledgeItem)
        .options(selectinload(KnowledgeItem.content_topics).selectinload(ContentTopic.topic))
        .where(KnowledgeItem.user_id == user_id)
        .order_by(desc(KnowledgeItem.updated_at))
    ).all()

    related_map: dict[str, set[str]] = {}
    for item in items:
        names = sorted(
            {
                content_topic.topic.name
                for content_topic in item.content_topics
                if content_topic.topic is not None and content_topic.topic.name
            }
        )
        for name in names:
            related_map.setdefault(name, set()).update({sibling for sibling in names if sibling != name})
    return related_map


def _normalize_ai_topic(value: str) -> str:
    cleaned = normalize_topic_label(value) or value.strip()
    cleaned = " ".join(cleaned.split()).strip()
    if not cleaned:
        return ""
    if len(cleaned.split()) > 4:
        return ""
    if cleaned.lower() in GENERIC_AI_JUNK:
        return ""
    return cleaned


def _topic_reason(path_name: str, topics: list[dict], index: int) -> str:
    previous_topics = [topic["topic"] for topic in topics[:index] if topic["state"] == "covered"]
    if not previous_topics:
        return f"{topics[index]['topic']} is the first missing step in {path_name}."
    if len(previous_topics) == 1:
        return f"You already covered {previous_topics[0]}, so {topics[index]['topic']} is the next gap in {path_name}."
    recent = previous_topics[-2:]
    return f"You already covered {' and '.join(recent)}, so {topics[index]['topic']} is the next gap in {path_name}."


def _rule_gap_topics(path: dict, related_map: dict[str, set[str]]) -> tuple[list[dict], float]:
    topics = path.get("topics", [])
    gap_topics: list[dict] = []
    confidences: list[float] = []
    for index, topic in enumerate(topics):
        if topic.get("state") == "covered":
            continue

        previous_topic = topics[index - 1]["topic"] if index > 0 else None
        next_topic = topics[index + 1]["topic"] if index + 1 < len(topics) else None
        neighbor_support = 0.0
        if previous_topic and previous_topic in related_map:
            neighbor_support += 0.08
        if next_topic and next_topic in related_map:
            neighbor_support += 0.04
        if topic.get("state") == "started":
            neighbor_support += 0.06

        confidence = min(0.96, 0.66 + neighbor_support + max(0, 0.12 - index * 0.01))
        confidences.append(round(confidence, 2))
        gap_topics.append(
            {
                "topic": topic["topic"],
                "state": topic.get("state", "missing"),
                "action": topic.get("action", "add"),
                "reason": _topic_reason(path["path_name"], topics, index),
                "confidence": round(confidence, 2),
                "source": "rules",
            }
        )

    return gap_topics[:MAX_PATH_GAPS], round(max(confidences, default=0.0), 2)


def _ai_gap_topics(path: dict, existing_topic_keys: set[str], related_map: dict[str, set[str]]) -> tuple[list[dict], float]:
    completed_topics = path.get("completed_topics", [])
    upcoming_topics = path.get("upcoming_topics", [])
    related_topics = sorted({topic for topic in completed_topics for topic in related_map.get(topic, set())})[:8]
    path_topic_keys = {canonical_topic_key(topic["topic"]) for topic in path.get("topics", [])}

    prompt = (
        "You are helping analyze gaps in a personal learning path.\n"
        "Return only concise missing concept names.\n"
        "Do not explain.\n"
        "Do not return sentences.\n"
        "Return at most 3 topics, one per line.\n"
        "Prefer concepts that strengthen the named learning path.\n\n"
        f"Learning path: {path['path_name']}\n"
        f"Domain: {path['domain']}\n"
        f"Completed topics:\n" + "\n".join(f"- {topic}" for topic in completed_topics[:6] or ["- None"]) + "\n\n"
        f"Current missing topics:\n" + "\n".join(f"- {topic}" for topic in upcoming_topics[:6] or ["- None"]) + "\n\n"
        f"Related graph neighbors:\n" + "\n".join(f"- {topic}" for topic in related_topics or ["- None"]) + "\n"
    )

    ai_topics: list[dict] = []
    seen: set[str] = set()
    for raw in generate_list(prompt, timeout=20):
        candidate = _normalize_ai_topic(raw)
        candidate_key = canonical_topic_key(candidate)
        if not candidate or not candidate_key or candidate_key in seen:
            continue
        if candidate_key in existing_topic_keys or candidate_key in path_topic_keys:
            continue
        seen.add(candidate_key)
        ai_topics.append(
            {
                "topic": candidate,
                "state": "missing",
                "action": "add",
                "reason": f"AI identified {candidate} as a useful supporting concept for {path['path_name']}.",
                "confidence": 0.72,
                "source": "ai",
            }
        )
        if len(ai_topics) >= 3:
            break

    confidence = 0.72 if ai_topics else 0.0
    return ai_topics, confidence


def _path_payload(path: dict, missing_topics: list[dict], source: str, cached: bool, rule_confidence: float, ai_confidence: float) -> dict:
    return {
        "path_name": path["path_name"],
        "domain": path["domain"],
        "progress_percent": path["progress_percent"],
        "covered_count": path["covered_count"],
        "total_count": path["total_count"],
        "next_topic": path.get("next_topic"),
        "topics": path.get("topics", []),
        "source": source,
        "cached": cached,
        "rule_confidence": rule_confidence,
        "ai_confidence": ai_confidence,
        "missing_topics": missing_topics,
    }


def _path_matches_context(path: dict, domain: str = "", topic: str = "") -> bool:
    normalized_domain = canonical_topic_key(domain)
    normalized_topic = canonical_topic_key(topic)
    path_domain = canonical_topic_key(path.get("domain", ""))
    path_topics = {canonical_topic_key(item.get("topic", "")) for item in path.get("topics", [])}

    if normalized_topic and normalized_topic in path_topics:
        return True
    if normalized_domain and normalized_domain == path_domain:
        return True
    return not normalized_domain and not normalized_topic


def _path_context_score(path: dict, domain: str = "", topic: str = "") -> int:
    normalized_domain = canonical_topic_key(domain)
    normalized_topic = canonical_topic_key(topic)
    score = 0
    path_domain = canonical_topic_key(path.get("domain", ""))
    path_topics = {canonical_topic_key(item.get("topic", "")) for item in path.get("topics", [])}

    if normalized_topic and normalized_topic in path_topics:
        score += 6
    if normalized_domain and normalized_domain == path_domain:
        score += 3
    next_topic = path.get("next_topic") or {}
    if canonical_topic_key(next_topic.get("topic", "")) == normalized_topic:
        score += 2
    return score


def analyze_knowledge_gaps(
    db: Session,
    user_id: int,
    refresh: bool = False,
    domain: str = "",
    topic: str = "",
    level: int | None = None,
) -> list[dict]:
    existing_topic_keys, topic_count = _existing_topic_keys(db, user_id)
    cache_key = _build_cache_key(topic_count, domain=domain, topic=topic, level=level)

    if not refresh:
        cached = _load_cached_payload(db, user_id, cache_key)
        if cached is not None:
            return [
                {
                    **entry,
                    "cached": True,
                }
                for entry in cached
            ]

    learning_paths = build_learning_paths(db, user_id)
    related_map = _build_related_topic_map(db, user_id)
    payload: list[dict] = []

    for path in learning_paths:
        rule_missing_topics, rule_confidence = _rule_gap_topics(path, related_map)
        missing_topics = rule_missing_topics[:]
        ai_confidence = 0.0
        source = "rules"

        should_use_ai = len(rule_missing_topics) < RULE_MIN_SUGGESTIONS or rule_confidence < RULE_CONFIDENCE_THRESHOLD
        if should_use_ai:
            try:
                ai_missing_topics, ai_confidence = _ai_gap_topics(path, existing_topic_keys, related_map)
                if ai_missing_topics:
                    source = "hybrid" if missing_topics else "ai"
                    merged = missing_topics[:]
                    seen = {canonical_topic_key(item["topic"]) for item in merged}
                    for item in ai_missing_topics:
                        item_key = canonical_topic_key(item["topic"])
                        if not item_key or item_key in seen:
                            continue
                        seen.add(item_key)
                        merged.append(item)
                    missing_topics = merged[:MAX_PATH_GAPS]
            except Exception as exc:  # noqa: BLE001
                logger.warning("Knowledge gap analyzer AI fallback for %s: %s", path["path_name"], exc)
                source = "rules"
                ai_confidence = 0.0

        if not missing_topics:
            continue

        payload.append(_path_payload(path, missing_topics, source, False, rule_confidence, ai_confidence))

    if topic or domain:
        matching_payload = [
            entry for entry in payload
            if _path_matches_context(entry, domain=domain, topic=topic)
        ]
        if matching_payload:
            payload = sorted(
                matching_payload,
                key=lambda entry: (
                    -_path_context_score(entry, domain=domain, topic=topic),
                    entry["progress_percent"],
                    entry["path_name"],
                )
            )

    for entry in payload:
        entry.pop("topics", None)

    _save_cached_payload(db, user_id, cache_key, payload)
    return payload
