from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.topic import LearningPathResponse
from app.services.learning_path_service import build_learning_paths


router = APIRouter(tags=["learning-paths"])


@router.get("/api/learning-paths", response_model=list[LearningPathResponse])
def get_learning_paths(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    paths = build_learning_paths(db, current_user.id)
    return [LearningPathResponse(**path) for path in paths]
