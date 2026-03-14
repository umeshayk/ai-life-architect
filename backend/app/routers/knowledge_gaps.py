from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.topic import KnowledgeGapPathResponse
from app.services.knowledge_gap_analyzer import analyze_knowledge_gaps


router = APIRouter(tags=["knowledge-gaps"])


@router.get("/api/knowledge/gaps", response_model=list[KnowledgeGapPathResponse])
def get_knowledge_gaps(
    refresh: bool = Query(False),
    domain: str = Query(""),
    topic: str = Query(""),
    level: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    gaps = analyze_knowledge_gaps(
        db,
        current_user.id,
        refresh=refresh,
        domain=domain,
        topic=topic,
        level=level,
    )
    return [KnowledgeGapPathResponse(**gap) for gap in gaps]
