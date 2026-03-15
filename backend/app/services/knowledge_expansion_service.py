from __future__ import annotations

import logging
import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.content_topic import ContentTopic
from app.models.topic import Topic
from app.models.topic_relationship import TopicRelationship
from app.services.cache_service import build_suggestion_cache_key, load_cached_payload, save_cached_payload
from app.services.graph_service import _topic_group
from app.services.learning_path_service import LEARNING_PATHS
from app.services.ollama_service import generate_topic_expansion
from app.services.topic_normalizer_service import canonical_topic_key, normalize_topic_label


logger = logging.getLogger(__name__)
RULE_CONFIDENCE_THRESHOLD = 0.80
RULE_MIN_SUGGESTIONS = 3
CACHE_TTL_HOURS = 24
MAX_SUGGESTIONS = 5

FALLBACK_TOPIC_RELATIONSHIPS = {
    "Hybrid Search": ["BM25", "ANN Index", "Reranking", "Cross Encoder", "Query Expansion"],
    "Semantic Search": ["Embeddings", "Vector Databases", "Approximate Nearest Neighbor", "Similarity Search", "Cross Encoder"],
    "Vector Databases": ["ANN Index", "HNSW", "IVF", "Vector Compression"],
    "Embeddings": ["Similarity Search", "Cross Encoder", "Query Expansion"],
    "Controlled Environment Agriculture": ["Climate Control", "Farm Automation", "Sensor Monitoring", "Yield Optimization"],
    "Knowledge Management": ["Action Planning", "Personal Knowledge Systems", "Knowledge Graph", "Note Linking"],
}

GENERIC_JUNK = {
    "concept", "concepts", "topic", "topics", "method", "methods", "system", "systems",
    "technique", "techniques", "modern approach", "modern approaches",
}

NOISE_TOKENS = {
    "add",
    "button",
    "click",
    "focu",
    "focus",
    "save",
    "saved",
    "test",
    "testing",
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

    lower_words = [word.lower() for word in words]
    if any(word in NOISE_TOKENS for word in lower_words):
        return ''
    if sum(1 for word in lower_words if word in NOISE_TOKENS) >= 1:
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

    candidate_key = canonical_topic_key(candidate)
    if any(token in candidate_key.split() for token in NOISE_TOKENS):
        return ''
    return candidate


def _resolve_topic_name(existing_topics: list[Topic], topic_name: str) -> str:
    lowered = (topic_name or '').strip().lower()
    for topic in existing_topics:
        if (topic.name or '').strip().lower() == lowered:
            return topic.name
    return _clean_topic_name(topic_name) or topic_name.strip()


def _topic_path(topic_name: str) -> dict[str, object] | None:
    key = canonical_topic_key(topic_name)
    for path in LEARNING_PATHS:
        if any(canonical_topic_key(path_topic) == key for path_topic in path['topics']):
            return path
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
        knowledge_ids = db.scalars(select(ContentTopic.knowledge_id).where(ContentTopic.topic_id == focused_topic.id)).all()
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

    ordered = []
    for name, _ in sorted(neighbor_scores.items(), key=lambda item: (-item[1], item[0])):
        cleaned = _clean_topic_name(name)
        if not cleaned:
            continue
        if canonical_topic_key(cleaned) == canonical_topic_key(topic_name):
            continue
        ordered.append(cleaned)

    deduped = []
    seen = set()
    for name in ordered:
        key = canonical_topic_key(name)
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(name)
    return deduped[:7]


def _rule_based_stack_suggestions(topic_name: str, context_topics: list[str]) -> list[str]:
    path = _topic_path(topic_name)
    if not path:
        return []

    path_topics = path['topics']
    try:
        current_index = next(index for index, name in enumerate(path_topics) if canonical_topic_key(name) == canonical_topic_key(topic_name))
    except StopIteration:
        return []

    known_keys = {canonical_topic_key(topic_name), *(canonical_topic_key(name) for name in context_topics)}
    suggestions: list[str] = []
    for candidate in path_topics[current_index + 1:]:
        if canonical_topic_key(candidate) in known_keys:
            continue
        suggestions.append(candidate)
        if len(suggestions) >= 3:
            break
    return suggestions


def _rule_based_neighbor_suggestions(topic_name: str, context_topics: list[str]) -> list[str]:
    cleaned = _clean_topic_name(topic_name)
    candidates = FALLBACK_TOPIC_RELATIONSHIPS.get(cleaned, [])
    context_keys = {canonical_topic_key(name) for name in context_topics}
    topic_key = canonical_topic_key(topic_name)
    results: list[str] = []
    for candidate in candidates:
        key = canonical_topic_key(candidate)
        if not key or key == topic_key or key in context_keys:
            continue
        results.append(candidate)
    return results


def get_rule_based_suggestions(topic_name: str, context: dict) -> dict:
    context_topics = context.get('context_topics') or []
    path_suggestions = _rule_based_stack_suggestions(topic_name, context_topics)
    neighbor_suggestions = _rule_based_neighbor_suggestions(topic_name, context_topics)

    merged: list[str] = []
    seen: set[str] = set()
    for suggestion in [*path_suggestions, *neighbor_suggestions]:
        key = canonical_topic_key(suggestion)
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(suggestion)
        if len(merged) >= MAX_SUGGESTIONS:
            break

    confidence = min(0.95, 0.56 + len(path_suggestions) * 0.12 + len(neighbor_suggestions) * 0.08)
    if path_suggestions and len(path_suggestions) >= 2:
        confidence += 0.08
    confidence = round(min(0.95, confidence), 2)

    return {
        'source': 'rules',
        'confidence': confidence,
        'suggestions': merged,
    }


def get_ai_suggestions(topic_name: str, context: dict) -> dict:
    context_topics = context.get('context_topics') or []
    known_domain = context.get('domain') or _topic_group(topic_name)
    known_path = context.get('learning_path') or 'No named path found'
    known_topics = context.get('known_topics') or []
    missing_topics = context.get('missing_topics') or []

    related_block = '\n'.join(f'- {topic}' for topic in context_topics) or '- None yet'
    known_block = '\n'.join(f'- {topic}' for topic in known_topics[:8]) or '- None yet'
    missing_block = '\n'.join(f'- {topic}' for topic in missing_topics[:6]) or '- None known'
    prompt = (
        'You are helping expand a personal knowledge graph.\n'
        'Return only concise concept names.\n'
        'Do not explain.\n'
        'Do not return sentences.\n'
        'Return at most 5 concepts, one per line.\n'
        'Do not return duplicates or concepts already known.\n\n'
        f'Focused topic: {topic_name}\n'
        f'Domain: {known_domain}\n'
        f'Learning path: {known_path}\n\n'
        f'Known neighboring topics:\n{related_block}\n\n'
        f'Already known topics:\n{known_block}\n\n'
        f'Missing topics if known:\n{missing_block}\n'
    )

    suggestions = generate_topic_expansion(prompt)
    cleaned = []
    seen: set[str] = set()
    topic_key = canonical_topic_key(topic_name)
    known_keys = {canonical_topic_key(name) for name in [*context_topics, *known_topics] if canonical_topic_key(name)}
    for raw in suggestions:
        candidate = _clean_topic_name(normalize_topic_label(raw) or raw)
        key = canonical_topic_key(candidate)
        if not candidate or not key or key == topic_key or key in seen or key in known_keys:
            continue
        seen.add(key)
        cleaned.append(candidate)
        if len(cleaned) >= MAX_SUGGESTIONS:
            break

    confidence = round(0.62 + min(0.18, len(cleaned) * 0.03), 2) if cleaned else 0.0
    return {
        'source': 'ai',
        'confidence': confidence,
        'suggestions': cleaned,
    }


def _filter_final_suggestions(topic_name: str, suggestions: list[str], existing_topic_keys: set[str], context_topic_keys: set[str], limit: int) -> list[str]:
    filtered: list[str] = []
    seen: set[str] = set()
    topic_key = canonical_topic_key(topic_name)
    for raw in suggestions:
        candidate = _clean_topic_name(normalize_topic_label(raw) or raw)
        key = canonical_topic_key(candidate)
        if not candidate or not key or key in seen or key == topic_key:
            continue
        if key in existing_topic_keys or key in context_topic_keys:
            continue
        seen.add(key)
        filtered.append(candidate)
        if len(filtered) >= limit:
            break
    return filtered


def suggest_missing_topics(db: Session, user_id: int, topic_name: str, limit: int = MAX_SUGGESTIONS, refresh: bool = False) -> dict[str, object]:
    normalized_topic = (topic_name or '').strip()
    if not normalized_topic:
        return {
            'topic': topic_name,
            'source': 'rules',
            'cached': False,
            'rule_confidence': 0.0,
            'ai_confidence': 0.0,
            'context_topics': [],
            'suggestions': [],
        }

    existing_topics = db.scalars(select(Topic).where(Topic.user_id == user_id)).all()
    resolved_topic_name = _resolve_topic_name(existing_topics, normalized_topic)
    focused_topic = next((topic for topic in existing_topics if topic.name.strip().lower() == resolved_topic_name.strip().lower()), None)
    context_topics = _build_context_topics(db, user_id, focused_topic, resolved_topic_name)
    known_topics = [topic.name for topic in existing_topics]
    existing_topic_keys = {canonical_topic_key(name) for name in known_topics if canonical_topic_key(name)}
    context_topic_keys = {canonical_topic_key(name) for name in context_topics if canonical_topic_key(name)}

    path = _topic_path(resolved_topic_name)
    missing_topics = []
    if path:
        path_topics = path['topics']
        missing_topics = [name for name in path_topics if canonical_topic_key(name) not in existing_topic_keys]
    domain = _topic_group(resolved_topic_name)
    graph_version = max(1, len(context_topics))
    cache_key = build_suggestion_cache_key(resolved_topic_name, graph_version)

    if not refresh:
        cached = load_cached_payload(db, cache_key, ttl_hours=CACHE_TTL_HOURS)
        if cached:
            cached_suggestions = _filter_final_suggestions(
                resolved_topic_name,
                cached.get('suggestions') or [],
                existing_topic_keys,
                context_topic_keys,
                limit,
            )
            cached['suggestions'] = cached_suggestions
            cached['cached'] = True
            cached['source'] = 'cache'
            cached['topic'] = resolved_topic_name
            cached['context_topics'] = context_topics[:7]
            return cached

    context = {
        'context_topics': context_topics,
        'domain': domain,
        'learning_path': path['path_name'] if path and 'path_name' in path else path['name'] if path else None,
        'known_topics': known_topics,
        'missing_topics': missing_topics,
    }

    rule_result = get_rule_based_suggestions(resolved_topic_name, context)
    rule_suggestions = _filter_final_suggestions(
        resolved_topic_name,
        rule_result['suggestions'],
        existing_topic_keys,
        context_topic_keys,
        limit,
    )

    ai_result = {'source': 'ai', 'confidence': 0.0, 'suggestions': []}
    final_source = 'rules'
    final_suggestions = rule_suggestions

    should_call_ai = refresh or len(rule_suggestions) < RULE_MIN_SUGGESTIONS or rule_result['confidence'] < RULE_CONFIDENCE_THRESHOLD
    if should_call_ai:
        try:
            ai_result = get_ai_suggestions(resolved_topic_name, context)
        except Exception as exc:
            logger.warning('Hybrid suggestion AI fallback for %s: %s', resolved_topic_name, exc)
            ai_result = {'source': 'ai', 'confidence': 0.0, 'suggestions': []}

        merged = _filter_final_suggestions(
            resolved_topic_name,
            [*rule_suggestions, *(ai_result.get('suggestions') or [])],
            existing_topic_keys,
            context_topic_keys,
            limit,
        )
        final_suggestions = merged
        if rule_suggestions and ai_result.get('suggestions'):
            final_source = 'hybrid'
        elif ai_result.get('suggestions'):
            final_source = 'ai'
        else:
            final_source = 'rules'

    payload = {
        'topic': resolved_topic_name,
        'source': final_source,
        'cached': False,
        'rule_confidence': round(rule_result['confidence'], 2),
        'ai_confidence': round(ai_result.get('confidence', 0.0), 2),
        'context_topics': context_topics[:7],
        'suggestions': final_suggestions[:limit],
    }
    save_cached_payload(db, cache_key, resolved_topic_name, payload)
    return payload

