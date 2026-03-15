from __future__ import annotations

from collections import Counter, defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.topic import Topic
from app.services.cache_service import load_cached_payload, save_cached_payload
from app.services.graph_service import _build_graph_context, _topic_group
from app.services.ollama_service import generate_list
from app.services.topic_normalizer_service import canonical_topic_key, normalize_topic_label

CACHE_TTL_HOURS = 12
MIN_RULE_BRIDGES = 3
MAX_DOMAIN_PAIRS = 4

BRIDGE_RULES = {
    tuple(sorted(("AI", "Agriculture"))): [
        "Farm Automation",
        "Climate Control",
        "Sensor Monitoring",
        "Yield Optimization",
    ],
    tuple(sorted(("AI", "Knowledge"))): [
        "Knowledge Graph Construction",
        "AI Knowledge Architect",
        "Personal Knowledge Systems",
    ],
    tuple(sorted(("AI", "Business"))): [
        "Decision Intelligence",
        "Workflow Automation",
        "Forecasting Systems",
    ],
    tuple(sorted(("AI", "Mathematics"))): [
        "Evaluation Metrics",
        "Optimization Methods",
        "Statistical Modeling",
    ],
    tuple(sorted(("Agriculture", "Knowledge"))): [
        "Agriculture Knowledge Systems",
        "Action Planning",
        "Yield Optimization",
    ],
    tuple(sorted(("Agriculture", "Business"))): [
        "Farm Operations",
        "Market Planning",
        "Supply Chain Planning",
    ],
    tuple(sorted(("Business", "Knowledge"))): [
        "Decision Frameworks",
        "Action Planning",
        "Knowledge Management",
    ],
}

NOISE_TOKENS = {
    "add",
    "button",
    "click",
    "focu",
    "focus",
    "testing",
    "test",
    "topic",
    "topics",
}


def _cache_key(user_id: int, topic_count: int, domain: str = "", topic: str = "") -> str:
    normalized_domain = canonical_topic_key(domain) or "all"
    normalized_topic = canonical_topic_key(topic) or "global"
    return f"bridges:{user_id}:{normalized_domain}:{normalized_topic}:{max(1, topic_count)}"


def _existing_topic_keys(db: Session, user_id: int, context: dict) -> set[str]:
    saved_names = db.scalars(select(Topic.name).where(Topic.user_id == user_id)).all()
    combined = set(context.get("topic_names", [])) | set(saved_names)
    return {canonical_topic_key(name) for name in combined if canonical_topic_key(name)}


def _clean_bridge_topic(value: str) -> str:
    normalized = normalize_topic_label(value)
    if not normalized:
        normalized = " ".join((value or "").strip().split())
    normalized = normalized.strip()
    if not normalized or len(normalized.split()) > 4:
        return ""
    tokens = {token.lower() for token in normalized.split()}
    if tokens & NOISE_TOKENS:
        return ""
    return normalized


def _active_domain_pairs(context: dict, domain: str = "", topic: str = "") -> list[tuple[tuple[str, str], float, list[str]]]:
    pair_scores: Counter[tuple[str, str]] = Counter()
    pair_topics: defaultdict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    topic_groups = context.get("topic_to_groups", {})
    pair_counts = context.get("pair_counts", Counter())
    normalized_domain = canonical_topic_key(domain)
    focused_topic = (topic or "").strip()

    for (left, right), weight in pair_counts.items():
        left_group = topic_groups.get(left, _topic_group(left))
        right_group = topic_groups.get(right, _topic_group(right))
        if left_group == right_group or "General" in {left_group, right_group}:
            continue
        if normalized_domain and canonical_topic_key(left_group) != normalized_domain and canonical_topic_key(right_group) != normalized_domain:
            continue
        if focused_topic and focused_topic not in {left, right} and _topic_group(focused_topic) not in {left_group, right_group}:
            continue
        pair_key = tuple(sorted((left_group, right_group)))
        boost = 2.0 if focused_topic and focused_topic in {left, right} else 1.0
        pair_scores[pair_key] += weight * boost
        pair_topics[pair_key][left] += weight
        pair_topics[pair_key][right] += weight

    ranked: list[tuple[tuple[str, str], float, list[str]]] = []
    for pair_key, score in pair_scores.most_common(MAX_DOMAIN_PAIRS):
        topics = [name for name, _ in pair_topics[pair_key].most_common(6)]
        ranked.append((pair_key, float(score), topics))
    return ranked


def _rule_bridges(db: Session, user_id: int, context: dict, domain: str = "", topic: str = "", limit: int = 4) -> tuple[list[dict], float, list[tuple[tuple[str, str], float, list[str]]]]:
    existing_keys = _existing_topic_keys(db, user_id, context)
    ranked_pairs = _active_domain_pairs(context, domain=domain, topic=topic)
    suggestions: list[dict] = []
    seen: set[str] = set()

    for pair_key, pair_score, context_topics in ranked_pairs:
        candidates = BRIDGE_RULES.get(pair_key, [])
        for index, candidate in enumerate(candidates):
            cleaned = _clean_bridge_topic(candidate)
            candidate_key = canonical_topic_key(cleaned)
            if not cleaned or not candidate_key or candidate_key in existing_keys or candidate_key in seen:
                continue
            seen.add(candidate_key)
            confidence = max(0.58, min(0.94, 0.62 + pair_score / 12 - index * 0.04))
            suggestions.append(
                {
                    "topic": cleaned,
                    "domains": list(pair_key),
                    "confidence": round(confidence, 2),
                    "source": "rules",
                    "reason": f"{cleaned} can connect your {pair_key[0]} and {pair_key[1]} knowledge areas.",
                    "context_topics": context_topics[:4],
                }
            )
            if len(suggestions) >= limit:
                break
        if len(suggestions) >= limit:
            break

    confidence = 0.86 if len(suggestions) >= MIN_RULE_BRIDGES else 0.68 if suggestions else 0.0
    return suggestions[:limit], confidence, ranked_pairs


def _ai_bridge_suggestions(ranked_pairs: list[tuple[tuple[str, str], float, list[str]]], existing_keys: set[str], limit: int) -> list[dict]:
    results: list[dict] = []
    seen = set(existing_keys)

    for pair_key, _pair_score, context_topics in ranked_pairs:
        if len(results) >= limit:
            break
        prompt = (
            "You are helping expand a personal knowledge graph\n"
            "Return only short bridge topic names that connect the two domains\n"
            "Use 1 to 4 words per line\n"
            "Do not explain\n"
            "Do not return topics already listed\n\n"
            f"Domain A: {pair_key[0]}\n"
            f"Domain B: {pair_key[1]}\n"
            "Known nearby topics\n"
            + "\n".join(f"- {name}" for name in context_topics[:6])
            + "\n\nBridge topics:"
        )
        try:
            generated = generate_list(prompt, timeout=20)
        except Exception:
            continue

        for raw in generated:
            cleaned = _clean_bridge_topic(raw)
            cleaned_key = canonical_topic_key(cleaned)
            if not cleaned or not cleaned_key or cleaned_key in seen:
                continue
            seen.add(cleaned_key)
            results.append(
                {
                    "topic": cleaned,
                    "domains": list(pair_key),
                    "confidence": 0.72,
                    "source": "ai",
                    "reason": f"{cleaned} is a plausible bridge between {pair_key[0]} and {pair_key[1]} based on your nearby topics.",
                    "context_topics": context_topics[:4],
                }
            )
            if len(results) >= limit:
                break

    return results[:limit]


def discover_domain_bridges(db: Session, user_id: int, limit: int = 4, domain: str = "", topic: str = "") -> list[dict]:
    context = _build_graph_context(db, user_id)
    topic_count = int(db.scalar(select(func.count(Topic.id)).where(Topic.user_id == user_id)) or 0)
    cache_key = _cache_key(user_id, topic_count, domain, topic)
    cached = load_cached_payload(db, cache_key, ttl_hours=CACHE_TTL_HOURS)
    if cached and isinstance(cached.get("bridges"), list):
        return cached["bridges"][:limit]

    rule_results, rule_confidence, ranked_pairs = _rule_bridges(db, user_id, context, domain=domain, topic=topic, limit=limit)
    final_results = list(rule_results)

    # Keep bridge suggestions stable and practical. Only use AI when rules produce
    # almost nothing, otherwise the card feels like it changes its mind after each add.
    if len(final_results) == 0 or (topic and len(final_results) < 2 and rule_confidence < 0.7):
        ai_results = _ai_bridge_suggestions(
            ranked_pairs,
            _existing_topic_keys(db, user_id, context) | {canonical_topic_key(item["topic"]) for item in final_results},
            limit - len(final_results),
        )
        existing_final_keys = {canonical_topic_key(item["topic"]) for item in final_results}
        for item in ai_results:
            if len(final_results) >= limit:
                break
            if canonical_topic_key(item["topic"]) in existing_final_keys:
                continue
            final_results.append(item)
            existing_final_keys.add(canonical_topic_key(item["topic"]))

    payload = {"bridges": final_results[:limit]}
    save_cached_payload(db, cache_key, topic or domain or "domain-bridges", payload)
    return payload["bridges"][:limit]
