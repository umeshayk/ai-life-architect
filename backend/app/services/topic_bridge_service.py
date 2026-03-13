from __future__ import annotations

import math
import re
from collections import defaultdict
from dataclasses import dataclass

import requests
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.topic import Topic
from app.schemas.graph import GraphEdge, GraphNode
from app.services.embeddings import generate_embedding
from app.services.topic_normalizer_service import normalize_topic_label


settings = get_settings()

BRIDGE_SIMILARITY_THRESHOLD = 0.44
MAX_BRIDGES = 6
GENERIC_TOPIC_TOKENS = {
    "ai",
    "agriculture",
    "business",
    "domain",
    "general",
    "group",
    "knowledge",
    "mathematics",
    "math",
    "property",
    "spiritual",
    "system",
    "systems",
    "technology",
    "topic",
    "topics",
    "travel",
}
TITLE_STOP_WORDS = {
    "a",
    "an",
    "and",
    "at",
    "by",
    "for",
    "from",
    "how",
    "in",
    "into",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}


@dataclass
class BridgeCandidate:
    source: str
    target: str
    source_group: str
    target_group: str
    label: str
    score: float
    shared_keyword_count: int
    shared_note_count: int
    linked_titles: list[str]


def _tokenize(value: str) -> list[str]:
    cleaned = re.sub(r"[^a-z0-9\s]+", " ", (value or "").lower())
    return [token for token in cleaned.split() if token and token not in TITLE_STOP_WORDS]


def _topic_tokens(topic_name: str, linked_titles: list[str]) -> set[str]:
    topic_tokens = {token for token in _tokenize(topic_name) if token not in GENERIC_TOPIC_TOKENS}
    title_tokens = {
        token
        for title in linked_titles[:6]
        for token in _tokenize(title)
        if token not in GENERIC_TOPIC_TOKENS
    }
    return topic_tokens | title_tokens


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    numerator = sum(l * r for l, r in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left)) or 1.0
    right_norm = math.sqrt(sum(value * value for value in right)) or 1.0
    return max(0.0, numerator / (left_norm * right_norm))


def _shared_note_score(left_titles: list[str], right_titles: list[str]) -> tuple[float, int]:
    left_tokens = {
        tuple(_tokenize(title))
        for title in left_titles[:8]
        if _tokenize(title)
    }
    right_tokens = {
        tuple(_tokenize(title))
        for title in right_titles[:8]
        if _tokenize(title)
    }
    overlap = len(left_tokens & right_tokens)
    denominator = max(1, min(len(left_tokens), len(right_tokens)))
    return overlap / denominator, overlap


def _keyword_overlap_score(left_tokens: set[str], right_tokens: set[str]) -> tuple[float, int]:
    if not left_tokens or not right_tokens:
        return 0.0, 0
    overlap = left_tokens & right_tokens
    union = left_tokens | right_tokens
    return len(overlap) / max(1, len(union)), len(overlap)


def _fallback_bridge_label(source_group: str, target_group: str, source: str, target: str) -> str:
    if source_group == "AI":
        return f"AI in {target_group}"
    if target_group == "AI":
        return f"AI in {source_group}"
    if "Property" in source or "Property" in target:
        return "Cross-Domain Property Intelligence"
    return f"{source_group} and {target_group}"


def _generate_bridge_label(source_group: str, target_group: str, source: str, target: str) -> str:
    prompt = (
        "Create a concise bridge topic label that connects two knowledge areas.\n"
        "Return only one short title-cased phrase, 2 to 5 words, no punctuation.\n"
        f"Source topic: {source} ({source_group})\n"
        f"Target topic: {target} ({target_group})\n"
        "Bridge label:"
    )
    try:
        response = requests.post(
            settings.ollama_url,
            json={"model": settings.ollama_model, "prompt": prompt, "stream": False},
            timeout=20,
        )
        response.raise_for_status()
        label = (response.json().get("response") or "").strip().splitlines()[0].strip()
    except Exception:
        label = ""

    if not label:
        label = _fallback_bridge_label(source_group, target_group, source, target)

    cleaned = normalize_topic_label(label) or label.strip()
    if not cleaned or len(cleaned.split()) > 6:
        return _fallback_bridge_label(source_group, target_group, source, target)
    return cleaned


def _persist_bridge_topics(db: Session, user_id: int, bridge_names: list[str]) -> dict[str, Topic]:
    existing_bridges = db.scalars(
        select(Topic).where(Topic.user_id == user_id, Topic.type == "bridge")
    ).all()
    existing_by_name = {topic.name: topic for topic in existing_bridges}

    for topic in existing_bridges:
        if topic.name not in bridge_names:
            db.execute(delete(Topic).where(Topic.id == topic.id))

    persisted: dict[str, Topic] = {}
    for bridge_name in bridge_names:
        topic = existing_by_name.get(bridge_name)
        if topic is None:
            topic = Topic(user_id=user_id, name=bridge_name, type="bridge")
            db.add(topic)
            db.flush()
        elif topic.type != "bridge":
            continue
        persisted[bridge_name] = topic

    db.commit()
    return persisted


def build_topic_bridges(
    db: Session,
    user_id: int,
    topic_names: list[str],
    topic_to_titles: dict[str, list[str]],
    topic_group_getter,
) -> tuple[list[GraphNode], list[GraphEdge]]:
    if len(topic_names) < 2:
        return [], []

    grouped_topics: dict[str, list[str]] = defaultdict(list)
    for topic_name in topic_names:
        group = topic_group_getter(topic_name)
        grouped_topics[group].append(topic_name)

    if len(grouped_topics) < 2:
        return [], []

    topic_embeddings = {
        topic_name: generate_embedding("\n".join([topic_name] + topic_to_titles.get(topic_name, [])[:4]))
        for topic_name in topic_names
    }
    topic_tokens = {
        topic_name: _topic_tokens(topic_name, topic_to_titles.get(topic_name, []))
        for topic_name in topic_names
    }

    candidates: list[BridgeCandidate] = []
    processed_group_pairs: set[tuple[str, str]] = set()
    for left_group, left_topics in grouped_topics.items():
        for right_group, right_topics in grouped_topics.items():
            if left_group >= right_group:
                continue
            group_key = (left_group, right_group)
            if group_key in processed_group_pairs:
                continue
            processed_group_pairs.add(group_key)

            best_pair: BridgeCandidate | None = None
            for left_topic in left_topics:
                for right_topic in right_topics:
                    embedding_score = _cosine_similarity(
                        topic_embeddings[left_topic],
                        topic_embeddings[right_topic],
                    )
                    keyword_score, shared_keyword_count = _keyword_overlap_score(
                        topic_tokens[left_topic],
                        topic_tokens[right_topic],
                    )
                    shared_note_score, shared_note_count = _shared_note_score(
                        topic_to_titles.get(left_topic, []),
                        topic_to_titles.get(right_topic, []),
                    )
                    score = round(
                        embedding_score * 0.68 + keyword_score * 0.22 + shared_note_score * 0.10,
                        3,
                    )
                    if score < BRIDGE_SIMILARITY_THRESHOLD:
                        continue

                    linked_titles = []
                    seen_titles: set[str] = set()
                    for title in topic_to_titles.get(left_topic, []) + topic_to_titles.get(right_topic, []):
                        if title in seen_titles:
                            continue
                        seen_titles.add(title)
                        linked_titles.append(title)
                        if len(linked_titles) >= 8:
                            break

                    candidate = BridgeCandidate(
                        source=left_topic,
                        target=right_topic,
                        source_group=left_group,
                        target_group=right_group,
                        label="",
                        score=score,
                        shared_keyword_count=shared_keyword_count,
                        shared_note_count=shared_note_count,
                        linked_titles=linked_titles,
                    )
                    if best_pair is None or candidate.score > best_pair.score:
                        best_pair = candidate

            if best_pair is not None:
                best_pair.label = _generate_bridge_label(
                    best_pair.source_group,
                    best_pair.target_group,
                    best_pair.source,
                    best_pair.target,
                )
                candidates.append(best_pair)

    if not candidates:
        return [], []

    candidates.sort(key=lambda candidate: (-candidate.score, candidate.label))
    deduped_candidates: list[BridgeCandidate] = []
    seen_labels: set[str] = set()
    for candidate in candidates:
        if candidate.label in seen_labels:
            continue
        seen_labels.add(candidate.label)
        deduped_candidates.append(candidate)
        if len(deduped_candidates) >= MAX_BRIDGES:
            break

    bridge_topics = _persist_bridge_topics(db, user_id, [candidate.label for candidate in deduped_candidates])

    bridge_nodes: list[GraphNode] = []
    bridge_edges: list[GraphEdge] = []
    for candidate in deduped_candidates:
        topic = bridge_topics.get(candidate.label)
        if topic is None:
            continue

        importance = round(max(1.0, candidate.score * 10 + len(candidate.linked_titles) * 0.25), 2)
        bridge_nodes.append(
            GraphNode(
                id=candidate.label,
                label=candidate.label,
                type="bridge",
                group="Bridge",
                size=0,
                importance=importance,
                connection_count=2,
                linked_titles=candidate.linked_titles[:8],
                linked_count=len(candidate.linked_titles),
                related_titles=[candidate.source, candidate.target],
            )
        )
        bridge_edges.append(
            GraphEdge(
                source=candidate.source,
                target=candidate.label,
                type="topic_bridge_relationship",
                weight=max(1.0, candidate.score * 4),
            )
        )
        bridge_edges.append(
            GraphEdge(
                source=candidate.label,
                target=candidate.target,
                type="topic_bridge_relationship",
                weight=max(1.0, candidate.score * 4),
            )
        )

    return bridge_nodes, bridge_edges
