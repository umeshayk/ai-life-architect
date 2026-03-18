from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.mentor import MentorAskRequest, MentorAskResponse
from app.services.mentor_service import answer_mentor_question

router = APIRouter(tags=["mentor"])


@router.post("/api/mentor/ask", response_model=MentorAskResponse)
def ask_mentor(payload: MentorAskRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    response = answer_mentor_question(db, current_user.id, payload.question, refresh=payload.refresh)
    return MentorAskResponse(**response)
