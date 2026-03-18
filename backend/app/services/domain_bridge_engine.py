from __future__ import annotations

from collections import Counter, defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.topic import Topic
from app.services.ai_insight_store import build_context_hash, get_ai_insight, save_ai_insight
from app.services.graph_service import _build_graph_context, _topic_group
from app.services.graph_state_service import get_user_graph_version
from app.services.ollama_service import generate_list
from app.services.topic_cluster_service import infer_topic_cluster
from app.services.topic_normalizer_service import canonical_topic_key, normalize_topic_label

FEATURE_TYPE = "bridge_suggestion"
MIN_RULE_BRIDGES = 3
MAX_DOMAIN_PAIRS = 4

BRIDGE_RULES = {
    tuple(sorted(("AI", "Agriculture"))): [
        "Farm Automation",
        "Sensor Monitoring",
        "Predictive Irrigation",
        "Yield Optimization",
    ],
    tuple(sorted(("AI", "Knowledge"))): [
        "Knowledge Graph Construction",
        "Semantic Retrieval",
        "Personal Knowledge Systems",
    ],
    tuple(sorted(("AI", "Business"))): [
        "Decision Intelligence",
        "Workflow Automation",
        "Forecasting Systems",
    ],
    tuple(sorted(("AI", "Mathematics"))): [
        "Optimization Methods",
        "Evaluation Metrics",
        "Statistical Modeling",
    ],
    tuple(sorted(("Agriculture", "Knowledge"))): [
        "Agriculture Knowledge Systems",
        "Action Planning",
        "Field Playbooks",
    ],
    tuple(sorted(("Agriculture", "Business"))): [
        "Farm Operations",
        "Supply Chain Planning",
        "Market Planning",
    ],
    tuple(sorted(("Business", "Knowledge"))): [
        "Decision Frameworks",
        "Knowledge Management",
        "Action Planning",
    ],
}

NOISE_TOKENS = {"add", "button", "click", "focu", "focus", "testing", "test", "topic", "topics"}


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


def _domain_for_topic(context: dict, topic_name: str) -> str:
    return context.get("topic_to_groups", {}).get(topic_name, _topic_group(topic_name))


def _cluster_for_topic(context: dict, topic_name: str) -> str:
    domain = _domain_for_topic(context, topic_name)
    return infer_topic_cluster(topic_name, domain if domain != "Bridge" else "General")


def _passes_filters(context: dict, left: str, right: str, domain: str = "", topic: str = "") -> bool:
    left_group = _domain_for_topic(context, left)
    right_group = _domain_for_topic(context, right)
    if left_group == right_group or "General" in {left_group, right_group}:
        return False
    normalized_domain = canonical_topic_key(domain)
    if normalized_domain:
        if canonical_topic_key(left_group) != normalized_domain and canonical_topic_key(right_group) != normalized_domain:
            return False
    focused_topic = (topic or "").strip()
    if focused_topic:
        focused_domain = _topic_group(focused_topic)
        if focused_topic not in {left, right} and focused_domain not in {left_group, right_group}:
            return False
    return True


def _analyze_graph_clusters(context: dict, domain: str = "", topic: str = "") -> list[dict]:
    pair_scores: Counter[tuple[str, str]] = Counter()
    pair_topics: defaultdict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    pair_clusters: defaultdict[tuple[str, str], Counter[str]] = defaultdict(Counter)

    def register_pair(left: str, right: str, weight: float, source: str) -> None:
        if not _passes_filters(context, left, right, domain=domain, topic=topic):
            return
        left_group = _domain_for_topic(context, left)
        right_group = _domain_for_topic(context, right)
        pair_key = tuple(sorted((left_group, right_group)))
        left_cluster = _cluster_for_topic(context, left)
        right_cluster = _cluster_for_topic(context, right)
        focused_topic = (topic or "").strip()
        source_multiplier = 1.25 if source == "relationship" else 1.0
        focus_multiplier = 1.6 if focused_topic and focused_topic in {left, right} else 1.0
        cross_cluster_bonus = 0.25 if left_cluster != right_cluster else 0.0
        total_weight = weight * source_multiplier * focus_multiplier + cross_cluster_bonus
        pair_scores[pair_key] += total_weight
        pair_topics[pair_key][left] += total_weight
        pair_topics[pair_key][right] += total_weight
        pair_clusters[pair_key][left_cluster] += total_weight
        pair_clusters[pair_key][right_cluster] += total_weight

    for (left, right), weight in context.get("pair_counts", Counter()).items():
        register_pair(left, right, float(weight), "cooccurrence")
    for relationship in context.get("stored_relationships", []):
        register_pair(relationship.source_topic, relationship.target_topic, max(1.0, float(relationship.confidence or 0.0) * 3.0), "relationship")

    ranked: list[dict] = []
    for pair_key, score in pair_scores.most_common(MAX_DOMAIN_PAIRS):
        ranked.append({
            "pair_key": pair_key,
            "score": float(score),
            "topics": [name for name, _ in pair_topics[pair_key].most_common(6)],
            "clusters": [name for name, _ in pair_clusters[pair_key].most_common(4)],
        })
    return ranked


def _cluster_rule_candidates(pair_key: tuple[str, str], clusters: list[str]) -> list[str]:
    cluster_text = " ".join(clusters).lower()
    candidates: list[str] = []
    if pair_key == tuple(sorted(("AI", "Knowledge"))):
        if "retrieval" in cluster_text or "knowledge systems" in cluster_text:
            candidates.extend(["Semantic Retrieval", "Knowledge Graph Construction"])
        if "representation" in cluster_text:
            candidates.append("Embedding Taxonomy")
    if pair_key == tuple(sorted(("AI", "Agriculture"))):
        if "retrieval" in cluster_text or "automation" in cluster_text:
            candidates.extend(["Sensor Monitoring", "Predictive Irrigation"])
        if "ranking" in cluster_text:
            candidates.append("Crop Prioritization")
    if pair_key == tuple(sorted(("AI", "Business"))):
        if "ranking" in cluster_text or "real estate" in cluster_text:
            candidates.extend(["Decision Intelligence", "Opportunity Scoring"])
    if pair_key == tuple(sorted(("Business", "Knowledge"))):
        if "knowledge systems" in cluster_text or "real estate" in cluster_text:
            candidates.extend(["Decision Frameworks", "Operational Playbooks"])
    if pair_key == tuple(sorted(("Agriculture", "Knowledge"))):
        if "agriculture automation" in cluster_text or "knowledge systems" in cluster_text:
            candidates.extend(["Field Playbooks", "Agriculture Knowledge Systems"])
    ordered: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        cleaned_key = canonical_topic_key(candidate)
        if cleaned_key and cleaned_key not in seen:
            seen.add(cleaned_key)
            ordered.append(candidate)
    return ordered


def _rule_bridges(db: Session, user_id: int, context: dict, domain: str = "", topic: str = "", limit: int = 4) -> tuple[list[dict], float, list[dict]]:
    existing_keys = _existing_topic_keys(db, user_id, context)
    ranked_pairs = _analyze_graph_clusters(context, domain=domain, topic=topic)
    suggestions: list[dict] = []
    seen: set[str] = set()
    for ranked_pair in ranked_pairs:
        pair_key = ranked_pair["pair_key"]
        pair_score = ranked_pair["score"]
        context_topics = ranked_pair["topics"]
        clusters = ranked_pair["clusters"]
        candidates = _cluster_rule_candidates(pair_key, clusters) + BRIDGE_RULES.get(pair_key, [])
        for index, candidate in enumerate(candidates):
            cleaned = _clean_bridge_topic(candidate)
            candidate_key = canonical_topic_key(cleaned)
            if not cleaned or not candidate_key or candidate_key in existing_keys or candidate_key in seen:
                continue
            seen.add(candidate_key)
            confidence = max(0.58, min(0.95, 0.61 + pair_score / 14 - index * 0.04))
            cluster_text = ", ".join(clusters[:2]) if clusters else "active clusters"
            suggestions.append({
                "topic": cleaned,
                "domains": list(pair_key),
                "confidence": round(confidence, 2),
                "source": "rules",
                "reason": f"{cleaned} can connect your {pair_key[0]} and {pair_key[1]} knowledge through {cluster_text}.",
                "context_topics": context_topics[:4],
            })
            if len(suggestions) >= limit:
                break
        if len(suggestions) >= limit:
            break
    confidence = 0.86 if len(suggestions) >= MIN_RULE_BRIDGES else 0.68 if suggestions else 0.0
    return suggestions[:limit], confidence, ranked_pairs


def _ai_bridge_suggestions(ranked_pairs: list[dict], existing_keys: set[str], limit: int) -> list[dict]:
    results: list[dict] = []
    seen = set(existing_keys)
    for ranked_pair in ranked_pairs:
        if len(results) >= limit:
            break
        pair_key = ranked_pair["pair_key"]
        context_topics = ranked_pair["topics"]
        clusters = ranked_pair["clusters"]
        prompt = (
            "You are helping expand a personal knowledge graph\n"
            "Return only short bridge topic names that connect the two domains\n"
            "Use 1 to 4 words per line\n"
            "Do not explain\n"
            "Do not return topics already listed\n\n"
            f"Domain A: {pair_key[0]}\n"
            f"Domain B: {pair_key[1]}\n"
            "Active clusters\n"
            + "\n".join(f"- {name}" for name in clusters[:4])
            + "\n\nKnown nearby topics\n"
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
            results.append({
                "topic": cleaned,
                "domains": list(pair_key),
                "confidence": 0.72,
                "source": "ai",
                "reason": f"{cleaned} is a plausible bridge between {pair_key[0]} and {pair_key[1]} based on your current clusters.",
                "context_topics": context_topics[:4],
            })
            if len(results) >= limit:
                break
    return results[:limit]


def _relationship_only_pairs(context: dict, domain: str = "", topic: str = "") -> list[dict]:
    fallback_pairs: Counter[tuple[str, str]] = Counter()
    fallback_topics: defaultdict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for relationship in context.get("stored_relationships", []):
        if not _passes_filters(context, relationship.source_topic, relationship.target_topic, domain=domain, topic=topic):
            continue
        left_group = _domain_for_topic(context, relationship.source_topic)
        right_group = _domain_for_topic(context, relationship.target_topic)
        pair_key = tuple(sorted((left_group, right_group)))
        weight = max(1.0, float(relationship.confidence or 0.0) * 2.0)
        fallback_pairs[pair_key] += weight
        fallback_topics[pair_key][relationship.source_topic] += weight
        fallback_topics[pair_key][relationship.target_topic] += weight
    return [{
        "pair_key": pair_key,
        "score": float(score),
        "topics": [name for name, _ in fallback_topics[pair_key].most_common(6)],
        "clusters": [],
    } for pair_key, score in fallback_pairs.most_common(MAX_DOMAIN_PAIRS)]


def _context_hash(context: dict, domain: str, topic: str) -> str:
    ranked_pairs = _analyze_graph_clusters(context, domain=domain, topic=topic)
    return build_context_hash({
        "domain": domain,
        "topic": topic,
        "pairs": ranked_pairs,
        "topic_names": context.get("topic_names", [])[:30],
        "version": "v2",
    })


def discover_domain_bridges(db: Session, user_id: int, limit: int = 4, domain: str = "", topic: str = "", refresh: bool = False) -> dict:
    context = _build_graph_context(db, user_id)
    graph_version = get_user_graph_version(db, user_id)
    context_hash = _context_hash(context, domain, topic)
    topic_scope = topic or domain or "global"

    if not refresh:
        cached = get_ai_insight(db, user_id, topic_scope, FEATURE_TYPE, context_hash, graph_version)
        if cached and isinstance(cached.get("bridges"), list):
            cached["bridges"] = cached["bridges"][:limit]
            return cached

    rule_results, rule_confidence, ranked_pairs = _rule_bridges(db, user_id, context, domain=domain, topic=topic, limit=limit)
    final_results = list(rule_results)
    if not ranked_pairs:
        ranked_pairs = _relationship_only_pairs(context, domain=domain, topic=topic)

    final_source = "rules"
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
            topic_key = canonical_topic_key(item["topic"])
            if not topic_key or topic_key in existing_final_keys:
                continue
            final_results.append(item)
            existing_final_keys.add(topic_key)
        if rule_results and ai_results:
            final_source = "hybrid"
        elif ai_results:
            final_source = "ai"
        elif not rule_results:
            final_source = "fallback"

    payload = {"bridges": final_results[:limit]}
    return save_ai_insight(
        db,
        user_id=user_id,
        topic_name=topic_scope,
        feature_type=FEATURE_TYPE,
        context_hash=context_hash,
        graph_version=graph_version,
        source=final_source,
        payload=payload,
        ttl_hours=72,
    )
