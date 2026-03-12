from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProfileBase(BaseModel):
    goals: str | None = None
    interests: str | None = None
    expertise: str | None = None
    preferred_topics: str | None = None


class ProfileUpdate(ProfileBase):
    pass


class ProfileResponse(ProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    updated_at: datetime
