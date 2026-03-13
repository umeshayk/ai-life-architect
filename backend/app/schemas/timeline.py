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


class KnowledgeGrowthPoint(BaseModel):
    month: str
    notes: int
    topics: int


class KnowledgeGrowthResponse(BaseModel):
    notes_count: int
    topics_count: int
    weekly_growth: int
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
    top_topics: list[TimelineTopicCount]
    summary: TimelineSummary
    insights: TimelineInsights
