from collections import Counter, defaultdict
import logging
from itertools import combinations
from threading import Lock
from time import monotonic

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.models.content_topic import ContentTopic
from app.models.knowledge import KnowledgeItem
from app.models.topic_relationship import TopicRelationship
from app.models.topic import Topic
from app.schemas.graph import GraphEdge, GraphNode, GraphResponse
from app.services.topic_bridge_service import build_topic_bridges
from app.services.topic_cluster_service import annotate_graph_clusters
from app.services.topic_hierarchy_service import infer_topic_hierarchy, sync_topic_hierarchy_metadata
from app.services.topic_linker import sync_relationships_for_user


logger = logging.getLogger("uvicorn.error")


TOPIC_CATEGORY_MAP = {
    "Embeddings": "AI",
    "Semantic Search": "AI",
    "Vector Databases": "AI",
    "Hybrid Search": "AI",
    "Retrieval Augmented Generation": "AI",
    "Retrieval Optimization": "AI",
    "LLM Systems": "AI",
    "Keyword Search": "AI",
    "Mushroom Farming": "Agriculture",
    "Hydroponic Farming": "Agriculture",
    "Controlled Environment Agriculture": "Agriculture",
    "Spawn Quality": "Agriculture",
    "Substrate Sterilization": "Agriculture",
    "Yield Optimization": "Agriculture",
    "Climate Control": "Agriculture",
    "Vedic Mathematics": "Mathematics",
    "Mathematics": "Mathematics",
    "Knowledge Management": "Knowledge",
    "AI Life Architect": "Knowledge",
    "Travel / Spiritual": "Spiritual",
}
MAX_TOPIC_COUNT = 36
MAX_ITEM_COUNT = 24
BRIDGE_CACHE_TTL_SECONDS = 45
_BRIDGE_CACHE: dict[tuple[int, tuple[str, ...], tuple[tuple[str, int], ...]], tuple[float, dict]] = {}
_BRIDGE_CACHE_LOCK = Lock()

FOCUSED_NEIGHBOR_NOISE_TOKENS = {
    "should",
    "key",
    "matter",
    "matters",
    "overview",
    "intro",
    "introduction",
    "basics",
}


def _topic_group(topic_name: str) -> str:
    if topic_name.startswith("AI in ") or " and " in topic_name:
        return "Bridge"
    if topic_name == "Real Estate" or topic_name.endswith(" Property"):
        return "Business"
    return TOPIC_CATEGORY_MAP.get(topic_name, "General")


def _empty_response(level: int, domain: str | None = None, topic: str | None = None) -> GraphResponse:
    return GraphResponse(nodes=[], edges=[], level=level, domain=domain, topic=topic, available_domains=[])


def _dedupe_titles(values: list[str], limit: int = 12) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        deduped.append(value)
        if len(deduped) >= limit:
            break
    return deduped


def _topic_node(
    topic_name: str,
    topic_counts: Counter[str],
    connection_counts: Counter[str],
    topic_to_titles: dict[str, list[str]],
    *,
    base_scale: float = 1.15,
    max_size: float = 18,
) -> GraphNode:
    importance = round(topic_counts[topic_name] * base_scale + connection_counts[topic_name] * 0.9, 2)
    return GraphNode(
        id=topic_name,
        label=topic_name,
        type="topic",
        group=_topic_group(topic_name),
        size=5 + min(max_size, importance * 1.35),
        importance=importance,
        connection_count=connection_counts[topic_name],
        linked_titles=_dedupe_titles(topic_to_titles.get(topic_name, [])),
        linked_count=topic_counts[topic_name],
    )


def _stored_relationships(db: Session, user_id: int) -> list[TopicRelationship]:
    return db.scalars(
        select(TopicRelationship).where(TopicRelationship.user_id == user_id)
    ).all()


def _relationship_lookup(relationships: list[TopicRelationship]) -> dict[tuple[str, str], TopicRelationship]:
    lookup: dict[tuple[str, str], TopicRelationship] = {}
    for relationship in relationships:
        key = tuple(sorted((relationship.source_topic, relationship.target_topic)))
        current = lookup.get(key)
        if current is None or relationship.confidence > current.confidence:
            lookup[key] = relationship
    return lookup


def _cooccurrence_edge(source: str, target: str, weight: float, relationship_lookup: dict[tuple[str, str], TopicRelationship]) -> GraphEdge:
    relationship = relationship_lookup.get(tuple(sorted((source, target))))
    if relationship is not None:
        return GraphEdge(
            source=source,
            target=target,
            type=relationship.relationship_type,
            weight=relationship.confidence,
            relationship_id=relationship.id,
            confidence=relationship.confidence,
        )
    return GraphEdge(source=source, target=target, type="topic_link", weight=float(weight))


def _build_graph_context(db: Session, user_id: int) -> dict:
    items = db.scalars(
        select(KnowledgeItem)
        .options(selectinload(KnowledgeItem.content_topics).selectinload(ContentTopic.topic))
        .where(KnowledgeItem.user_id == user_id)
        .order_by(desc(KnowledgeItem.updated_at))
        .limit(160)
    ).all()
    relationships = _stored_relationships(db, user_id)
    if not items:
        return {
            "items": [],
            "topic_counts": Counter(),
            "pair_counts": Counter(),
            "topic_to_titles": defaultdict(list),
            "topic_to_items": defaultdict(list),
            "topic_names": [],
            "topic_metadata": {},
            "available_domains": [],
            "topic_to_groups": {},
            "stored_relationships": relationships,
        "relationship_lookup": _relationship_lookup(relationships),
        }

    topic_counts: Counter[str] = Counter()
    pair_counts: Counter[tuple[str, str]] = Counter()
    topic_to_titles: dict[str, list[str]] = defaultdict(list)
    topic_to_items: dict[str, list[KnowledgeItem]] = defaultdict(list)
    recent_topic_names: list[str] = []

    for item in items:
        topic_names = sorted(
            {
                content_topic.topic.name
                for content_topic in item.content_topics
                if content_topic.topic is not None and content_topic.topic.name
            }
        )
        if not topic_names:
            continue

        for topic_name in topic_names:
            topic_counts[topic_name] += 1
            topic_to_titles[topic_name].append(item.title)
            topic_to_items[topic_name].append(item)
            if topic_name not in recent_topic_names:
                recent_topic_names.append(topic_name)

        for left, right in combinations(topic_names, 2):
            pair_counts[(left, right)] += 1

    for relationship in relationships:
        topic_counts[relationship.source_topic] += 0
        topic_counts[relationship.target_topic] += 0
        if relationship.source_topic not in recent_topic_names:
            recent_topic_names.append(relationship.source_topic)
        if relationship.target_topic not in recent_topic_names:
            recent_topic_names.append(relationship.target_topic)

    top_topic_names = [topic_name for topic_name, _ in topic_counts.most_common(MAX_TOPIC_COUNT)]
    for topic_name in recent_topic_names:
        if topic_name in top_topic_names:
            continue
        top_topic_names.append(topic_name)
        if len(top_topic_names) >= MAX_TOPIC_COUNT:
            break

    top_topic_names = [topic_name for topic_name in top_topic_names if _topic_group(topic_name) != "Bridge"]
    topic_metadata = sync_topic_hierarchy_metadata(db, user_id, top_topic_names)
    topic_to_groups = {topic_name: _topic_group(topic_name) for topic_name in top_topic_names}
    available_domains = sorted({group for group in topic_to_groups.values() if group != "Bridge"})

    return {
        "items": items,
        "topic_counts": topic_counts,
        "pair_counts": pair_counts,
        "topic_to_titles": topic_to_titles,
        "topic_to_items": topic_to_items,
        "topic_names": top_topic_names,
        "topic_metadata": topic_metadata,
        "available_domains": available_domains,
        "topic_to_groups": topic_to_groups,
        "stored_relationships": relationships,
        "relationship_lookup": _relationship_lookup(relationships),
    }


def _build_bridge_context(db: Session, user_id: int, context: dict) -> dict:
    topic_names = tuple(context["topic_names"])
    topic_signature = tuple(
        (topic_name, len(context["topic_to_titles"].get(topic_name, [])))
        for topic_name in topic_names
    )
    cache_key = (user_id, topic_names, topic_signature)
    now = monotonic()

    with _BRIDGE_CACHE_LOCK:
        cached = _BRIDGE_CACHE.get(cache_key)
        if cached and now - cached[0] <= BRIDGE_CACHE_TTL_SECONDS:
            return cached[1]

    bridge_nodes, bridge_edges = build_topic_bridges(
        db,
        user_id,
        list(topic_names),
        {topic_name: context["topic_to_titles"][topic_name] for topic_name in topic_names},
        _topic_group,
    )
    bridge_context = {
        "bridge_nodes": bridge_nodes,
        "bridge_edges": bridge_edges,
        "bridge_lookup": {node.label: node for node in bridge_nodes},
    }

    with _BRIDGE_CACHE_LOCK:
        stale_keys = [
            key for key, value in _BRIDGE_CACHE.items()
            if now - value[0] > BRIDGE_CACHE_TTL_SECONDS
        ]
        for key in stale_keys:
            _BRIDGE_CACHE.pop(key, None)
        _BRIDGE_CACHE[cache_key] = (now, bridge_context)

    return bridge_context


def _relationship_edges(context: dict, selected_topics: set[str]) -> list[GraphEdge]:
    edges: list[GraphEdge] = []
    for relationship in context["stored_relationships"]:
        if relationship.source_topic not in selected_topics or relationship.target_topic not in selected_topics:
            continue
        edges.append(
            GraphEdge(
                source=relationship.source_topic,
                target=relationship.target_topic,
                type=relationship.relationship_type,
                weight=relationship.confidence,
                relationship_id=relationship.id,
                confidence=relationship.confidence,
            )
        )
    return edges


def _is_noisy_focused_neighbor(topic_name: str, center_topic: str) -> bool:
    words = {word.lower() for word in topic_name.split() if word}
    center_words = {word.lower() for word in center_topic.split() if word}
    if not words:
        return True
    if len(words) <= 2 and words & FOCUSED_NEIGHBOR_NOISE_TOKENS:
        return True
    if words & FOCUSED_NEIGHBOR_NOISE_TOKENS and words & center_words:
        return True
    return False


def _focused_neighbor_score(topic_name: str, center_topic: str, context: dict) -> float:
    if topic_name == center_topic:
        return 10_000.0

    topic_counts: Counter[str] = context["topic_counts"]
    relationship_lookup: dict[tuple[str, str], TopicRelationship] = context["relationship_lookup"]
    pair_counts: Counter[tuple[str, str]] = context["pair_counts"]

    relationship = relationship_lookup.get(tuple(sorted((topic_name, center_topic))))
    pair_weight = pair_counts.get((topic_name, center_topic), 0) + pair_counts.get((center_topic, topic_name), 0)
    topic_count = topic_counts.get(topic_name, 0)
    group = _topic_group(topic_name)

    score = topic_count * 2.0 + pair_weight * 1.6
    if relationship is not None:
        score += relationship.confidence * 12
    if group != "General":
        score += 1.5
    if topic_count <= 1 and group == "General":
        score -= 4.5
    if len(topic_name.split()) > 3:
        score -= 3
    return score


def _should_include_focused_neighbor(topic_name: str, center_topic: str, context: dict) -> bool:
    if topic_name == center_topic:
        return True

    topic_counts: Counter[str] = context["topic_counts"]
    relationship_lookup: dict[tuple[str, str], TopicRelationship] = context["relationship_lookup"]
    pair_counts: Counter[tuple[str, str]] = context["pair_counts"]

    relationship = relationship_lookup.get(tuple(sorted((topic_name, center_topic))))
    pair_weight = pair_counts.get((topic_name, center_topic), 0) + pair_counts.get((center_topic, topic_name), 0)
    topic_count = topic_counts.get(topic_name, 0)
    group = _topic_group(topic_name)
    words = topic_name.split()

    if _is_noisy_focused_neighbor(topic_name, center_topic):
        return False
    if relationship is not None and relationship.confidence >= 0.7:
        return True
    if topic_count >= 2 and pair_weight >= 1 and group != "General":
        return True
    if pair_weight >= 2 and group != "General":
        return True
    if group != "General" and topic_count >= 2:
        return True

    if group == "General":
        return False
    if len(words) > 3:
        return False
    return topic_count >= 2 or pair_weight >= 2


def _domain_edges(pair_counts: Counter[tuple[str, str]], topic_to_groups: dict[str, str]) -> tuple[list[GraphEdge], Counter[str]]:
    domain_pair_counts: Counter[tuple[str, str]] = Counter()
    for (source, target), weight in pair_counts.items():
        source_group = topic_to_groups.get(source)
        target_group = topic_to_groups.get(target)
        if not source_group or not target_group or source_group == target_group:
            continue
        pair = tuple(sorted((source_group, target_group)))
        domain_pair_counts[pair] += weight

    edges = [
        GraphEdge(source=source, target=target, type="domain_link", weight=float(weight))
        for (source, target), weight in domain_pair_counts.most_common(18)
    ]
    connection_counts: Counter[str] = Counter()
    for edge in edges:
        connection_counts[edge.source] += 1
        connection_counts[edge.target] += 1
    return edges, connection_counts


def _build_level_one(context: dict) -> GraphResponse:
    topic_counts: Counter[str] = context["topic_counts"]
    topic_to_groups: dict[str, str] = context["topic_to_groups"]
    available_domains: list[str] = context["available_domains"]
    if not topic_counts or not available_domains:
        return _empty_response(1)

    domain_topic_counts: Counter[str] = Counter()
    domain_titles: dict[str, list[str]] = defaultdict(list)
    for topic_name, count in topic_counts.items():
        group = topic_to_groups.get(topic_name)
        if not group or group == "Bridge":
            continue
        domain_topic_counts[group] += count
        domain_titles[group].append(topic_name)

    edges, connection_counts = _domain_edges(context["pair_counts"], topic_to_groups)
    nodes = []
    for domain in available_domains:
        topic_names = sorted(domain_titles.get(domain, []), key=lambda name: (-topic_counts[name], name))
        importance = round(domain_topic_counts[domain] * 1.6 + connection_counts[domain], 2)
        nodes.append(
            GraphNode(
                id=domain,
                label=domain,
                type="domain",
                group=domain,
                size=18 + min(26, importance * 1.4),
                importance=importance,
                connection_count=connection_counts[domain],
                linked_titles=topic_names[:10],
                linked_count=domain_topic_counts[domain],
                related_titles=topic_names[:6],
            )
        )

    return GraphResponse(nodes=nodes, edges=edges, level=1, available_domains=available_domains)


def _build_level_two(context: dict, domain: str | None) -> GraphResponse:
    available_domains: list[str] = context["available_domains"]
    if not domain or domain not in available_domains:
        return _build_level_one(context)

    topic_counts: Counter[str] = context["topic_counts"]
    topic_to_titles: dict[str, list[str]] = context["topic_to_titles"]
    topic_metadata: dict[str, dict[str, int | str | None]] = context["topic_metadata"]
    topic_to_groups: dict[str, str] = context["topic_to_groups"]

    domain_topics = [
        topic_name
        for topic_name in context["topic_names"]
        if topic_to_groups.get(topic_name) == domain and (topic_metadata.get(topic_name, {}).get("level") or 2) <= 2
    ]
    if not domain_topics:
        domain_topics = [topic_name for topic_name in context["topic_names"] if topic_to_groups.get(topic_name) == domain]
    if not domain_topics:
        return GraphResponse(nodes=[], edges=[], level=2, domain=domain, available_domains=available_domains)

    selected_topics = set(domain_topics)
    edges = [
        _cooccurrence_edge(source, target, float(weight), context["relationship_lookup"])
        for (source, target), weight in context["pair_counts"].most_common(40)
        if source in selected_topics and target in selected_topics
    ]
    edges.extend(_relationship_edges(context, selected_topics))
    connection_counts: Counter[str] = Counter()
    for edge in edges:
        connection_counts[edge.source] += 1
        connection_counts[edge.target] += 1

    nodes = [
        _topic_node(topic_name, topic_counts, connection_counts, topic_to_titles, base_scale=0.95, max_size=14)
        for topic_name in sorted(domain_topics, key=lambda name: (-topic_counts[name], name))
    ]
    return GraphResponse(nodes=nodes, edges=edges, level=2, domain=domain, available_domains=available_domains)


def _build_level_three(context: dict, bridge_context: dict, domain: str | None, topic: str | None) -> GraphResponse:
    available_domains: list[str] = context["available_domains"]
    if not topic or topic not in context["topic_counts"]:
        return _build_level_two(context, domain)

    topic_counts: Counter[str] = context["topic_counts"]
    topic_to_titles: dict[str, list[str]] = context["topic_to_titles"]
    topic_metadata: dict[str, dict[str, int | str | None]] = context["topic_metadata"]
    topic_to_groups: dict[str, str] = context["topic_to_groups"]

    neighbor_topics: set[str] = {topic}
    for (source, target), weight in context["pair_counts"].most_common(120):
        if weight < 1:
            continue
        if source == topic:
            neighbor_topics.add(target)
        elif target == topic:
            neighbor_topics.add(source)
        if len(neighbor_topics) >= 9:
            break

    for relationship in context["stored_relationships"]:
        if relationship.source_topic == topic:
            neighbor_topics.add(relationship.target_topic)
        elif relationship.target_topic == topic:
            neighbor_topics.add(relationship.source_topic)

    parent_name = topic_metadata.get(topic, {}).get("parent_name")
    if isinstance(parent_name, str):
        neighbor_topics.add(parent_name)
    child_parent_map = infer_topic_hierarchy(context["topic_names"])
    for child_name, child_parent_name in child_parent_map.items():
        if child_parent_name == topic:
            neighbor_topics.add(child_name)

    bridge_nodes = []
    bridge_edges = []
    for node in bridge_context["bridge_nodes"]:
        related = set(node.related_titles or [])
        if topic in related:
            bridge_nodes.append(node)
    bridge_node_ids = {node.id for node in bridge_nodes}
    for edge in bridge_context["bridge_edges"]:
        source_id = edge.source
        target_id = edge.target
        if source_id in bridge_node_ids or target_id in bridge_node_ids:
            bridge_edges.append(edge)
            if source_id != topic and source_id not in bridge_node_ids:
                neighbor_topics.add(source_id)
            if target_id != topic and target_id not in bridge_node_ids:
                neighbor_topics.add(target_id)

    scored_neighbors = sorted(
        (
            name for name in neighbor_topics
            if name in topic_counts and _should_include_focused_neighbor(name, topic, context)
        ),
        key=lambda name: _focused_neighbor_score(name, topic, context),
        reverse=True,
    )
    prioritized_topics: list[str] = []
    for name in scored_neighbors:
        if name == topic:
            prioritized_topics.append(name)
            continue
        if len(prioritized_topics) >= 8:
            continue
        prioritized_topics.append(name)

    selected_topics = set(prioritized_topics)
    edges = []
    for (source, target), weight in context["pair_counts"].most_common(80):
        if source in selected_topics and target in selected_topics:
            edges.append(_cooccurrence_edge(source, target, float(weight), context["relationship_lookup"]))

    edges.extend(_relationship_edges(context, selected_topics))
    child_counts: Counter[str] = Counter()
    for edge in edges + bridge_edges:
        child_counts[edge.source] += 1
        child_counts[edge.target] += 1

    for child_name, child_parent_name in child_parent_map.items():
        if child_name in selected_topics and child_parent_name in selected_topics:
            edges.append(
                GraphEdge(
                    source=child_parent_name,
                    target=child_name,
                    type="topic_parent_relationship",
                    weight=1.4,
                )
            )
            child_counts[child_parent_name] += 1
            child_counts[child_name] += 1

    edges.extend(bridge_edges)
    nodes = [
        _topic_node(topic_name, topic_counts, child_counts, topic_to_titles, base_scale=1.05, max_size=16)
        for topic_name in sorted(selected_topics, key=lambda name: (name != topic, -topic_counts[name], name))
    ]

    for node in bridge_nodes:
        connection_count = child_counts[node.id]
        nodes.append(
            GraphNode(
                **{
                    **node.model_dump(),
                    "size": 5 + min(24, (node.importance + connection_count) * 1.8),
                    "importance": round(node.importance + connection_count, 2),
                    "connection_count": connection_count,
                }
            )
        )

    response = GraphResponse(nodes=nodes, edges=edges, level=3, domain=domain or topic_to_groups.get(topic), topic=topic, available_domains=available_domains)
    return annotate_graph_clusters(response, center_topic=topic)


def _build_level_four(context: dict, bridge_context: dict | None, domain: str | None, topic: str | None) -> GraphResponse:
    available_domains: list[str] = context["available_domains"]
    if not topic:
        return _build_level_two(context, domain)

    resolved_domain = domain or context["topic_to_groups"].get(topic)
    topic_to_items: dict[str, list[KnowledgeItem]] = context["topic_to_items"]
    topic_to_titles: dict[str, list[str]] = context["topic_to_titles"]
    topic_counts: Counter[str] = context["topic_counts"]
    bridge_lookup: dict[str, GraphNode] = (bridge_context or {}).get("bridge_lookup", {})

    root_node: GraphNode | None = None
    root_edges: list[GraphEdge] = []
    candidate_items: list[KnowledgeItem] = []

    if topic in topic_counts:
        root_node = GraphNode(
            id=topic,
            label=topic,
            type="topic",
            group=context["topic_to_groups"].get(topic, "General"),
            size=18,
            importance=10,
            connection_count=0,
            linked_titles=_dedupe_titles(topic_to_titles.get(topic, [])),
            linked_count=topic_counts[topic],
        )
        candidate_items = topic_to_items.get(topic, [])[:MAX_ITEM_COUNT]
    elif topic in bridge_lookup:
        bridge_node = bridge_lookup[topic]
        root_node = GraphNode(
            **{
                **bridge_node.model_dump(),
                "size": 18,
                "importance": max(bridge_node.importance, 10),
            }
        )
        related_topics = [name for name in bridge_node.related_titles if name in topic_to_items]
        seen_ids: set[int] = set()
        for related_topic in related_topics:
            for item in topic_to_items.get(related_topic, []):
                if item.id in seen_ids:
                    continue
                seen_ids.add(item.id)
                candidate_items.append(item)
                if len(candidate_items) >= MAX_ITEM_COUNT:
                    break
            if len(candidate_items) >= MAX_ITEM_COUNT:
                break
    else:
        if bridge_context is None:
            return _build_level_two(context, resolved_domain)
        return _build_level_three(context, bridge_context, resolved_domain, topic)

    item_nodes: list[GraphNode] = []
    for item in candidate_items[:MAX_ITEM_COUNT]:
        topics = sorted(
            {
                content_topic.topic.name
                for content_topic in item.content_topics
                if content_topic.topic is not None and content_topic.topic.name
            }
        )
        item_nodes.append(
            GraphNode(
                id=f"knowledge-{item.id}",
                label=item.title,
                type="knowledge",
                group=resolved_domain or root_node.group,
                size=8,
                importance=4,
                connection_count=1,
                summary=(item.summary or item.content[:180]).strip() if item.content else item.summary,
                content_type=item.type,
                tags=[tag.strip() for tag in (item.tags or "").split(",") if tag.strip()],
                topics=topics,
                linked_titles=topics[:8],
                linked_count=len(topics),
            )
        )
        root_edges.append(
            GraphEdge(
                source=root_node.id,
                target=f"knowledge-{item.id}",
                type="knowledge_item_link",
                weight=1.2,
            )
        )

    if root_node is None:
        return GraphResponse(nodes=[], edges=[], level=4, domain=resolved_domain, topic=topic, available_domains=available_domains)

    root_node.connection_count = len(root_edges)
    root_node.size = 12 + min(18, max(root_node.importance, len(root_edges)) * 1.3)
    return GraphResponse(
        nodes=[root_node, *item_nodes],
        edges=root_edges,
        level=4,
        domain=resolved_domain,
        topic=topic,
        available_domains=available_domains,
    )


def build_brain_map_for_user(db: Session, user_id: int, level: int = 1, domain: str | None = None, topic: str | None = None) -> GraphResponse:
    request_started = monotonic()
    context_started = monotonic()
    context = _build_graph_context(db, user_id)
    context_elapsed_ms = round((monotonic() - context_started) * 1000, 1)

    if not context["items"] and not context["stored_relationships"]:
        logger.info(
            "brain_map level=%s domain=%s topic=%s context_ms=%s total_ms=%s empty=1",
            level,
            domain,
            topic,
            context_elapsed_ms,
            round((monotonic() - request_started) * 1000, 1),
        )
        return _empty_response(level, domain, topic)

    bridge_elapsed_ms = 0.0
    builder_started = monotonic()

    if level <= 1:
        response = _build_level_one(context)
    elif level == 2:
        response = _build_level_two(context, domain)
    elif level == 3:
        bridge_started = monotonic()
        bridge_context = _build_bridge_context(db, user_id, context)
        bridge_elapsed_ms = round((monotonic() - bridge_started) * 1000, 1)
        builder_started = monotonic()
        response = _build_level_three(context, bridge_context, domain, topic)
    else:
        bridge_context = None
        if topic and topic not in context["topic_counts"]:
            bridge_started = monotonic()
            bridge_context = _build_bridge_context(db, user_id, context)
            bridge_elapsed_ms = round((monotonic() - bridge_started) * 1000, 1)
        builder_started = monotonic()
        response = _build_level_four(context, bridge_context, domain, topic)

    builder_elapsed_ms = round((monotonic() - builder_started) * 1000, 1)
    total_elapsed_ms = round((monotonic() - request_started) * 1000, 1)
    logger.info(
        "brain_map level=%s domain=%s topic=%s context_ms=%s bridge_ms=%s build_ms=%s total_ms=%s nodes=%s edges=%s",
        level,
        domain,
        topic,
        context_elapsed_ms,
        bridge_elapsed_ms,
        builder_elapsed_ms,
        total_elapsed_ms,
        len(response.nodes),
        len(response.edges),
    )
    return response


def build_topic_graph_for_user(db: Session, user_id: int, topic_id: int) -> GraphResponse:
    topic = db.scalar(
        select(Topic).where(Topic.id == topic_id, Topic.user_id == user_id)
    )
    if topic is None:
        raise ValueError("Topic not found")

    sync_relationships_for_user(db, user_id)

    return build_brain_map_for_user(
        db,
        user_id,
        level=3,
        domain=_topic_group(topic.name),
        topic=topic.name,
    )

