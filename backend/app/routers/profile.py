from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.profile import UserProfile
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.profile import ProfileResponse, ProfileUpdate


router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse | None)
def get_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.scalar(select(UserProfile).where(UserProfile.user_id == current_user.id))


@router.put("", response_model=ProfileResponse)
def update_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == current_user.id))
    if profile is None:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    for field, value in payload.model_dump().items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile
