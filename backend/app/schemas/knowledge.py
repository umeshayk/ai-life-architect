from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class KnowledgeBase(BaseModel):
    type: str = Field(pattern="^(note|link|file)$")
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    source_url: HttpUrl | None = None
    tags: list[str] | None = None
    file_name: str | None = None


class KnowledgeCreate(KnowledgeBase):
    pass


class KnowledgeUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = Field(default=None, min_length=1)
    source_url: HttpUrl | None = None
    tags: list[str] | None = None


class KnowledgeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    type: str
    title: str
    content: str
    summary: str | None = None
    tags: list[str] = Field(default_factory=list)
    source_url: str | None = None
    file_name: str | None = None
    created_at: datetime
    updated_at: datetime


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)


class WeeklyInsightsResponse(BaseModel):
    total_items: int
    items_added_this_week: int
    top_tags: list[str]
    recent_titles: list[str]
