from __future__ import annotations

import json
import logging
from collections import Counter

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.content_topic import ContentTopic
from app.models.knowledge import KnowledgeItem
from app.models.topic import Topic
from app.services.ai_insight_store import build_context_hash, get_ai_insight, save_ai_insight
from app.services.graph_service import _topic_group
from app.services.graph_state_service import get_user_graph_version
from app.services.learning_path_service import build_learning_paths
from app.services.ollama_service import generate_text
from app.services.topic_normalizer_service import canonical_topic_key


logger = logging.getLogger(__name__)
FEATURE_TYPE = "topic_summary"
SUMMARY_PROMPT_VERSION = "v3"
GENERIC_SUMMARY_PHRASES = {
    "for ai",
    "important topic",
    "useful concept",
    "improves search efficiency",
    "helps with learning",
    "supports the graph",
}


def _linked_items(db: Session, user_id: int, topic_id: int) -> list[KnowledgeItem]:
    return db.scalars(
        select(KnowledgeItem)
        .join(ContentTopic, ContentTopic.knowledge_id == KnowledgeItem.id)
        .where(ContentTopic.topic_id == topic_id, KnowledgeItem.user_id == user_id)
        .order_by(desc(KnowledgeItem.updated_at))
    ).all()


def _related_topics(db: Session, user_id: int, topic_id: int, items: list[KnowledgeItem]) -> list[str]:
    related_counter: Counter[str] = Counter()
    for item in items:
        sibling_topics = db.scalars(
            select(Topic.name)
            .join(ContentTopic, ContentTopic.topic_id == Topic.id)
            .where(ContentTopic.knowledge_id == item.id, Topic.user_id == user_id, Topic.id != topic_id)
        ).all()
        for sibling_topic in sibling_topics:
            if sibling_topic:
                related_counter[sibling_topic] += 1
    return [name for name, _ in related_counter.most_common(6)]


def _path_membership(db: Session, user_id: int, topic_name: str) -> tuple[list[str], list[str]]:
    memberships: list[str] = []
    skills_unlocked: list[str] = []
    topic_key = canonical_topic_key(topic_name)
    for path in build_learning_paths(db, user_id):
        path_topics = path.get("topics", [])
        topic_names = [item.get("topic", "") for item in path_topics]
        normalized_names = [canonical_topic_key(name) for name in topic_names]
        if topic_key not in normalized_names:
            continue
        memberships.append(path["path_name"])
        index = normalized_names.index(topic_key)
        for unlocked in topic_names[index + 1:index + 3]:
            if unlocked and unlocked not in skills_unlocked:
                skills_unlocked.append(unlocked)
    return memberships, skills_unlocked


def _context_hash(topic: Topic, items: list[KnowledgeItem], related_topics: list[str], memberships: list[str], skills_unlocked: list[str]) -> str:
    return build_context_hash(
        {
            "version": SUMMARY_PROMPT_VERSION,
            "topic": topic.name,
            "domain": _topic_group(topic.name),
            "item_titles": [item.title for item in items[:6]],
            "item_times": [item.updated_at.isoformat() for item in items[:6] if item.updated_at],
            "related_topics": related_topics[:6],
            "memberships": memberships,
            "skills_unlocked": skills_unlocked[:4],
        }
    )


def _fallback_summary(topic: Topic, related_topics: list[str], memberships: list[str], skills_unlocked: list[str]) -> tuple[str, str, list[str], str]:
    domain = _topic_group(topic.name)
    if related_topics:
        related_preview = ", ".join(related_topics[:3])
        summary = f"{topic.name} is connected to {related_preview} in your {domain} knowledge graph."
    else:
        summary = f"{topic.name} is a {domain} topic in your knowledge graph."

    why_parts: list[str] = []
    if memberships:
        why_parts.append(f"It belongs to the {memberships[0]} learning path.")
    if related_topics:
        why_parts.append(f"It connects concepts like {', '.join(related_topics[:3])}.")
    if not why_parts:
        why_parts.append("It helps organize related knowledge in your graph.")

    return summary, " ".join(why_parts), skills_unlocked[:3], "rules"


def _parse_ai_summary(raw_text: str) -> dict | None:
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    summary = str(data.get("summary", "")).strip()
    why = str(data.get("why_it_matters", "")).strip()
    skills = data.get("skills_unlocked", [])
    if not summary or not why or not isinstance(skills, list):
        return None
    return {
        "summary": summary,
        "why_it_matters": why,
        "skills_unlocked": [str(skill).strip() for skill in skills if str(skill).strip()][:4],
    }


def _is_low_quality_summary(topic: Topic, payload: dict, related_topics: list[str], memberships: list[str]) -> bool:
    summary = payload.get("summary", "").strip()
    why = payload.get("why_it_matters", "").strip()
    combined = f"{summary} {why}".lower()
    if len(summary.split()) < 5 or len(why.split()) < 5:
        return True
    if any(phrase in combined for phrase in GENERIC_SUMMARY_PHRASES):
        return True
    if canonical_topic_key(summary) == canonical_topic_key(topic.name):
        return True
    has_related_reference = any(name.lower() in combined for name in related_topics[:3])
    has_path_reference = any(name.lower() in combined for name in memberships[:2])
    return not (has_related_reference or has_path_reference)


def _generate_ai_summary(topic: Topic, items: list[KnowledgeItem], related_topics: list[str], memberships: list[str], skills_unlocked: list[str]) -> dict | None:
    note_titles = [item.title for item in items[:5] if item.title]
    domain = _topic_group(topic.name)
    prompt = (
        "Return valid JSON only with keys summary, why_it_matters, skills_unlocked.\n"
        "Do not include markdown or code fences.\n"
        "summary must be 1 to 2 sentences that explain what the topic means in practical terms.\n"
        "why_it_matters must be 1 to 2 sentences that explain why this topic matters in the user's graph, what it connects to, and which learning path it belongs to if applicable.\n"
        "skills_unlocked must be an array of concise topic names.\n"
        "Be specific. Mention real related topics from the provided context.\n"
        "Avoid vague phrases like 'important topic', 'for AI', or 'improves efficiency'.\n"
        "If a learning path is present, reference it naturally.\n\n"
        f"Topic: {topic.name}\n"
        f"Domain: {domain}\n"
        f"Linked notes:\n" + "\n".join(f"- {title}" for title in note_titles or ["- None"]) + "\n\n"
        f"Related topics:\n" + "\n".join(f"- {name}" for name in related_topics or ["- None"]) + "\n\n"
        f"Learning paths:\n" + "\n".join(f"- {name}" for name in memberships or ["- None"]) + "\n\n"
        f"Likely skills unlocked:\n" + "\n".join(f"- {name}" for name in skills_unlocked or ["- None"]) + "\n\n"
        "Example style:\n"
        '{"summary":"Hybrid Search combines keyword and semantic retrieval to improve recall and precision across search results.","why_it_matters":"It connects Semantic Search, Keyword Search, and Vector Databases in your graph, and it supports the AI Retrieval Engineer path.","skills_unlocked":["Retrieval Augmented Generation","Retrieval Optimization"]}'
    )
    parsed = _parse_ai_summary(generate_text(prompt, timeout=25))
    if not parsed:
        return None
    if _is_low_quality_summary(topic, parsed, related_topics, memberships):
        return None
    return parsed


def get_topic_summary(db: Session, user_id: int, topic_id: int, refresh: bool = False) -> dict:
    topic = db.scalar(select(Topic).where(Topic.id == topic_id, Topic.user_id == user_id))
    if topic is None:
        raise ValueError("Topic not found")

    items = _linked_items(db, user_id, topic.id)
    related_topics = _related_topics(db, user_id, topic.id, items)
    memberships, skills_unlocked = _path_membership(db, user_id, topic.name)
    graph_version = get_user_graph_version(db, user_id)
    context_hash = _context_hash(topic, items, related_topics, memberships, skills_unlocked)

    if not refresh:
        cached = get_ai_insight(db, user_id, topic.name, FEATURE_TYPE, context_hash, graph_version)
        if cached:
            return cached

    summary_text, why_it_matters, final_skills, source = _fallback_summary(topic, related_topics, memberships, skills_unlocked)
    should_use_ai = bool(items or related_topics or memberships)
    if should_use_ai:
        try:
            ai_payload = _generate_ai_summary(topic, items, related_topics, memberships, skills_unlocked)
            if ai_payload:
                summary_text = ai_payload["summary"]
                why_it_matters = ai_payload["why_it_matters"]
                final_skills = ai_payload["skills_unlocked"] or final_skills
                source = "ai"
        except Exception as exc:  # noqa: BLE001
            logger.warning("Topic summary AI fallback for %s: %s", topic.name, exc)
            source = "fallback" if source != "ai" else source

    payload = {
        "topic": topic.name,
        "summary": summary_text,
        "why_it_matters": why_it_matters,
        "skills_unlocked": final_skills,
    }
    return save_ai_insight(
        db,
        user_id=user_id,
        topic_name=topic.name,
        feature_type=FEATURE_TYPE,
        context_hash=context_hash,
        graph_version=graph_version,
        source=source,
        payload=payload,
        ttl_hours=168,
    )
