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
            if phrase in seen:
                continue
            seen.add(phrase)
            phrases.append((normalize_extracted_phrase(phrase), size))
    return phrases


def normalize_extracted_phrase(phrase: str) -> str:
    normalized = re.sub(r"\s+", " ", phrase.lower()).strip()
    if not normalized:
        return ""

    if normalized in PHRASE_NORMALIZATION_MAP:
        return PHRASE_NORMALIZATION_MAP[normalized]

    if normalized.startswith("help "):
        normalized = normalized[5:]
    if normalized in {"key concept", "key concepts", "why it matters", "related topics"}:
        return ""
    if normalized.startswith("building ") and "second brain" in normalized:
        return "Building Second Brain"
    if "organize knowledge" in normalized or "knowledge organization" in normalized:
        return "Knowledge Organization"
    if "bm25" in normalized and "vector" in normalized:
        return "Hybrid Search"
    if "vector search" in normalized:
        return "Vector Search"

    return " ".join(word.upper() if word in {"ai", "llm", "rag", "api"} else word.title() for word in normalized.split())
