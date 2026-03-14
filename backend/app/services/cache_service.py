from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.topic_expansion_cache import TopicExpansionCache


DEFAULT_CACHE_HOURS = 24


def build_suggestion_cache_key(topic_name: str, graph_version: int) -> str:
    normalized = (topic_name or '').strip().lower()
    return f"suggestions:{normalized}:{graph_version}"


def load_cached_payload(db: Session, cache_key: str, ttl_hours: int = DEFAULT_CACHE_HOURS) -> dict | None:
    entry = db.scalar(select(TopicExpansionCache).where(TopicExpansionCache.topic_key == cache_key))
    if entry is None or not (entry.suggestions_blob or '').strip():
        return None

    updated_at = entry.updated_at
    if updated_at is not None:
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        if updated_at < datetime.now(timezone.utc) - timedelta(hours=ttl_hours):
            return None

    try:
        return json.loads(entry.suggestions_blob)
    except json.JSONDecodeError:
        return None


def save_cached_payload(db: Session, cache_key: str, topic_name: str, payload: dict) -> None:
    serialized = json.dumps(payload)
    entry = db.scalar(select(TopicExpansionCache).where(TopicExpansionCache.topic_key == cache_key))
    if entry is None:
        entry = TopicExpansionCache(topic_key=cache_key, topic_name=topic_name, suggestions_blob=serialized)
        db.add(entry)
    else:
        entry.topic_name = topic_name
        entry.suggestions_blob = serialized
    db.commit()
