from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.content_topic import ContentTopic
from app.models.knowledge import KnowledgeItem
from app.services.connection_service import rebuild_connections_for_user
from app.services.embeddings import sync_knowledge_embedding
from app.services.knowledge_gap_service import get_next_learning_topics
from app.services.learning_path_service import build_learning_paths
from app.services.summarizer import build_summary_and_tags
from app.services.topic_service import assign_topics_to_item, preview_topics_for_item


def load_knowledge_item_with_relations(db: Session, item_id: int) -> KnowledgeItem | None:
    return db.scalar(
        select(KnowledgeItem)
        .options(
            selectinload(KnowledgeItem.content_topics).selectinload(ContentTopic.topic),
            selectinload(KnowledgeItem.outgoing_connections),
        )
        .where(KnowledgeItem.id == item_id)
    )


def _path_snapshot(paths: list[dict]) -> dict[str, dict]:
    return {path["path_name"]: path for path in paths}


def _path_topic_names(path: dict) -> set[str]:
    return {topic["topic"] for topic in path.get("topics", [])}


def _build_learning_path_impacts(before_paths: list[dict], after_paths: list[dict], normalized_topics: list[str]) -> list[dict]:
    before_map = _path_snapshot(before_paths)
    normalized_set = {topic.lower() for topic in normalized_topics}
    impacts: list[dict] = []

    for after_path in after_paths:
        path_topic_names = {topic.lower() for topic in _path_topic_names(after_path)}
        touches_path = bool(path_topic_names & normalized_set)
        before_path = before_map.get(after_path["path_name"])
        before_progress = before_path["progress_percent"] if before_path else 0
        before_covered = before_path["covered_count"] if before_path else 0
        after_progress = after_path["progress_percent"]
        after_covered = after_path["covered_count"]

        if not touches_path or (before_progress == after_progress and before_covered == after_covered):
            continue

        impacts.append(
            {
                "path_name": after_path["path_name"],
                "progress_before": before_progress,
                "progress_after": after_progress,
                "covered_before": before_covered,
                "covered_after": after_covered,
                "total_count": after_path["total_count"],
            }
        )

    return impacts


def _build_ingestion_summary(
    db: Session,
    *,
    item: KnowledgeItem,
    preview: dict[str, list[str]],
    after_paths: list[dict],
    before_paths: list[dict],
    graph_updated: bool,
) -> dict:
    normalized_topics = [
        content_topic.topic.name
        for content_topic in item.content_topics
        if content_topic.topic is not None and content_topic.topic.name
    ]
    suggested_next_topics = [topic["topic"] for topic in get_next_learning_topics(db, item.user_id, limit=3)]

    return {
        "item_id": item.id,
        "title": item.title,
        "extracted_topics": preview.get("extracted_topics", []),
        "normalized_topics": normalized_topics or preview.get("normalized_topics", []),
        "graph_updated": graph_updated,
        "learning_paths_affected": _build_learning_path_impacts(before_paths, after_paths, normalized_topics or preview.get("normalized_topics", [])),
        "suggested_next_topics": suggested_next_topics,
    }


def _apply_item_content(
    item: KnowledgeItem,
    *,
    item_type: str,
    title: str,
    content: str,
    source_url: str | None,
    tags: list[str] | None,
    file_name: str | None,
) -> None:
    summary, generated_tags = build_summary_and_tags(title, content)
    item.type = item_type
    item.title = title
    item.content = content
    item.summary = summary
    item.tags = ",".join(tags or generated_tags)
    item.source_url = source_url
    item.file_name = file_name


def finalize_ingested_item(
    db: Session,
    item: KnowledgeItem,
    *,
    before_paths: list[dict],
    skip_topic_generation: bool = False,
    preview: dict[str, list[str]] | None = None,
) -> tuple[KnowledgeItem, dict]:
    if preview is None:
        preview = preview_topics_for_item(item)

    sync_knowledge_embedding(db, item)
    if not skip_topic_generation:
        assign_topics_to_item(db, item)
    rebuild_connections_for_user(db, item.user_id)

    loaded_item = load_knowledge_item_with_relations(db, item.id)
    after_paths = build_learning_paths(db, item.user_id)
    summary = _build_ingestion_summary(
        db,
        item=loaded_item,
        preview=preview,
        after_paths=after_paths,
        before_paths=before_paths,
        graph_updated=not skip_topic_generation and bool(loaded_item.content_topics),
    )
    return loaded_item, summary


def create_ingested_knowledge_item(
    db: Session,
    *,
    user_id: int,
    item_type: str,
    title: str,
    content: str,
    source_url: str | None = None,
    tags: list[str] | None = None,
    file_name: str | None = None,
    skip_topic_generation: bool = False,
) -> tuple[KnowledgeItem, dict]:
    before_paths = build_learning_paths(db, user_id)
    preview_source = KnowledgeItem(
        id=-1,
        user_id=user_id,
        type=item_type,
        title=title,
        content=content,
        summary=build_summary_and_tags(title, content)[0],
        tags=",".join(tags or []),
        source_url=source_url,
        file_name=file_name,
    )
    preview = preview_topics_for_item(preview_source) if not skip_topic_generation else {"extracted_topics": [], "normalized_topics": []}

    item = KnowledgeItem(user_id=user_id)
    _apply_item_content(
        item,
        item_type=item_type,
        title=title,
        content=content,
        source_url=source_url,
        tags=tags,
        file_name=file_name,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return finalize_ingested_item(db, item, before_paths=before_paths, skip_topic_generation=skip_topic_generation, preview=preview)


def update_ingested_knowledge_item(
    db: Session,
    item: KnowledgeItem,
    *,
    item_type: str,
    title: str,
    content: str,
    source_url: str | None = None,
    tags: list[str] | None = None,
    file_name: str | None = None,
    skip_topic_generation: bool = False,
) -> tuple[KnowledgeItem, dict]:
    before_paths = build_learning_paths(db, item.user_id)
    preview_source = KnowledgeItem(
        id=item.id,
        user_id=item.user_id,
        type=item_type,
        title=title,
        content=content,
        summary=build_summary_and_tags(title, content)[0],
        tags=",".join(tags or []),
        source_url=source_url,
        file_name=file_name,
    )
    preview = preview_topics_for_item(preview_source) if not skip_topic_generation else {"extracted_topics": [], "normalized_topics": []}

    _apply_item_content(
        item,
        item_type=item_type,
        title=title,
        content=content,
        source_url=source_url,
        tags=tags,
        file_name=file_name,
    )
    db.commit()
    db.refresh(item)
    return finalize_ingested_item(db, item, before_paths=before_paths, skip_topic_generation=skip_topic_generation, preview=preview)
