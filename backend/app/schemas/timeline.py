from datetime import datetime

from pydantic import BaseModel


class TimelineTopicCount(BaseModel):
    name: str
    count: int


class TimelineItem(BaseModel):
    id: int
    title: str
    type: str
    summary: str | None
    tags: list[str]
    topics: list[str]
    created_at: datetime


class TimelineGroup(BaseModel):
    label: str
    date_key: str
    count: int
    items: list[TimelineItem]


class TimelineSummary(BaseModel):
    total_items: int
    most_active_period: str
    top_topics: list[str]
    latest_item_title: str | None


class TimelineResponse(BaseModel):
    groups: list[TimelineGroup]
    top_topics: list[TimelineTopicCount]
    summary: TimelineSummary
