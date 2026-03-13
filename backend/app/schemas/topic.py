from datetime import datetime

from pydantic import BaseModel

from app.schemas.knowledge import KnowledgeResponse


class TopicSummary(BaseModel):
    id: int
    name: str
    count: int
    discovery_method: str = "discovered"


class TopicItem(BaseModel):
    id: int
    name: str
    confidence_score: float
    created_at: datetime


class TopicRebuildResponse(BaseModel):
    processed_items: int
    topics_created: int
    links_created: int
    discovery_method: str = "discovered"


class TopicCleanupResponse(BaseModel):
    merged_topics: int
    discovery_method: str = "normalized"


class TopicItemsResponse(BaseModel):
    topic: TopicSummary
    items: list[KnowledgeResponse]


class TopicNoteSummary(BaseModel):
    id: int
    title: str
    type: str
    preview: str


class TopicDetailResponse(BaseModel):
    topic: str
    notes: list[TopicNoteSummary]
    related_topics: list[str]


class KnowledgeSuggestion(BaseModel):
    suggested_topic: str
    reason: str
    confidence: float
    domain: str
    topic_exists: bool = False
    state: str = "missing"
    action: str = "add"


class NextLearningTopic(BaseModel):
    topic: str
    reason: str
    confidence: float
    domain: str
    state: str = "missing"
    action: str = "add"
    priority: int
    topic_exists: bool = False
