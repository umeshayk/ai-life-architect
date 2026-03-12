from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.evolution import EvolutionResponse
from app.schemas.timeline import TimelineResponse
from app.services.timeline_service import get_timeline, get_timeline_evolution


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
