from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from hashlib import sha256

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.ai_topic_insight import AITopicInsight
from app.services.topic_normalizer_service import canonical_topic_key

DEFAULT_TTL_HOURS = 72


def _normalized_topic_name(topic_name: str) -> str:
    normalized = canonical_topic_key(topic_name or "")
    return normalized or "global"


def build_context_hash(payload: dict | list | str | int | float | None) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(serialized.encode("utf-8")).hexdigest()


def get_ai_insight(
    db: Session,
    user_id: int,
    topic_name: str,
    feature_type: str,
    context_hash: str,
    graph_version: int,
) -> dict | None:
    insight = db.scalar(
        select(AITopicInsight)
        .where(
            AITopicInsight.user_id == user_id,
            AITopicInsight.topic_name == _normalized_topic_name(topic_name),
            AITopicInsight.feature_type == feature_type,
            AITopicInsight.context_hash == context_hash,
            AITopicInsight.graph_version == graph_version,
        )
        .order_by(AITopicInsight.updated_at.desc())
    )
    if insight is None:
        return None

    if insight.expires_at is not None:
        expires_at = insight.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= datetime.now(timezone.utc):
            return None

    try:
        payload = json.loads(insight.payload_json)
    except json.JSONDecodeError:
        return None

    if not isinstance(payload, dict):
        return None

    payload["cached"] = True
    payload["source"] = "cache"
    payload["stored_source"] = insight.source
    payload["feature_type"] = feature_type
    payload["graph_version"] = graph_version
    return payload


def save_ai_insight(
    db: Session,
    *,
    user_id: int,
    topic_name: str,
    feature_type: str,
    context_hash: str,
    graph_version: int,
    source: str,
    payload: dict,
    ttl_hours: int | None = DEFAULT_TTL_HOURS,
) -> dict:
    expires_at = None
    if ttl_hours is not None:
        expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)

    serialized = json.dumps(payload, sort_keys=True)
    normalized_topic = _normalized_topic_name(topic_name)
    insight = db.scalar(
        select(AITopicInsight).where(
            AITopicInsight.user_id == user_id,
            AITopicInsight.topic_name == normalized_topic,
            AITopicInsight.feature_type == feature_type,
            AITopicInsight.context_hash == context_hash,
            AITopicInsight.graph_version == graph_version,
        )
    )
    if insight is None:
        insight = AITopicInsight(
            user_id=user_id,
            topic_name=normalized_topic,
            feature_type=feature_type,
            context_hash=context_hash,
            graph_version=graph_version,
            source=source,
            payload_json=serialized,
            expires_at=expires_at,
        )
        db.add(insight)
    else:
        insight.source = source
        insight.payload_json = serialized
        insight.expires_at = expires_at

    db.commit()
    result = dict(payload)
    result["cached"] = False
    result["source"] = source
    result["stored_source"] = source
    result["feature_type"] = feature_type
    result["graph_version"] = graph_version
    return result


def invalidate_ai_insights_for_topic(db: Session, user_id: int, topic_name: str) -> int:
    normalized_topic = _normalized_topic_name(topic_name)
    now = datetime.now(timezone.utc)
    result = db.execute(
        update(AITopicInsight)
        .where(
            AITopicInsight.user_id == user_id,
            AITopicInsight.topic_name == normalized_topic,
            (AITopicInsight.expires_at.is_(None) | (AITopicInsight.expires_at > now)),
        )
        .values(expires_at=now)
    )
    db.flush()
    return int(result.rowcount or 0)


def invalidate_ai_insights_for_graph_change(db: Session, user_id: int) -> int:
    now = datetime.now(timezone.utc)
    result = db.execute(
        update(AITopicInsight)
        .where(
            AITopicInsight.user_id == user_id,
            (AITopicInsight.expires_at.is_(None) | (AITopicInsight.expires_at > now)),
        )
        .values(expires_at=now)
    )
    db.flush()
    return int(result.rowcount or 0)


def latest_ai_insight_example(db: Session, user_id: int, feature_type: str | None = None) -> dict | None:
    stmt = select(AITopicInsight).where(AITopicInsight.user_id == user_id)
    if feature_type:
        stmt = stmt.where(AITopicInsight.feature_type == feature_type)
    insight = db.scalar(stmt.order_by(AITopicInsight.updated_at.desc()))
    if insight is None:
        return None
    return {
        "topic_name": insight.topic_name,
        "feature_type": insight.feature_type,
        "graph_version": insight.graph_version,
        "source": insight.source,
        "context_hash": insight.context_hash,
        "expires_at": insight.expires_at.isoformat() if insight.expires_at else None,
        "payload": json.loads(insight.payload_json),
    }


def count_active_ai_insights(db: Session, user_id: int) -> int:
    now = datetime.now(timezone.utc)
    return int(
        db.scalar(
            select(func.count(AITopicInsight.id)).where(
                AITopicInsight.user_id == user_id,
                (AITopicInsight.expires_at.is_(None) | (AITopicInsight.expires_at > now)),
            )
        )
        or 0
    )

