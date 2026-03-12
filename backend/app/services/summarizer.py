import re
from collections import Counter


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "was",
    "were",
    "with",
}


def build_summary_and_tags(title: str, content: str) -> tuple[str, list[str]]:
    normalized = " ".join(content.split())
    sentences = re.split(r"(?<=[.!?])\s+", normalized)
    summary = " ".join(sentences[:2]).strip() if sentences and sentences[0] else normalized[:280]
    summary = summary[:280] if summary else f"Summary for {title}"

    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", f"{title} {content}".lower())
    counts = Counter(word for word in words if word not in STOP_WORDS)
    tags = [word for word, _ in counts.most_common(5)]
    return summary, tags
