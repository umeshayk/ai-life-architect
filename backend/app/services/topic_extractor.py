import re
from collections import Counter

try:
    import spacy
except Exception:  # pragma: no cover - optional dependency at runtime
    spacy = None


EXTRA_STOP_WORDS = {
    "allow",
    "allows",
    "combine",
    "combines",
    "concept",
    "concepts",
    "control",
    "definition",
    "dimensional",
    "example",
    "examples",
    "help",
    "helps",
    "high",
    "improve",
    "improves",
    "matter",
    "notes",
    "question",
    "questions",
    "related",
    "relies",
    "store",
    "stores",
    "topics",
    "used",
    "uses",
    "using",
    "when",
    "how",
    "why",
    "with",
    "vs",
}

PHRASE_NORMALIZATION_MAP = {
    "bm25 vector": "Hybrid Search",
    "bm25 vector search": "Hybrid Search",
    "building second brain": "Building Second Brain",
    "controlled environment agriculture": "Controlled Environment Agriculture",
    "hybrid bm25 vector": "Hybrid Search",
    "hybrid bm25 vector search": "Hybrid Search",
    "hybrid search": "Hybrid Search",
    "keyword search": "Keyword Search",
    "keyword semantic search": "Hybrid Search",
    "second brain method": "Building Second Brain",
    "brain method": "Building Second Brain",
    "organize knowledge": "Knowledge Organization",
    "help organize knowledge": "Knowledge Organization",
    "knowledge organization": "Knowledge Organization",
    "personal productivity": "Personal Productivity",
    "semantic search": "Semantic Search",
    "vector search": "Vector Search",
    "vector database": "Vector Databases",
    "vector databases": "Vector Databases",
    "farm automation": "Farm Automation",
    "yield optimization": "Yield Optimization",
    "climate control": "Climate Control",
    "commercial property": "Commercial Property",
}

LOCATION_SPLIT_ANCHORS = {"temple", "temples"}
GENERIC_SINGLE_WORDS = {
    "bus",
    "file",
    "files",
    "itinerary",
    "knowledge",
    "link",
    "links",
    "note",
    "notes",
    "pdf",
    "summary",
    "title",
    "train",
}

BLOCKED_TOPIC_WORDS = {
    "allow",
    "allows",
    "combine",
    "combines",
    "help",
    "helps",
    "improve",
    "improves",
    "relies",
    "store",
    "stores",
    "use",
    "uses",
    "using",
    "with",
    "and",
    "or",
}

EXTRACTION_STOP_WORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}

_ALLOWED_SINGLE_TOKENS = {
    "ai",
    "embeddings",
    "fastapi",
    "mathematics",
    "mysuru",
    "react",
    "rag",
}

_NLP = None
_NLP_ATTEMPTED = False


def _get_nlp():
    global _NLP, _NLP_ATTEMPTED
    if _NLP_ATTEMPTED:
        return _NLP
    _NLP_ATTEMPTED = True
    if spacy is None:
        return None
    try:
        _NLP = spacy.load("en_core_web_sm")
    except Exception:
        _NLP = None
    return _NLP


def tokenize_topic_segment(text: str, stop_words: set[str], junk_topics: set[str]) -> list[str]:
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", text.lower())
    cleaned = []
    for token in tokens:
        normalized = re.sub(r"[^a-z0-9]+", "", token.lower())
        if not normalized:
            continue
        if normalized in stop_words or normalized in EXTRA_STOP_WORDS or normalized in junk_topics:
            continue
        cleaned.append(normalized)
    return cleaned


def extract_topic_phrases(tokens: list[str], max_words: int = 4) -> list[tuple[str, int]]:
    phrases: list[tuple[str, int]] = []
    seen: set[str] = set()

    for size in range(min(max_words, len(tokens)), 1, -1):
        for index in range(len(tokens) - size + 1):
            phrase = " ".join(tokens[index:index + size]).strip()
            for normalized_phrase in normalize_extracted_variants(phrase):
                if not normalized_phrase or normalized_phrase in seen:
                    continue
                seen.add(normalized_phrase)
                phrases.append((normalized_phrase, size))
    return phrases


def normalize_extracted_phrase(phrase: str) -> str:
    variants = normalize_extracted_variants(phrase)
    return variants[0] if variants else ""


def _clean_phrase_text(phrase: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9\s/-]+", " ", phrase.lower())
    normalized = normalized.replace("/", " ")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _is_valid_topic_phrase(phrase: str) -> bool:
    normalized = _clean_phrase_text(phrase)
    if not normalized:
        return False
    words = [word for word in normalized.split() if word]
    if not words or len(words) > 3:
        return False
    if any(word in BLOCKED_TOPIC_WORDS or word in EXTRACTION_STOP_WORDS for word in words):
        return False
    if len(words) == 1 and words[0] not in _ALLOWED_SINGLE_TOKENS and len(words[0]) < 5:
        return False
    return True


def _dedupe_topic_labels(labels: list[str]) -> list[str]:
    deduped: list[str] = []
    seen_keys: set[str] = set()
    for label in labels:
        variants = normalize_extracted_variants(label)
        normalized = variants[0] if variants else ""
        if not normalized:
            continue
        key = re.sub(r"\s+", " ", normalized.lower()).strip()
        if key in seen_keys:
            continue
        seen_keys.add(key)
        deduped.append(normalized)
    return deduped


def _extract_known_phrases(text: str) -> list[str]:
    normalized = _clean_phrase_text(text)
    if not normalized:
        return []

    matches: list[str] = []
    for phrase in sorted(PHRASE_NORMALIZATION_MAP, key=lambda item: (-len(item.split()), item)):
        if phrase in normalized:
            matches.append(PHRASE_NORMALIZATION_MAP[phrase])
    return _dedupe_topic_labels(matches)


def _extract_with_spacy(text: str, max_topics: int) -> list[str]:
    nlp = _get_nlp()
    if nlp is None or not text.strip():
        return []

    doc = nlp(text[:4000])
    ranked: list[str] = _extract_known_phrases(text)
    for chunk in doc.noun_chunks:
        chunk_text = chunk.text.strip()
        if not _is_valid_topic_phrase(chunk_text):
            continue
        normalized = normalize_extracted_phrase(chunk_text)
        if normalized:
            ranked.append(normalized)

    return _dedupe_topic_labels(ranked)[:max_topics]


def _topic_tokens_for_fallback(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", text.lower())
    cleaned: list[str] = []
    for token in tokens:
        normalized = re.sub(r"[^a-z0-9]+", "", token)
        if not normalized:
            continue
        if normalized in EXTRACTION_STOP_WORDS or normalized in EXTRA_STOP_WORDS:
            continue
        cleaned.append(normalized)
    return cleaned


def _extract_with_regex(text: str, max_topics: int) -> list[str]:
    ranked: list[str] = _extract_known_phrases(text)
    tokens = _topic_tokens_for_fallback(text)

    for phrase, _size in extract_topic_phrases(tokens, max_words=2):
        cleaned_phrase = _clean_phrase_text(phrase)
        if cleaned_phrase not in PHRASE_NORMALIZATION_MAP:
            continue
        if not _is_valid_topic_phrase(phrase):
            continue
        normalized = normalize_extracted_phrase(phrase)
        if normalized:
            ranked.append(normalized)

    for token in tokens:
        if token not in _ALLOWED_SINGLE_TOKENS:
            continue
        normalized = normalize_extracted_phrase(token)
        if normalized:
            ranked.append(normalized)

    return _dedupe_topic_labels(ranked)[:max_topics]


def extract_clean_topics(text: str, max_topics: int = 3) -> list[str]:
    if not text.strip():
        return []

    candidates = _extract_with_spacy(text, max_topics=max_topics)
    if not candidates:
        candidates = _extract_with_regex(text, max_topics=max_topics)
    return candidates[:max_topics]


def extract_clean_topic_scores(text: str, max_topics: int = 3) -> Counter[str]:
    scores: Counter[str] = Counter()
    for index, label in enumerate(extract_clean_topics(text, max_topics=max_topics), start=1):
        scores[label] += max(1.0, 4 - index)
    return scores


def normalize_extracted_variants(phrase: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", phrase.lower()).strip()
    if not normalized:
        return []

    normalized = _dedupe_phrase_words(normalized)

    if normalized in PHRASE_NORMALIZATION_MAP:
        return [PHRASE_NORMALIZATION_MAP[normalized]]

    if normalized.startswith("help "):
        normalized = normalized[5:]
    if normalized in {"key concept", "key concepts", "why it matters", "related topics"}:
        return []
    if normalized.startswith("building ") and "second brain" in normalized:
        return ["Building Second Brain"]
    if "organize knowledge" in normalized or "knowledge organization" in normalized:
        return ["Knowledge Organization"]
    if "bm25" in normalized and "vector" in normalized:
        return ["Hybrid Search"]
    if "vector search" in normalized:
        return ["Vector Search"]

    split_variants = _split_location_phrase(normalized)
    if split_variants:
        return split_variants

    return [_title_case_topic(normalized)]


def _dedupe_phrase_words(phrase: str) -> str:
    deduped_words: list[str] = []
    seen: set[str] = set()
    for word in phrase.split():
        if word in seen:
            continue
        seen.add(word)
        deduped_words.append(word)
    return " ".join(deduped_words)


def _split_location_phrase(normalized: str) -> list[str]:
    words = normalized.split()
    for anchor in LOCATION_SPLIT_ANCHORS:
        if anchor not in words:
            continue
        anchor_index = words.index(anchor)
        if anchor_index == 0 or anchor_index == len(words) - 1:
            continue
        main_words = words[: anchor_index + 1]
        location_words = words[anchor_index + 1 :]
        if len(main_words) > 4 or len(location_words) > 2:
            continue
        main_topic = _title_case_topic(" ".join(main_words))
        location_topic = _title_case_topic(" ".join(location_words))
        results = [main_topic]
        if location_topic and location_topic.lower() not in GENERIC_SINGLE_WORDS:
            results.append(location_topic)
        return results
    return []


def _title_case_topic(phrase: str) -> str:
    return " ".join(word.upper() if word in {"ai", "llm", "rag", "api"} else word.title() for word in phrase.split())

