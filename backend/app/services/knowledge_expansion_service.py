from __future__ import annotations

import logging
import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.content_topic import ContentTopic
from app.models.topic import Topic
from app.models.topic_expansion_cache import TopicExpansionCache
from app.models.topic_relationship import TopicRelationship
from app.services.graph_service import _topic_group
from app.services.learning_path_service import LEARNING_PATHS
from app.services.ollama_service import generate_topic_expansion
from app.services.topic_normalizer_service import normalize_topic_label


logger = logging.getLogger(__name__)

FALLBACK_TOPIC_RELATIONSHIPS = {
    "Hybrid Search": [
        "BM25",
        "ANN Index",
        "Reranking",
        "Cross Encoder",
        "Query Expansion",
    ],
    "Semantic Search": [
        "Embeddings",
        "Vector Databases",
        "Approximate Nearest Neighbor",
        "Similarity Search",
        "Cross Encoder",
    ],
    "Vector Databases": [
        "ANN Index",
        "HNSW",
        "IVF",
        "Vector Compression",
    ],
    "Embeddings": [
        "Similarity Search",
        "Cross Encoder",
        "Query Expansion",
    ],
    "Controlled Environment Agriculture": [
        "Climate Control",
        "Farm Automation",
        "Sensor Monitoring",
        "Yield Optimization",
    ],
    "Knowledge Management": [
        "Action Planning",
        "Personal Knowledge Systems",
        "Knowledge Retrieval",
        "Note Linking",
    ],
}

GENERIC_JUNK = {
    "concept",
    "concepts",
    "topic",
    "topics",
    "method",
    "methods",
    "system",
    "systems",
    "technique",
    "techniques",
    "modern approach",
    "modern approaches",
}

DISPLAY_WORDS = {
    "ai": "AI",
    "ann": "ANN",
    "api": "API",
    "bm25": "BM25",
    "hnsw": "HNSW",
    "ivf": "IVF",
    "llm": "LLM",
    "rag": "RAG",
}


def _clean_topic_name(value: str) -> str:
    normalized = re.sub(r'[^a-zA-Z0-9\s/-]+', ' ', (value or '').strip())
    normalized = re.sub(r'\s+', ' ', normalized).strip(' -_/')
    if not normalized:
        return ''

    words = normalized.split()
    if len(words) > 4:
        return ''

    lowered = normalized.lower()
    if lowered in GENERIC_JUNK:
        return ''

    formatted_words: list[str] = []
    for word in words:
        lower_word = word.lower()
        if lower_word in DISPLAY_WORDS:
            formatted_words.append(DISPLAY_WORDS[lower_word])
        elif word.isupper() and len(word) <= 5:
            formatted_words.append(word)
        else:
            formatted_words.append(word.title())

    candidate = ' '.join(formatted_words).strip()
    if not candidate or candidate.lower() in GENERIC_JUNK:
        return ''
    return candidate


def _canonical_key(value: str) -> str:
    normalized = normalize_topic_label(value) or _clean_topic_name(value)
    return re.sub(r'\s+', ' ', (normalized or '').strip().lower())


def _resolve_topic_name(existing_topics: list[Topic], topic_name: str) -> str:
    lowered = (topic_name or '').strip().lower()
    for topic in existing_topics:
        if (topic.name or '').strip().lower() == lowered:
            return topic.name
    return _clean_topic_name(topic_name) or topic_name.strip()


def _topic_path_name(topic_name: str) -> str | None:
    key = _canonical_key(topic_name)
    for path in LEARNING_PATHS:
        for path_topic in path['topics']:
            if _canonical_key(path_topic) == key:
                return path['path_name']
    return None


def _build_context_topics(db: Session, user_id: int, focused_topic: Topic | None, topic_name: str) -> list[str]:
    neighbor_scores: dict[str, float] = {}
    lowered = topic_name.lower()

    relationships = db.scalars(
        select(TopicRelationship).where(
            TopicRelationship.user_id == user_id,
            (func.lower(TopicRelationship.source_topic) == lowered)
            | (func.lower(TopicRelationship.target_topic) == lowered),
        )
    ).all()

    for relationship in relationships:
        other = relationship.target_topic if relationship.source_topic.lower() == lowered else relationship.source_topic
        if other and other.lower() != lowered:
            neighbor_scores[other] = neighbor_scores.get(other, 0.0) + max(1.0, relationship.confidence) * 3

    if focused_topic is not None:
        knowledge_ids = db.scalars(
            select(ContentTopic.knowledge_id).where(ContentTopic.topic_id == focused_topic.id)
        ).all()
        if knowledge_ids:
            sibling_rows = db.execute(
                select(Topic.name, func.count(ContentTopic.knowledge_id))
                .join(ContentTopic, ContentTopic.topic_id == Topic.id)
                .where(
                    Topic.user_id == user_id,
                    ContentTopic.knowledge_id.in_(knowledge_ids),
                    Topic.id != focused_topic.id,
                )
                .group_by(Topic.name)
                .order_by(func.count(ContentTopic.knowledge_id).desc(), Topic.name.asc())
            ).all()
            for sibling_name, count in sibling_rows:
                if sibling_name and sibling_name.lower() != lowered:
                    neighbor_scores[sibling_name] = neighbor_scores.get(sibling_name, 0.0) + float(count) * 2

    ordered_neighbors = [
        name for name, _ in sorted(neighbor_scores.items(), key=lambda item: (-item[1], item[0]))
    ]
    return ordered_neighbors[:7]


def _fallback_suggestions(topic_name: str) -> list[str]:
    cleaned_topic = _clean_topic_name(topic_name)
    if cleaned_topic in FALLBACK_TOPIC_RELATIONSHIPS:
        return FALLBACK_TOPIC_RELATIONSHIPS[cleaned_topic]
    lowered = cleaned_topic.lower()
    for key, values in FALLBACK_TOPIC_RELATIONSHIPS.items():
        if key.lower() == lowered:
            return values
    return []


def _build_prompt(topic_name: str, context_topics: list[str], known_domain: str, known_path: str | None) -> str:
    related_block = '\n'.join(f'- {topic}' for topic in context_topics) or '- None yet'
    path_line = known_path or 'No named path found'
    return (
        'You are helping expand a personal knowledge graph.\n'
        'Return only important missing concept names.\n'
        'Be concise.\n'
        'Do not explain.\n'
        'Do not return sentences.\n'
        'Return 3 to 7 concept names, one per line.\n\n'
        f'Focused topic: {topic_name}\n\n'
        f'Known related topics:\n{related_block}\n\n'
        f'Known domain: {known_domain}\n'
        f'Known learning path: {known_path or "No named path found"}\n\n'
        'Suggest important missing concepts that logically belong around this topic but are not already listed.\n'
        'Prefer concise concept names like BM25, Reranking, Cross Encoder, ANN Index, Query Expansion.\n'
        'Answer with only concept names, one per line.\n'
    )


def _dedupe_clean_suggestions(raw_suggestions: list[str], topic_name: str, limit: int = 8) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    topic_key = _canonical_key(topic_name)

    for raw in raw_suggestions:
        candidate = _clean_topic_name(raw)
        if not candidate:
            continue
        normalized = normalize_topic_label(candidate) or candidate
        normalized = _clean_topic_name(normalized)
        if not normalized:
            continue
        candidate_key = _canonical_key(normalized)
        if not candidate_key or candidate_key == topic_key or candidate_key in seen:
            continue
        if any(junk in candidate_key for junk in GENERIC_JUNK):
            continue
        seen.add(candidate_key)
        cleaned.append(normalized)
        if len(cleaned) >= limit:
            break

    return cleaned


def _filter_suggestions(
    raw_suggestions: list[str],
    *,
    topic_name: str,
    existing_topic_keys: set[str],
    context_topic_keys: set[str],
    limit: int,
) -> list[str]:
    filtered: list[str] = []
    seen: set[str] = set()
    for normalized in _dedupe_clean_suggestions(raw_suggestions, topic_name, limit=max(limit * 2, 8)):
        candidate_key = _canonical_key(normalized)
        if not candidate_key or candidate_key in seen:
            continue
        if candidate_key in existing_topic_keys:
            continue
        if candidate_key in context_topic_keys:
            continue
        seen.add(candidate_key)
        filtered.append(normalized)
        if len(filtered) >= limit:
            break
    return filtered


def _load_cached_ai_suggestions(db: Session, topic_key: str) -> list[str]:
    cached = db.scalar(select(TopicExpansionCache).where(TopicExpansionCache.topic_key == topic_key))
    if cached is None or not (cached.suggestions_blob or '').strip():
        return []
    return [line.strip() for line in cached.suggestions_blob.splitlines() if line.strip()]


def _save_cached_ai_suggestions(db: Session, topic_key: str, topic_name: str, suggestions: list[str]) -> None:
    if not suggestions:
        return
    blob = '\n'.join(suggestions)
    cached = db.scalar(select(TopicExpansionCache).where(TopicExpansionCache.topic_key == topic_key))
    if cached is None:
        cached = TopicExpansionCache(topic_key=topic_key, topic_name=topic_name, suggestions_blob=blob)
        db.add(cached)
    else:
        cached.topic_name = topic_name
        cached.suggestions_blob = blob
    db.commit()


def suggest_missing_topics(db: Session, user_id: int, topic_name: str, limit: int = 5, refresh: bool = False) -> dict[str, object]:
    normalized_topic = (topic_name or '').strip()
    if not normalized_topic:
        return {
            'topic': topic_name,
            'source': 'fallback',
            'context_topics': [],
            'suggestions': [],
        }

    existing_topics = db.scalars(select(Topic).where(Topic.user_id == user_id)).all()
    resolved_topic_name = _resolve_topic_name(existing_topics, normalized_topic)
    focused_topic = next(
        (topic for topic in existing_topics if topic.name.strip().lower() == resolved_topic_name.strip().lower()),
        None,
    )
    context_topics = _build_context_topics(db, user_id, focused_topic, resolved_topic_name)
    context_topic_keys = {_canonical_key(name) for name in context_topics if _canonical_key(name)}
    existing_topic_keys = {_canonical_key(topic.name) for topic in existing_topics if _canonical_key(topic.name)}

    domain = _topic_group(resolved_topic_name)
    path_name = _topic_path_name(resolved_topic_name)
    prompt = _build_prompt(resolved_topic_name, context_topics, domain, path_name)
    topic_key = _canonical_key(resolved_topic_name)

    source = 'ai'
    base_suggestions = [] if refresh else _load_cached_ai_suggestions(db, topic_key)
    if base_suggestions:
        source = 'cache'
    else:
        try:
            raw_ai_suggestions = generate_topic_expansion(prompt)
            base_suggestions = _dedupe_clean_suggestions(raw_ai_suggestions, resolved_topic_name, limit=8)
            if base_suggestions:
                _save_cached_ai_suggestions(db, topic_key, resolved_topic_name, base_suggestions)
            else:
                source = 'fallback'
        except Exception as exc:
            logger.warning('Knowledge expansion AI fallback for %s: %s', resolved_topic_name, exc)
            source = 'fallback'

    suggestions = _filter_suggestions(
        base_suggestions,
        topic_name=resolved_topic_name,
        existing_topic_keys=existing_topic_keys,
        context_topic_keys=context_topic_keys,
        limit=limit,
    )

    if not suggestions:
        fallback_suggestions = _fallback_suggestions(resolved_topic_name)
        suggestions = _filter_suggestions(
            fallback_suggestions,
            topic_name=resolved_topic_name,
            existing_topic_keys=existing_topic_keys,
            context_topic_keys=context_topic_keys,
            limit=limit,
        )
        source = 'fallback'
        logger.info('Knowledge expansion fallback used for %s', resolved_topic_name)

    return {
        'topic': resolved_topic_name,
        'source': source,
        'context_topics': context_topics[:7],
        'suggestions': suggestions[:limit],
    }

