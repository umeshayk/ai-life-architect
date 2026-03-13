import re


EXTRA_STOP_WORDS = {
    "combine",
    "concept",
    "concepts",
    "definition",
    "example",
    "help",
    "improve",
    "matter",
    "notes",
    "question",
    "related",
    "topics",
    "used",
    "when",
    "how",
    "why",
    "vs",
}

PHRASE_NORMALIZATION_MAP = {
    "bm25 vector": "Hybrid Search",
    "bm25 vector search": "Hybrid Search",
    "building second brain": "Building Second Brain",
    "hybrid bm25 vector": "Hybrid Search",
    "hybrid bm25 vector search": "Hybrid Search",
    "hybrid search": "Hybrid Search",
    "keyword semantic search": "Hybrid Search",
    "second brain method": "Building Second Brain",
    "brain method": "Building Second Brain",
    "organize knowledge": "Knowledge Organization",
    "help organize knowledge": "Knowledge Organization",
    "knowledge organization": "Knowledge Organization",
    "personal productivity": "Personal Productivity",
    "vector search": "Vector Search",
    "vector database": "Vector Databases",
    "vector databases": "Vector Databases",
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
