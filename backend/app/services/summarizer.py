import re
from collections import Counter


STOP_WORDS = {
    "a",
    "about",
    "after",
    "all",
    "also",
    "an",
    "and",
    "are",
    "around",
    "as",
    "at",
    "be",
    "been",
    "being",
    "but",
    "by",
    "can",
    "could",
    "did",
    "do",
    "does",
    "each",
    "few",
    "for",
    "from",
    "had",
    "has",
    "have",
    "having",
    "how",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "just",
    "many",
    "may",
    "more",
    "most",
    "new",
    "not",
    "of",
    "one",
    "on",
    "other",
    "or",
    "our",
    "out",
    "over",
    "should",
    "some",
    "such",
    "that",
    "the",
    "their",
    "them",
    "there",
    "these",
    "they",
    "this",
    "those",
    "to",
    "up",
    "use",
    "using",
    "very",
    "was",
    "we",
    "were",
    "what",
    "when",
    "which",
    "who",
    "will",
    "with",
    "you",
    "your",
}


def _clean_tokens(text: str) -> list[str]:
    raw_tokens = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text.lower())
    return [token for token in raw_tokens if token not in STOP_WORDS]


def _extract_tag_phrases(title: str, content: str, limit: int = 5) -> list[str]:
    combined = f"{title}. {content}"
    segments = re.split(r"[.!?\n,:;()\-]+", combined)
    phrase_counts: Counter[str] = Counter()
    word_counts: Counter[str] = Counter()

    for segment in segments:
        tokens = _clean_tokens(segment)
        if not tokens:
            continue

        for size in (3, 2):
            for index in range(len(tokens) - size + 1):
                phrase = " ".join(tokens[index:index + size])
                phrase_counts[phrase] += 1

        for token in tokens:
            word_counts[token] += 1

    tags: list[str] = []
    for phrase, _ in phrase_counts.most_common(limit * 2):
        if phrase not in tags:
            tags.append(phrase)
        if len(tags) >= limit:
            return tags

    for word, _ in word_counts.most_common(limit * 2):
        if word not in tags:
            tags.append(word)
        if len(tags) >= limit:
            break

    return tags


def build_summary_and_tags(title: str, content: str) -> tuple[str, list[str]]:
    normalized = " ".join(content.split())
    sentences = re.split(r"(?<=[.!?])\s+", normalized)
    summary = " ".join(sentences[:2]).strip() if sentences and sentences[0] else normalized[:280]
    summary = summary[:280] if summary else f"Summary for {title}"
    tags = _extract_tag_phrases(title, content, limit=5)
    return summary, tags
