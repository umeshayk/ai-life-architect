import re
from collections import Counter

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.models.content_topic import ContentTopic
from app.models.knowledge import KnowledgeItem
from app.models.knowledge_connection import KnowledgeConnection
from app.models.topic import Topic
from app.services.topic_extractor import extract_clean_topics, extract_clean_topic_scores, extract_topic_phrases, tokenize_topic_segment
from app.services.topic_normalizer_service import get_or_create_normalized_topic, merge_similar_topics, normalize_topic_label
from app.services.timeline_event_service import build_topic_path_events, log_knowledge_event


STOP_WORDS = {
    "a",
    "about",
    "after",
    "also",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "being",
    "but",
    "can",
    "for",
    "from",
    "help",
    "how",
    "improve",
    "in",
    "into",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "up",
    "use",
    "using",
    "was",
    "were",
    "with",
    "when",
    "why",
    "you",
    "your",
}

JUNK_TOPICS = {
    "architect",
    "augmented",
    "database",
    "generation",
    "including",
    "knowledge",
    "life",
    "located",
    "management",
    "method",
    "note",
    "notes",
    "personal",
    "search",
    "semantic",
    "system",
    "systems",
    "technology",
    "txt",
    "personal",
    "users",
    "pdf",
    "file",
    "files",
    "content",
    "title",
    "summary",
    "organize",
    "document",
    "documents",
    "link",
    "links",
    "item",
    "items",
}

ALIAS_MAP = {
    "ai": "AI / Technology",
    "a i": "AI / Technology",
    "artificial intelligence": "AI / Technology",
    "ai technology": "AI / Technology",
    "ai life architect": "AI Life Architect",
    "life architect": "AI Life Architect",
    "ai notes": "AI / Technology",
    "llm": "LLM Systems",
    "llm system": "LLM Systems",
    "llm systems": "LLM Systems",
    "semantic search": "Semantic Search",
    "retrieval augmented": "Retrieval Augmented Generation",
    "augmented generation": "Retrieval Augmented Generation",
    "retrieval augmented generation": "Retrieval Augmented Generation",
    "rag": "Retrieval Augmented Generation",
    "vector database": "Vector Databases",
    "vector databases": "Vector Databases",
    "vector search": "Vector Databases",
    "embedding": "Embeddings",
    "embeddings": "Embeddings",
    "keyword search": "Keyword Search",
    "knowledge mgmt": "Knowledge Management",
    "knowledge management": "Knowledge Management",
    "second brain": "Knowledge Management",
    "knowledge architect": "Knowledge Management",
    "mushroom": "Mushroom Farming",
    "oyster mushroom": "Mushroom Farming",
    "mushroom farming": "Mushroom Farming",
    "oyster mushroom farming": "Mushroom Farming",
    "farm business": "Farm Business",
    "hydroponic farming": "Hydroponic Farming",
    "hydroponics": "Hydroponic Farming",
    "controlled environment agriculture": "Controlled Environment Agriculture",
    "fastapi": "FastAPI",
    "react": "React",
    "building second brain": "Building Second Brain",
    "second brain method": "Building Second Brain",
    "brain method": "Building Second Brain",
    "knowledge organization": "Knowledge Organization",
    "organize knowledge": "Knowledge Organization",
    "personal productivity": "Personal Productivity",
    "travel spiritual": "Travel / Spiritual",
    "jyotirlinga": "Travel / Spiritual",
    "temple": "Travel / Spiritual",
    "vedic": "Vedic Mathematics",
    "vedic math": "Vedic Mathematics",
    "vedic mathematics": "Vedic Mathematics",
    "vedic multiplication": "Vedic Mathematics",
    "vedic square": "Vedic Mathematics",
    "nikhilam": "Vedic Mathematics",
    "urdhva": "Vedic Mathematics",
    "sutra": "Vedic Mathematics",
    "math": "Mathematics",
}

CANONICAL_MULTI_WORD_TOPICS = {
    "AI / Technology",
    "AI Life Architect",
    "Building Second Brain",
    "Controlled Environment Agriculture",
    "Embeddings",
    "Farm Business",
    "FastAPI",
    "Hydroponic Farming",
    "Keyword Search",
    "Knowledge Organization",
    "Knowledge Management",
    "LLM Systems",
    "Mushroom Farming",
    "Personal Productivity",
    "React",
    "Retrieval Augmented Generation",
    "Semantic Search",
    "Travel / Spiritual",
    "Vector Databases",
    "Vedic Mathematics",
}

DISCOVERY_PATTERNS = [
    ("Hybrid Search", ("hybrid", "search")),
    ("Keyword Search", ("keyword", "search")),
    ("Semantic Search", ("semantic", "search")),
    ("Retrieval Augmented Generation", ("retrieval", "augmented")),
    ("Retrieval Augmented Generation", ("augmented", "generation")),
    ("Retrieval Augmented Generation", ("rag",)),
    ("Knowledge Management", ("knowledge", "management")),
    ("Knowledge Management", ("second", "brain")),
    ("AI Life Architect", ("ai", "life", "architect")),
    ("Mushroom Farming", ("mushroom", "farming")),
    ("Mushroom Farming", ("oyster", "mushroom")),
    ("Hydroponic Farming", ("hydroponic",)),
    ("Hydroponic Farming", ("hydroponics",)),
    ("Controlled Environment Agriculture", ("controlled", "environment", "agriculture")),
    ("Vector Databases", ("vector", "database")),
    ("Vector Databases", ("vector", "databases")),
    ("Embeddings", ("embedding",)),
    ("Embeddings", ("embeddings",)),
    ("Vedic Mathematics", ("vedic",)),
    ("Vedic Mathematics", ("nikhilam",)),
    ("Vedic Mathematics", ("urdhva",)),
    ("Vedic Mathematics", ("sutra",)),
    ("Vedic Mathematics", ("vedic", "multiplication")),
    ("Vedic Mathematics", ("vedic", "square")),
]

RULE_FALLBACKS = {
    "Agriculture": {"mushroom", "farming", "hydroponic", "agriculture", "farm"},
    "AI / Technology": {"fastapi", "react", "embedding", "embeddings", "vector", "semantic", "rag", "ai", "llm"},
    "Mathematics": {"nikhilam", "vedic", "multiplication", "subtraction", "math"},
    "Travel / Spiritual": {"jyotirlinga", "temple", "kashi", "kedarnath", "somnath"},
    "Knowledge Management": {"productivity", "second", "brain", "knowledge", "workflow"},
}


def _normalize_words(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9\s]+", " ", value.lower())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def normalize_topic_name(value: str) -> str:
    normalized = _normalize_words(value)
    if not normalized:
        return ""
    normalized = " ".join(dict.fromkeys(normalized.split()))

    direct_label = _match_topic_patterns(normalized)
    if direct_label:
        return direct_label

    if normalized in ALIAS_MAP:
        return ALIAS_MAP[normalized]

    parts = []
    for token in normalized.split():
        if token.endswith("ies") and len(token) > 4:
            token = token[:-3] + "y"
        elif token.endswith("s") and len(token) > 4 and not token.endswith("ss"):
            token = token[:-1]
        parts.append(token)
    singular_normalized = " ".join(parts)

    direct_label = _match_topic_patterns(singular_normalized)
    if direct_label:
        return direct_label

    if singular_normalized in ALIAS_MAP:
        return ALIAS_MAP[singular_normalized]

    display_words = {
        "ai": "AI",
        "llm": "LLM",
        "rag": "RAG",
        "api": "API",
        "fastapi": "FastAPI",
    }
    final_label = " ".join(display_words.get(word, word.title()) for word in singular_normalized.split()).strip()
    return normalize_topic_label(final_label) or final_label


def _match_topic_patterns(normalized: str) -> str:
    token_set = set(normalized.split())
    for label, terms in DISCOVERY_PATTERNS:
        if all(term in token_set for term in terms):
            return label
    return ""


def _is_junk_topic(label: str) -> bool:
    normalized = _normalize_words(label)
    if not normalized:
        return True
    if label in CANONICAL_MULTI_WORD_TOPICS:
        return False
    if normalized in JUNK_TOPICS:
        return True
    tokens = normalized.split()
    if len(tokens) == 1 and tokens[0] in JUNK_TOPICS:
        return True
    if all(token in STOP_WORDS or token in JUNK_TOPICS for token in tokens):
        return True
    return False


def _allow_single_word_topic(phrase: str, label: str) -> bool:
    normalized_phrase = _normalize_words(phrase)
    normalized_label = _normalize_words(label)
    if " " in normalized_phrase:
        return True
    if label in CANONICAL_MULTI_WORD_TOPICS:
        return True
    if normalized_phrase in ALIAS_MAP and ALIAS_MAP[normalized_phrase] != label:
        return True
    allowed_singletons = {"Embeddings", "FastAPI", "Mathematics", "React", "Travel / Spiritual", "Vector Databases", "Vedic Mathematics"}
    return label in allowed_singletons and normalized_label not in JUNK_TOPICS


def _merge_ranked_topics(ranked: list[tuple[str, float]], local_scores: Counter[str]) -> list[tuple[str, float]]:
    deduped: list[tuple[str, float]] = []
    seen_tokens: set[str] = set()

    for label, confidence in ranked:
        if _is_junk_topic(label):
            continue

        normalized = _normalize_words(label)
        tokens = set(normalized.split())
        if tokens and tokens.issubset(seen_tokens):
            continue

        replaced = False
        for index, (existing_label, existing_confidence) in enumerate(deduped):
            existing_tokens = set(_normalize_words(existing_label).split())
            if not existing_tokens:
                continue
            if tokens.issuperset(existing_tokens) and local_scores[label] >= local_scores[existing_label] * 0.9:
                deduped[index] = (label, max(confidence, existing_confidence))
                seen_tokens.update(tokens)
                replaced = True
                break
            if existing_tokens.issuperset(tokens) and local_scores[existing_label] >= local_scores[label]:
                replaced = True
                break

        if replaced:
            continue

        deduped.append((label, confidence))
        seen_tokens.update(tokens)
        if len(deduped) >= 3:
            break

    return deduped[:3]


def _dedupe_normalized_assignments(assignments: list[tuple[str, float]]) -> list[tuple[str, float]]:
    deduped: dict[str, tuple[str, float]] = {}
    order: list[str] = []

    for label, confidence in assignments:
        normalized_label = normalize_topic_label(label) or label
        key = _normalize_words(normalized_label)
        if not key:
            continue
        existing = deduped.get(key)
        if existing is None:
            deduped[key] = (normalized_label, confidence)
            order.append(key)
            continue
        if confidence > existing[1]:
            deduped[key] = (normalized_label, confidence)

    return [deduped[key] for key in order[:3]]


def _is_canonical_topic(label: str) -> bool:
    return label in CANONICAL_MULTI_WORD_TOPICS or label in RULE_FALLBACKS


def _tokenize_segment(text: str) -> list[str]:
    return tokenize_topic_segment(text, STOP_WORDS, JUNK_TOPICS)


def _extract_candidate_scores(item: KnowledgeItem) -> Counter[str]:
    scores: Counter[str] = Counter()
    content_excerpt = (item.content or "")[:800]
    combined_text = " ".join([item.title or "", item.summary or "", item.tags or "", content_excerpt])
    sources = [
        (" ".join(tag.strip() for tag in (item.tags or "").split(",") if tag.strip()), 2.2),
        (item.title or "", 1.6),
        (item.summary or "", 1.0),
        (content_excerpt, 0.55),
    ]

    normalized_tokens = set(_normalize_words(combined_text).split())
    for label, terms in DISCOVERY_PATTERNS:
        if all(term in normalized_tokens for term in terms):
            scores[label] += 2.8 if len(terms) > 1 else 1.8

    clean_topics = extract_clean_topic_scores(combined_text, max_topics=5)
    for label, score in clean_topics.items():
        scores[normalize_topic_name(label) or label] += score * 2.1

    for text, weight in sources:
        if not text:
            continue
        clean_topics = extract_clean_topics(text, max_topics=4)
        for index, label in enumerate(clean_topics, start=1):
            normalized_label = normalize_topic_name(label) or label
            if not normalized_label or _is_junk_topic(normalized_label):
                continue
            scores[normalized_label] += weight * max(1.0, 3.4 - index * 0.5)

        segments = re.split(r"[.!?\n,:;()\-/]+", text)
        for segment in segments:
            tokens = _tokenize_segment(segment)
            if not tokens:
                continue
            for phrase, size in extract_topic_phrases(tokens, max_words=3):
                label = normalize_topic_name(phrase)
                if not label or _is_junk_topic(label):
                    continue
                scores[label] += weight * {3: 1.45, 2: 1.25}.get(size, 0.85)

            for phrase in tokens:
                label = normalize_topic_name(phrase)
                if not label or _is_junk_topic(label):
                    continue
                if not _allow_single_word_topic(phrase, label):
                    continue
                scores[label] += weight * 0.55
    return scores


def _fallback_topics(item: KnowledgeItem) -> list[tuple[str, float]]:
    keyword_text = " ".join([item.title or "", item.summary or "", item.content or "", item.tags or ""]).lower()
    candidates = []
    for topic_name, keywords in RULE_FALLBACKS.items():
        hits = sum(1 for keyword in keywords if keyword in keyword_text)
        if hits:
            candidates.append((topic_name, round(min(0.92, 0.42 + hits * 0.12), 2)))
    if candidates:
        return candidates[:3]
    return [("General Knowledge", 0.32)]


def _build_item_topic_assignments(
    items: list[KnowledgeItem],
    *,
    confidence_floor: float = 0.46,
) -> tuple[dict[int, list[tuple[str, float]]], dict[int, Counter[str]]]:
    assignments: dict[int, list[tuple[str, float]]] = {}
    item_candidates: dict[int, Counter[str]] = {}

    for item in items:
        local_scores = _extract_candidate_scores(item)
        item_candidates[item.id] = local_scores

        ranked: list[tuple[str, float]] = []
        for label, score in local_scores.items():
            if _is_junk_topic(label):
                continue

            normalized_label = _normalize_words(label)
            token_count = len(normalized_label.split())
            base_confidence = 0.26 + score * 0.11
            if token_count >= 2:
                base_confidence += 0.08
            if label in CANONICAL_MULTI_WORD_TOPICS:
                base_confidence += 0.04
            confidence = round(min(0.95, base_confidence), 2)

            if confidence >= confidence_floor:
                ranked.append((label, confidence))

        ranked.sort(key=lambda pair: (local_scores[pair[0]], pair[1], pair[0]), reverse=True)
        deduped = _merge_ranked_topics(ranked, local_scores)

        if not deduped and local_scores:
            label, score = local_scores.most_common(1)[0]
            fallback_confidence = round(min(0.88, 0.3 + score * 0.12), 2)
            if not _is_junk_topic(label) and fallback_confidence >= 0.42:
                deduped = [(label, fallback_confidence)]

        if not deduped:
            deduped = _fallback_topics(item)

        primary = deduped[:1]
        secondaries = [
            (label, confidence)
            for label, confidence in deduped[1:]
            if confidence >= max(primary[0][1] * 0.72, 0.58)
        ]
        assignments[item.id] = _dedupe_normalized_assignments((primary + secondaries)[:3])

    return assignments, item_candidates


def _stable_global_topic_counts(assignments: dict[int, list[tuple[str, float]]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    confidence_totals: Counter[str] = Counter()

    for topics in assignments.values():
        seen_labels: set[str] = set()
        for label, confidence in topics:
            if label in seen_labels:
                continue
            seen_labels.add(label)
            counts[label] += 1
            confidence_totals[label] += confidence

    stable = Counter(
        {
            label: count
            for label, count in counts.items()
            if count >= 2 or confidence_totals[label] >= 1.7 or _is_canonical_topic(label)
        }
    )
    if stable:
        return stable
    return counts


def discover_topic_assignments(items: list[KnowledgeItem]) -> dict[int, list[tuple[str, float]]]:
    assignments, _ = _build_item_topic_assignments(items)
    return assignments


def _get_or_create_topic(db: Session, user_id: int, name: str, source_method: str = "discovery") -> tuple[Topic, bool]:
    topic, created = get_or_create_normalized_topic(db, user_id, name)
    if topic is None:
        fallback_name = normalize_topic_label(name)
        if not fallback_name:
            fallback_name = name.strip()
        topic = db.scalar(select(Topic).where(Topic.user_id == user_id, Topic.name == fallback_name))
        if topic is not None:
            return topic, False
        topic = Topic(user_id=user_id, name=fallback_name)
        db.add(topic)
        db.flush()
        log_knowledge_event(db, user_id=user_id, event_type="topic_created", topic_id=topic.id, source=source_method, metadata={"topic_name": topic.name})
        build_topic_path_events(db, user_id=user_id, topic=topic, source=source_method)
        return topic, True
    if created:
        log_knowledge_event(db, user_id=user_id, event_type="topic_created", topic_id=topic.id, source=source_method, metadata={"topic_name": topic.name})
        build_topic_path_events(db, user_id=user_id, topic=topic, source=source_method)
    return topic, created


def _load_user_items(db: Session, user_id: int) -> list[KnowledgeItem]:
    return db.scalars(
        select(KnowledgeItem)
        .options(selectinload(KnowledgeItem.outgoing_connections).selectinload(KnowledgeConnection.target_item))
        .where(KnowledgeItem.user_id == user_id)
    ).all()


def assign_topics_for_item(db: Session, item: KnowledgeItem, source_method: str = "discovery") -> tuple[int, int]:
    assignments, _ = _build_item_topic_assignments([item])
    item_assignments = assignments.get(item.id, [])

    db.execute(delete(ContentTopic).where(ContentTopic.knowledge_id == item.id))
    db.flush()

    topics_created = 0
    links_created = 0
    seen_topic_ids: set[int] = set()
    for label, confidence in item_assignments:
        topic, created = _get_or_create_topic(db, item.user_id, label, source_method=source_method)
        if topic.id in seen_topic_ids:
            continue
        seen_topic_ids.add(topic.id)
        if created:
            topics_created += 1
        db.add(
            ContentTopic(
                user_id=item.user_id,
                knowledge_id=item.id,
                topic_id=topic.id,
                confidence_score=confidence,
            )
        )
        log_knowledge_event(db, user_id=item.user_id, event_type="topic_linked", topic_id=topic.id, source=source_method, metadata={"item_id": item.id, "item_title": item.title, "confidence": confidence})
        links_created += 1

    db.commit()
    return topics_created, links_created


def discover_topics_for_user(db: Session, user_id: int, reset_topics: bool = True) -> tuple[int, int, int]:
    items = _load_user_items(db, user_id)
    if reset_topics:
        topic_ids = db.scalars(select(Topic.id).where(Topic.user_id == user_id)).all()
        if topic_ids:
            db.execute(delete(ContentTopic).where(ContentTopic.topic_id.in_(topic_ids)))
        db.execute(delete(Topic).where(Topic.user_id == user_id))
        db.commit()
    else:
        item_ids = [item.id for item in items]
        if item_ids:
            db.execute(delete(ContentTopic).where(ContentTopic.knowledge_id.in_(item_ids)))
            db.commit()

    assignments = discover_topic_assignments(items)
    topics_created = 0
    links_created = 0
    for item in items:
        seen_topic_ids: set[int] = set()
        for label, confidence in assignments.get(item.id, []):
            topic, created = _get_or_create_topic(db, user_id, label, source_method="discovery")
            if topic.id in seen_topic_ids:
                continue
            seen_topic_ids.add(topic.id)
            if created:
                topics_created += 1
            db.add(
                ContentTopic(
                    user_id=user_id,
                    knowledge_id=item.id,
                    topic_id=topic.id,
                    confidence_score=confidence,
                )
            )
            log_knowledge_event(db, user_id=user_id, event_type="topic_linked", topic_id=topic.id, source="discovery", metadata={"item_id": item.id, "item_title": item.title, "confidence": confidence})
            links_created += 1
    db.commit()
    merge_similar_topics(db, user_id)
    return len(items), topics_created, links_created


def reassign_topics_for_user(db: Session, user_id: int) -> tuple[int, int, int]:
    return discover_topics_for_user(db, user_id, reset_topics=False)


def _extract_raw_candidate_scores(item: KnowledgeItem) -> Counter[str]:
    text = " ".join([item.title or "", item.summary or "", item.content or "", item.tags or ""])
    scores = extract_clean_topic_scores(text, max_topics=5)
    if scores:
        return scores

    for label, score in _extract_candidate_scores(item).most_common(3):
        scores[label] = score
    return scores


def preview_topic_discovery_for_item(item: KnowledgeItem) -> dict[str, list[str]]:
    raw_scores = _extract_raw_candidate_scores(item)
    extracted_topics = [label for label, _score in raw_scores.most_common(3)]
    assignments, _ = _build_item_topic_assignments([item])
    normalized_topics = [label for label, _confidence in assignments.get(item.id, [])][:3]

    if not extracted_topics:
        extracted_topics = normalized_topics.copy()

    return {
        "extracted_topics": extracted_topics[:3],
        "normalized_topics": normalized_topics[:3],
    }
