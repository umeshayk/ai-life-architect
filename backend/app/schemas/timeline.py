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


class KnowledgeEventItem(BaseModel):
    id: int
    event_type: str
    event_label: str
    topic: str | None = None
    related_topic: str | None = None
    source: str
    metadata: dict = {}
    created_at: datetime


class KnowledgeEventGroup(BaseModel):
    label: str
    date_key: str
    count: int
    events: list[KnowledgeEventItem]


class TimelineSummary(BaseModel):
    total_items: int
    most_active_period: str
    top_topics: list[str]
    latest_item_title: str | None


class KnowledgeGrowthPoint(BaseModel):
    month: str
    notes: int
    topics: int


class KnowledgeGrowthResponse(BaseModel):
    notes_count: int
    topics_count: int
    this_week_count: int
    previous_week_count: int
    weekly_growth_delta: int
    fastest_topic: str | None
    timeline: list[KnowledgeGrowthPoint]


class StrategyStep(BaseModel):
    topic: str
    completed: bool


class KnowledgeStrategy(BaseModel):
    domain: str
    path: list[StrategyStep]


class KnowledgeProject(BaseModel):
    name: str
    topics: list[str]
    progress: float
    next_step: str | None


class KnowledgeForecast(BaseModel):
    domain: str
    confidence: float
    estimated_mastery_months: int


class TimelineInsights(BaseModel):
    summary: str
    emerging_topics: list[str]
    dominant_topic: str | None
    fastest_topic: str | None
    emerging_topic: str | None
    stable_topic: str | None
    suggested_topics: list[str]
    knowledge_gaps: list[str]
    strategies: list[KnowledgeStrategy]
    projects: list[KnowledgeProject]
    forecast: list[KnowledgeForecast]
    suggestions: list[str]


class TimelineResponse(BaseModel):
    groups: list[TimelineGroup]
    event_groups: list[KnowledgeEventGroup] = []
    top_topics: list[TimelineTopicCount]
    summary: TimelineSummary
    insights: TimelineInsights
