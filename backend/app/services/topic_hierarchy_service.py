from collections import Counter, defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.topic import Topic
from app.schemas.graph import GraphEdge, GraphNode


PROPERTY_SUFFIX = "Property"
REAL_ESTATE_PARENT = "Real Estate"
PROPERTY_DOMAIN_TOKENS = {
    "agricultural",
    "apartment",
    "commercial",
    "estate",
    "farm",
    "land",
    "plot",
    "property",
    "residential",
    "site",
    "villa",
}


def _is_property_topic(topic_name: str) -> bool:
    normalized = topic_name.lower()
    return normalized.endswith(" property") or any(token in normalized.split() for token in PROPERTY_DOMAIN_TOKENS)


def _property_location_tokens(topic_name: str) -> list[str]:
    tokens = topic_name.split()
    if tokens and tokens[-1].lower() == "property":
        tokens = tokens[:-1]
    return [token for token in tokens if token.lower() not in PROPERTY_DOMAIN_TOKENS]


def infer_topic_hierarchy(topic_names: list[str]) -> dict[str, str]:
    parent_map: dict[str, str] = {}
    property_topics = [name for name in topic_names if _is_property_topic(name)]

    locality_parents: dict[str, Counter[str]] = defaultdict(Counter)
    for topic_name in property_topics:
        location_tokens = _property_location_tokens(topic_name)
        if len(location_tokens) < 2:
            continue
        child_token = location_tokens[-1]
        parent_token = location_tokens[0]
        locality_parents[child_token][f"{parent_token} {PROPERTY_SUFFIX}"] += 1

    for topic_name in property_topics:
        location_tokens = _property_location_tokens(topic_name)
        lowered_name = topic_name.lower()

        if "commercial" in lowered_name or "agricultural" in lowered_name:
            parent_map[topic_name] = REAL_ESTATE_PARENT
            continue

        if len(location_tokens) >= 2:
            parent_map[topic_name] = f"{location_tokens[0]} {PROPERTY_SUFFIX}"
            continue

        if len(location_tokens) == 1:
            inferred_parent = locality_parents.get(location_tokens[0])
            if inferred_parent:
                parent_map[topic_name] = inferred_parent.most_common(1)[0][0]
                continue
            parent_map[topic_name] = REAL_ESTATE_PARENT

    return parent_map


def sync_topic_hierarchy_metadata(db: Session, user_id: int, topic_names: list[str]) -> dict[str, dict[str, int | str | None]]:
    if not topic_names:
        return {}

    topics = db.scalars(
        select(Topic).where(Topic.user_id == user_id, Topic.name.in_(topic_names))
    ).all()
    topics_by_name = {topic.name: topic for topic in topics}
    parent_name_map = infer_topic_hierarchy(topic_names)
    metadata: dict[str, dict[str, int | str | None]] = {}
    changed = False

    for topic in topics:
        if topic.type == "bridge":
            desired_parent_id = None
            desired_level = 3
            parent_name = None
        else:
            parent_name = parent_name_map.get(topic.name)
            parent_topic = topics_by_name.get(parent_name) if parent_name else None
            desired_parent_id = parent_topic.id if parent_topic and parent_topic.id != topic.id else None
            desired_level = 3 if desired_parent_id is not None else 2

        if topic.parent_topic_id != desired_parent_id:
            topic.parent_topic_id = desired_parent_id
            changed = True
        if topic.level != desired_level:
            topic.level = desired_level
            changed = True

        metadata[topic.name] = {
            "id": topic.id,
            "parent_name": parent_name,
            "parent_topic_id": desired_parent_id,
            "level": desired_level,
            "type": topic.type,
        }

    if changed:
        db.commit()

    return metadata


def build_hierarchy_graph(
    topic_counts: Counter[str],
    topic_to_titles: dict[str, list[str]],
    topic_group_getter,
) -> tuple[list[GraphNode], list[GraphEdge]]:
    topic_names = list(topic_counts.keys())
    parent_map = infer_topic_hierarchy(topic_names)
    if not parent_map:
        return [], []

    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    created_nodes: set[str] = set(topic_names)
    child_counts: Counter[str] = Counter(parent_map.values())

    for child_name, parent_name in parent_map.items():
        if parent_name not in created_nodes:
            linked_titles = topic_to_titles.get(parent_name, [])
            nodes.append(
                GraphNode(
                    id=parent_name,
                    label=parent_name,
                    type="topic",
                    group=topic_group_getter(parent_name),
                    size=12 + min(12, child_counts[parent_name] * 2.0),
                    linked_titles=linked_titles[:12],
                    linked_count=max(len(linked_titles), child_counts[parent_name]),
                )
            )
            created_nodes.add(parent_name)

        edges.append(
            GraphEdge(
                source=parent_name,
                target=child_name,
                type="topic_parent_relationship",
                weight=1.0 + max(0, child_counts[parent_name] - 1) * 0.4,
            )
        )

    return nodes, edges
