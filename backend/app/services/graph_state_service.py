from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user_graph_state import UserGraphState
from app.services.ai_insight_store import invalidate_ai_insights_for_graph_change, invalidate_ai_insights_for_topic


def get_or_create_user_graph_state(db: Session, user_id: int) -> UserGraphState:
    state = db.scalar(select(UserGraphState).where(UserGraphState.user_id == user_id))
    if state is None:
        state = UserGraphState(user_id=user_id, graph_version=1)
        db.add(state)
        db.flush()
    return state


def get_user_graph_version(db: Session, user_id: int) -> int:
    return get_or_create_user_graph_state(db, user_id).graph_version


def bump_user_graph_version(db: Session, user_id: int, *, topic_name: str | None = None, reason: str = "") -> int:
    state = get_or_create_user_graph_state(db, user_id)
    state.graph_version += 1
    if topic_name:
        invalidate_ai_insights_for_topic(db, user_id, topic_name)
    invalidate_ai_insights_for_graph_change(db, user_id)
    db.flush()
    return state.graph_version
