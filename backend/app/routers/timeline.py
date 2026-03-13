from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.action_plan import ActionPlanResponse
from app.schemas.evolution import EvolutionResponse
from app.schemas.timeline import KnowledgeGrowthResponse, TimelineResponse
from app.services.action_plan_service import get_weekly_action_plan
from app.services.timeline_service import get_knowledge_growth, get_timeline, get_timeline_evolution


router = APIRouter(tags=["timeline"])


@router.get("/api/timeline", response_model=TimelineResponse)
def read_timeline(
    range: str = Query(default="30d"),
    group_by: str = Query(default="week"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_timeline(db, current_user.id, range_key=range, group_by=group_by)


@router.get("/api/timeline/evolution", response_model=EvolutionResponse)
def read_timeline_evolution(
    range: str = Query(default="30d"),
    group_by: str = Query(default="week"),
    limit_topics: int = Query(default=5),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_timeline_evolution(
        db,
        current_user.id,
        range_key=range,
        group_by=group_by,
        limit_topics=limit_topics,
    )


@router.get("/api/timeline/action-plan", response_model=ActionPlanResponse)
def read_timeline_action_plan(
    range: str = Query(default="30d"),
    group_by: str = Query(default="week"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_weekly_action_plan(
        db,
        current_user.id,
        range_key=range,
        group_by=group_by,
    )


@router.get("/api/timeline/growth", response_model=KnowledgeGrowthResponse)
def read_timeline_growth(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_knowledge_growth(db, current_user.id)
