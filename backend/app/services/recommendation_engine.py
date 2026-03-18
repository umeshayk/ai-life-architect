from __future__ import annotations

from collections import defaultdict

from sqlalchemy.orm import Session

from app.services.ai_insight_store import build_context_hash, get_ai_insight, save_ai_insight
from app.services.domain_bridge_engine import discover_domain_bridges
from app.services.graph_service import _topic_group
from app.services.graph_state_service import get_user_graph_version
from app.services.knowledge_expansion_service import suggest_missing_topics
from app.services.knowledge_gap_analyzer import analyze_knowledge_gaps
from app.services.learning_path_service import build_learning_paths
from app.services.mastery_service import get_mastery_lookup
from app.services.topic_normalizer_service import canonical_topic_key
from app.services.topic_service import get_raw_topics_with_counts

LEARNING_PATH_WEIGHT = 5.0
GAP_WEIGHT = 3.0
GRAPH_NEIGHBOR_WEIGHT = 3.0
EXPANSION_WEIGHT = 2.0
BRIDGE_WEIGHT = 2.0
STARTED_TOPIC_BONUS = 0.8
MAX_EXPANSION_ANCHORS = 4
FOCUSED_TOPIC_WEIGHT = 4.0
FOCUSED_NEIGHBOR_WEIGHT = 2.5
FEATURE_TYPE = "recommendation_reason"


def _existing_topics(db: Session, user_id: int) -> tuple[dict[str, dict], int]:
    rows = get_raw_topics_with_counts(db, user_id)
    payload: dict[str, dict] = {}
    for topic, count in rows:
        key = canonical_topic_key(topic.name)
        if not key:
            continue
        payload[key] = {
            "name": topic.name,
            "count": count,
            "id": topic.id,
            "domain": _topic_group(topic.name),
        }
    return payload, len(rows)


def _build_candidate(topic_name: str, domain: str = "General", path_name: str | None = None) -> dict:
    return {
        "topic": topic_name,
        "domain": domain,
        "path_name": path_name,
        "score": 0.0,
        "signals": set(),
        "reasons": [],
        "started": False,
        "exists": False,
    }


def _add_signal(candidate_map: dict[str, dict], topic_name: str, *, score: float, signal: str, reason: str, domain: str = "General", path_name: str | None = None, started: bool = False, exists: bool = False) -> None:
    key = canonical_topic_key(topic_name)
    if not key:
        return
    candidate = candidate_map.setdefault(key, _build_candidate(topic_name, domain=domain, path_name=path_name))
    candidate["topic"] = topic_name
    candidate["domain"] = domain or candidate.get("domain") or "General"
    candidate["path_name"] = path_name or candidate.get("path_name")
    candidate["score"] += score
    candidate["signals"].add(signal)
    if reason not in candidate["reasons"]:
        candidate["reasons"].append(reason)
    candidate["started"] = candidate["started"] or started
    candidate["exists"] = candidate["exists"] or exists


def _path_topic_index(path: dict, topic_name: str) -> int:
    key = canonical_topic_key(topic_name)
    for index, topic in enumerate(path.get("topics", [])):
        if canonical_topic_key(topic.get("topic", "")) == key:
            return index
    return -1


def _collect_learning_path_signals(candidate_map: dict[str, dict], learning_paths: list[dict], domain: str = "") -> None:
    normalized_domain = canonical_topic_key(domain)
    for path in learning_paths:
        if normalized_domain and canonical_topic_key(path.get("domain", "")) != normalized_domain:
            continue
        next_topic = path.get("next_topic")
        if next_topic:
            _add_signal(
                candidate_map,
                next_topic["topic"],
                score=LEARNING_PATH_WEIGHT,
                signal="learning_path",
                reason=f"This is the next topic in your {path['path_name']} learning path.",
                domain=path["domain"],
                path_name=path["path_name"],
                started=next_topic.get("action") == "focus",
                exists=next_topic.get("action") == "focus",
            )

        topics = path.get("topics", [])
        for index, topic in enumerate(topics):
            if topic.get("state") == "covered":
                continue
            previous_states = [item.get("state") for item in topics[max(0, index - 2):index]]
            support = sum(1 for state in previous_states if state in {"covered", "started"})
            if support <= 0:
                continue
            bonus = GRAPH_NEIGHBOR_WEIGHT + (0.5 if support > 1 else 0.0)
            _add_signal(
                candidate_map,
                topic["topic"],
                score=bonus,
                signal="graph_neighbor",
                reason=f"{topic['topic']} fits naturally after your current topics in {path['path_name']}.",
                domain=path["domain"],
                path_name=path["path_name"],
                started=topic.get("action") == "focus",
                exists=topic.get("action") == "focus",
            )


def _collect_gap_signals(candidate_map: dict[str, dict], gaps: list[dict]) -> None:
    for path in gaps:
        for item in path.get("missing_topics", []):
            started = item.get("action") == "focus" or item.get("state") == "started"
            _add_signal(
                candidate_map,
                item["topic"],
                score=GAP_WEIGHT,
                signal="knowledge_gap",
                reason=item.get("reason") or f"{item['topic']} is still missing in {path['path_name']}.",
                domain=path["domain"],
                path_name=path["path_name"],
                started=started,
                exists=started,
            )


def _collect_focused_topic_signals(candidate_map: dict[str, dict], db: Session, user_id: int, learning_paths: list[dict], focused_topic: str = "", domain: str = "") -> None:
    focused_key = canonical_topic_key(focused_topic)
    if not focused_key:
        return
    normalized_domain = canonical_topic_key(domain)
    for path in learning_paths:
        if normalized_domain and canonical_topic_key(path.get("domain", "")) != normalized_domain:
            continue
        topics = path.get("topics", [])
        index = _path_topic_index(path, focused_topic)
        if index < 0:
            continue
        for next_topic in topics[index + 1:index + 3]:
            if next_topic.get("state") == "covered":
                continue
            started = next_topic.get("action") == "focus" or next_topic.get("state") == "started"
            _add_signal(
                candidate_map,
                next_topic["topic"],
                score=FOCUSED_TOPIC_WEIGHT if next_topic is topics[index + 1] else FOCUSED_NEIGHBOR_WEIGHT,
                signal="focused_topic",
                reason=f"{next_topic['topic']} is the next useful step from {focused_topic} in {path['path_name']}.",
                domain=path["domain"],
                path_name=path["path_name"],
                started=started,
                exists=started,
            )

    payload = suggest_missing_topics(db, user_id, focused_topic, limit=4, refresh=False)
    for suggestion in payload.get("suggestions", []):
        _add_signal(
            candidate_map,
            suggestion,
            score=FOCUSED_NEIGHBOR_WEIGHT,
            signal="focused_topic",
            reason=f"{suggestion} is strongly related to the topic you're exploring: {focused_topic}.",
            domain=domain or _topic_group(suggestion),
        )


def _collect_expansion_signals(candidate_map: dict[str, dict], db: Session, user_id: int, learning_paths: list[dict], domain: str = "") -> None:
    normalized_domain = canonical_topic_key(domain)
    anchor_topics: list[tuple[str, str, str]] = []
    for path in learning_paths:
        if normalized_domain and canonical_topic_key(path.get("domain", "")) != normalized_domain:
            continue
        next_topic = path.get("next_topic")
        if next_topic:
            index = _path_topic_index(path, next_topic["topic"])
            if index > 0:
                previous_topic = path["topics"][index - 1]
                anchor_topics.append((previous_topic["topic"], path["domain"], path["path_name"]))
        for topic in path.get("topics", []):
            if topic.get("state") == "started":
                anchor_topics.append((topic["topic"], path["domain"], path["path_name"]))

    deduped_anchors: list[tuple[str, str, str]] = []
    seen_anchor_keys: set[str] = set()
    for topic_name, topic_domain, path_name in anchor_topics:
        key = canonical_topic_key(topic_name)
        if not key or key in seen_anchor_keys:
            continue
        seen_anchor_keys.add(key)
        deduped_anchors.append((topic_name, topic_domain, path_name))
        if len(deduped_anchors) >= MAX_EXPANSION_ANCHORS:
            break

    bridge_domains: defaultdict[str, set[str]] = defaultdict(set)
    for topic_name, topic_domain, path_name in deduped_anchors:
        payload = suggest_missing_topics(db, user_id, topic_name, limit=3, refresh=False)
        for suggestion in payload.get("suggestions", []):
            _add_signal(
                candidate_map,
                suggestion,
                score=EXPANSION_WEIGHT,
                signal="expansion",
                reason=f"{suggestion} is a useful adjacent concept around {topic_name}.",
                domain=topic_domain,
                path_name=path_name,
            )
            bridge_domains[canonical_topic_key(suggestion)].add(topic_domain)

    bridges_payload = discover_domain_bridges(db, user_id, limit=4, domain=domain, topic="")
    for bridge in bridges_payload.get("bridges", []):
        _add_signal(
            candidate_map,
            bridge["topic"],
            score=BRIDGE_WEIGHT,
            signal="bridge",
            reason=bridge.get("reason") or "This topic helps connect important areas of your graph.",
            domain=bridge.get("domains", [domain or _topic_group(bridge["topic"])])[0] if bridge.get("domains") else (domain or _topic_group(bridge["topic"])),
        )

    for candidate_key, domains in bridge_domains.items():
        if len(domains) < 2:
            continue
        candidate = candidate_map.get(candidate_key)
        if not candidate:
            continue
        candidate["score"] += BRIDGE_WEIGHT
        candidate["signals"].add("bridge")
        bridge_reason = "This topic helps connect concepts across multiple active parts of your graph."
        if bridge_reason not in candidate["reasons"]:
            candidate["reasons"].append(bridge_reason)


def _finalize_candidates(candidate_map: dict[str, dict], existing_topics: dict[str, dict], mastery_lookup: dict[str, float], domain: str = "") -> list[dict]:
    normalized_domain = canonical_topic_key(domain)
    results: list[dict] = []
    for key, candidate in candidate_map.items():
        existing = existing_topics.get(key)
        mastery_score = mastery_lookup.get(key, 0.0)
        if mastery_score >= 0.82:
            continue
        if existing and existing.get("count", 0) >= 3 and mastery_score >= 0.6:
            continue

        action = "focus" if existing else "add"
        if candidate.get("started"):
            action = "focus"

        score = candidate["score"] + (STARTED_TOPIC_BONUS if action == "focus" else 0.0) - (mastery_score * 3.0)
        topic_domain = candidate.get("domain") or existing.get("domain") if existing else candidate.get("domain")
        topic_domain = topic_domain or _topic_group(candidate["topic"])
        if normalized_domain and canonical_topic_key(topic_domain) != normalized_domain:
            continue

        unique_reasons = candidate.get("reasons", [])
        reason = unique_reasons[0] if unique_reasons else f"{candidate['topic']} is a strong next concept for your graph."
        if "learning_path" in candidate["signals"] and "knowledge_gap" in candidate["signals"]:
            reason = f"{candidate['topic']} is the next step in {candidate['path_name']} and fills a current gap in your graph."
        elif "bridge" in candidate["signals"]:
            reason = f"{candidate['topic']} helps connect important areas of your current graph."
        elif "expansion" in candidate["signals"] and "graph_neighbor" in candidate["signals"]:
            reason = f"{candidate['topic']} deepens your current neighborhood of related concepts."

        confidence = max(0.55, min(0.97, 0.52 + score / 12.0))
        results.append(
            {
                "topic": candidate["topic"],
                "score": round(score, 2),
                "confidence": round(confidence, 2),
                "reason": reason,
                "source_signals": sorted(candidate["signals"]),
                "domain": topic_domain,
                "action": action,
                "path_name": candidate.get("path_name"),
                "mastery_score": round(mastery_score, 2),
            }
        )
    return sorted(results, key=lambda item: (-item["score"], -item["confidence"], item["topic"]))


def _recommendation_context_hash(existing_topics: dict[str, dict], learning_paths: list[dict], gaps: list[dict], mastery_lookup: dict[str, float], domain: str, topic: str) -> str:
    return build_context_hash(
        {
            "domain": domain,
            "topic": topic,
            "existing_topics": sorted(existing_topics.keys())[:30],
            "learning_paths": [
                {
                    "path_name": path.get("path_name"),
                    "domain": path.get("domain"),
                    "progress_percent": path.get("progress_percent"),
                    "covered_count": path.get("covered_count"),
                    "total_count": path.get("total_count"),
                    "next_topic": (path.get("next_topic") or {}).get("topic"),
                }
                for path in learning_paths
            ],
            "gaps": [
                {
                    "path_name": path.get("path_name"),
                    "domain": path.get("domain"),
                    "missing_topics": [item.get("topic") for item in path.get("missing_topics", [])[:6]],
                }
                for path in gaps
            ],
            "mastery_keys": sorted(key for key, score in mastery_lookup.items() if score >= 0.5)[:20],
            "version": "v2",
        }
    )


def recommend_next_topics(db: Session, user_id: int, limit: int = 3, domain: str = "", topic: str = "", refresh: bool = False) -> dict:
    existing_topics, _topic_count = _existing_topics(db, user_id)
    learning_paths = build_learning_paths(db, user_id)
    gaps = analyze_knowledge_gaps(db, user_id, refresh=False, domain=domain)
    mastery_lookup = get_mastery_lookup(db, user_id)
    graph_version = get_user_graph_version(db, user_id)
    context_hash = _recommendation_context_hash(existing_topics, learning_paths, gaps, mastery_lookup, domain, topic)
    topic_scope = topic or domain or "global"

    if not refresh:
        cached = get_ai_insight(db, user_id, topic_scope, FEATURE_TYPE, context_hash, graph_version)
        if cached and isinstance(cached.get("recommendations"), list):
            cached["recommendations"] = cached["recommendations"][:limit]
            return cached

    candidate_map: dict[str, dict] = {}
    _collect_learning_path_signals(candidate_map, learning_paths, domain=domain)
    _collect_gap_signals(candidate_map, gaps)
    _collect_focused_topic_signals(candidate_map, db, user_id, learning_paths, focused_topic=topic, domain=domain)
    _collect_expansion_signals(candidate_map, db, user_id, learning_paths, domain=domain)

    recommendations = _finalize_candidates(candidate_map, existing_topics, mastery_lookup, domain=domain)
    payload = {"recommendations": recommendations[: max(limit, 3)]}
    return save_ai_insight(
        db,
        user_id=user_id,
        topic_name=topic_scope,
        feature_type=FEATURE_TYPE,
        context_hash=context_hash,
        graph_version=graph_version,
        source="hybrid",
        payload=payload,
        ttl_hours=72,
    )


def recommend_next_topic(db: Session, user_id: int, domain: str = "", topic: str = "", refresh: bool = False) -> dict | None:
    payload = recommend_next_topics(db, user_id, limit=1, domain=domain, topic=topic, refresh=refresh)
    recommendations = payload.get("recommendations") or []
    return recommendations[0] if recommendations else None
