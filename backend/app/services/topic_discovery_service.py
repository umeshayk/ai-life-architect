import re
from collections import Counter, defaultdict

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.models.content_topic import ContentTopic
from app.models.knowledge import KnowledgeItem
from app.models.knowledge_connection import KnowledgeConnection
from app.models.topic import Topic


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
    "how",
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
    "use",
    "using",
    "was",
    "were",
    "with",
    "you",
    "your",
}

JUNK_TOPICS = {
    "personal",
    "users",
    "including",
    "located",
    "txt",
    "pdf",
    "note",
    "notes",
    "file",
    "files",
    "content",
    "title",
    "summary",
    "document",
    "documents",
    "link",
    "links",
    "item",
    "items",
    "knowledge",
}

ALIAS_MAP = {
    "ai": "AI / Technology",
    "a i": "AI / Technology",
    "artificial intelligence": "AI / Technology",
    "ai technology": "AI / Technology",
    "ai notes": "AI / Technology",
    "llm": "LLM Systems",
    "llm system": "LLM Systems",
    "llm systems": "LLM Systems",
    "semantic search": "Semantic Search",
    "vector database": "Vector Databases",
    "vector databases": "Vector Databases",
    "embedding": "Embeddings",
    "embeddings": "Embeddings",
    "knowledge mgmt": "Knowledge Management",
    "knowledge management": "Knowledge Management",
    "second brain": "Knowledge Management",
    "mushroom": "Mushroom Farming",
    "mushroom farming": "Mushroom Farming",
    "oyster mushroom farming": "Mushroom Farming",
    "farm business": "Farm Business",
    "hydroponic farming": "Hydroponic Farming",
    "hydroponics": "Hydroponic Farming",
    "fastapi": "FastAPI",
    "react": "React",
    "travel spiritual": "Travel / Spiritual",
    "jyotirlinga": "Travel / Spiritual",
    "temple": "Travel / Spiritual",
    "vedic math": "Mathematics",
    "vedic mathematics": "Mathematics",
    "math": "Mathematics",
}

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

    if singular_normalized in ALIAS_MAP:
        return ALIAS_MAP[singular_normalized]

    display_words = {
        "ai": "AI",
        "llm": "LLM",
        "rag": "RAG",
        "api": "API",
        "fastapi": "FastAPI",
    }
    final_label = " ".join(display_words.get(word, word.title()) for word in singular_normalized.split())
    return final_label.strip()


def _is_junk_topic(label: str) -> bool:
    normalized = _normalize_words(label)
    if not normalized:
        return True
    if normalized in JUNK_TOPICS:
        return True
    tokens = normalized.split()
    if len(tokens) == 1 and tokens[0] in JUNK_TOPICS:
        return True
    if all(token in STOP_WORDS or token in JUNK_TOPICS for token in tokens):
        return True
    return False


def _tokenize_segment(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", text.lower())
    cleaned = []
    for token in tokens:
        normalized = _normalize_words(token)
        if not normalized or normalized in STOP_WORDS or normalized in JUNK_TOPICS:
            continue
        cleaned.append(normalized)
    return cleaned


def _extract_candidate_scores(item: KnowledgeItem) -> Counter[str]:
    scores: Counter[str] = Counter()
    content_excerpt = (item.content or "")[:800]
    sources = [
        (" ".join(tag.strip() for tag in (item.tags or "").split(",") if tag.strip()), 2.2),
        (item.title or "", 1.6),
        (item.summary or "", 1.0),
        (content_excerpt, 0.55),
    ]

    for text, weight in sources:
        if not text:
            continue
        segments = re.split(r"[.!?\n,:;()\-/]+", text)
        for segment in segments:
            tokens = _tokenize_segment(segment)
            if not tokens:
                continue
            for size, multiplier in ((3, 1.45), (2, 1.25), (1, 0.75)):
                for index in range(len(tokens) - size + 1):
                    phrase = " ".join(tokens[index:index + size])
                    label = normalize_topic_name(phrase)
                    if not label or _is_junk_topic(label):
                        continue
                    scores[label] += weight * multiplier
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


def _select_global_topics(
    items: list[KnowledgeItem],
    item_candidates: dict[int, Counter[str]],
) -> tuple[Counter[str], Counter[str]]:
    global_item_counts: Counter[str] = Counter()
    global_scores: Counter[str] = Counter()

    for item in items:
        for label, score in item_candidates[item.id].items():
            global_scores[label] += score
            global_item_counts[label] += 1

    for item in items:
        for connection in item.outgoing_connections:
            if connection.target_item is None or connection.target_item.id not in item_candidates:
                continue
            shared = set(item_candidates[item.id]).intersection(item_candidates[connection.target_item.id])
            for label in shared:
                global_scores[label] += 0.45

    return global_item_counts, global_scores


def discover_topic_assignments(items: list[KnowledgeItem]) -> dict[int, list[tuple[str, float]]]:
    if not items:
        return {}

    item_candidates = {item.id: _extract_candidate_scores(item) for item in items}
    global_item_counts, global_scores = _select_global_topics(items, item_candidates)

    selected_labels = {
        label
        for label, count in global_item_counts.items()
        if (count >= 2 or global_scores[label] >= 3.4) and not _is_junk_topic(label)
    }
    if not selected_labels:
        selected_labels = {
            label
            for label, _ in global_scores.most_common(12)
            if not _is_junk_topic(label)
        }

    assignments: dict[int, list[tuple[str, float]]] = {}
    for item in items:
        local_scores = item_candidates[item.id].copy()

        for connection in item.outgoing_connections:
            if connection.target_item is None or connection.target_item.id not in item_candidates:
                continue
            for label, score in item_candidates[connection.target_item.id].most_common(4):
                local_scores[label] += score * 0.16

        ranked = []
        for label, score in local_scores.items():
            if label not in selected_labels and global_item_counts[label] < 2 and score < 2.0:
                continue
            confidence = min(0.95, 0.3 + score * 0.1 + min(global_item_counts[label], 4) * 0.08)
            ranked.append((label, round(confidence, 2)))

        ranked.sort(key=lambda pair: (local_scores[pair[0]], pair[1]), reverse=True)
        deduped: list[tuple[str, float]] = []
        seen = set()
        for label, confidence in ranked:
            if label in seen or _is_junk_topic(label):
                continue
            seen.add(label)
            deduped.append((label, confidence))
            if len(deduped) >= 3:
                break

        if not deduped:
            deduped = _fallback_topics(item)

        assignments[item.id] = deduped[:3]

    return assignments


def _get_or_create_topic(db: Session, user_id: int, name: str) -> tuple[Topic, bool]:
    topic = db.scalar(select(Topic).where(Topic.user_id == user_id, Topic.name == name))
    if topic is not None:
        return topic, False
    topic = Topic(user_id=user_id, name=name)
    db.add(topic)
    db.flush()
    return topic, True


def _load_user_items(db: Session, user_id: int) -> list[KnowledgeItem]:
    return db.scalars(
        select(KnowledgeItem)
        .options(selectinload(KnowledgeItem.outgoing_connections).selectinload(KnowledgeConnection.target_item))
        .where(KnowledgeItem.user_id == user_id)
    ).all()


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
        for label, confidence in assignments.get(item.id, []):
            topic, created = _get_or_create_topic(db, user_id, label)
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
            links_created += 1
    db.commit()
    return len(items), topics_created, links_created


def reassign_topics_for_user(db: Session, user_id: int) -> tuple[int, int, int]:
    return discover_topics_for_user(db, user_id, reset_topics=False)
