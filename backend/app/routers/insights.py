from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.insight import WeeklyInsightResponse
from app.services.insight_service import build_weekly_insights


router = APIRouter(tags=["insights"])


@router.get("/api/insights/weekly", response_model=WeeklyInsightResponse)
def get_weekly_insights(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return WeeklyInsightResponse(**build_weekly_insights(db, current_user.id))
